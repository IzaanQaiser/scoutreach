"""Outreach review/regenerate/send orchestration for Phase 6."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
import random
import time

from app.db.run_repository import RunRepository
from app.integrations.gemini_client import GeminiDossierClient
from app.integrations.gmail_client import GmailClient
from app.integrations.provider_errors import ProviderError
from app.middleware.auth import AuthenticatedUser
from app.middleware.errors import ApiError
from app.models.statuses import (
    OUTREACH_REVIEWABLE_STATUSES,
    OUTREACH_STATUS_APPROVED,
    OUTREACH_STATUS_DRAFT,
    OUTREACH_STATUS_FAILED,
    OUTREACH_STATUS_GENERATION_FAILED,
    OUTREACH_STATUS_NEEDS_REVIEW,
    OUTREACH_STATUS_REJECTED,
    OUTREACH_STATUS_SENDING,
    OUTREACH_STATUS_SENT,
    RUN_STATUS_COMPLETED,
    RUN_STATUS_COMPLETED_WITH_ERRORS,
    RUN_STATUS_MESSAGES_GENERATED,
    RUN_STATUS_SENDING,
)


logger = logging.getLogger(__name__)

DEFAULT_SENDS_PER_DAY_LIMIT = 350
DEFAULT_SEND_RETRY_ATTEMPTS = 3
DEFAULT_SEND_RETRY_BASE_DELAY_SECONDS = 0.2
DEFAULT_SEND_RETRY_MAX_JITTER_SECONDS = 0.2
DEFAULT_PROVIDER_THROTTLE_SECONDS = 0.05

RETRYABLE_GMAIL_CODES = {
    "GMAIL_RATE_LIMITED",
    "GMAIL_TRANSIENT",
}

REVIEW_SUMMARY_STATUSES = (
    OUTREACH_STATUS_DRAFT,
    OUTREACH_STATUS_APPROVED,
    OUTREACH_STATUS_NEEDS_REVIEW,
    OUTREACH_STATUS_REJECTED,
    OUTREACH_STATUS_SENT,
    OUTREACH_STATUS_FAILED,
    OUTREACH_STATUS_GENERATION_FAILED,
)


class OutreachService:
    def __init__(
        self,
        *,
        repository: RunRepository,
        gemini_client: GeminiDossierClient,
        gmail_client: GmailClient,
        sends_per_day_limit: int = DEFAULT_SENDS_PER_DAY_LIMIT,
        send_retry_attempts: int = DEFAULT_SEND_RETRY_ATTEMPTS,
        send_retry_base_delay_seconds: float = DEFAULT_SEND_RETRY_BASE_DELAY_SECONDS,
        send_retry_max_jitter_seconds: float = DEFAULT_SEND_RETRY_MAX_JITTER_SECONDS,
        provider_throttle_seconds: float = DEFAULT_PROVIDER_THROTTLE_SECONDS,
    ) -> None:
        self._repository = repository
        self._gemini_client = gemini_client
        self._gmail_client = gmail_client
        self._sends_per_day_limit = sends_per_day_limit
        self._send_retry_attempts = max(send_retry_attempts, 1)
        self._send_retry_base_delay_seconds = max(send_retry_base_delay_seconds, 0)
        self._send_retry_max_jitter_seconds = max(send_retry_max_jitter_seconds, 0)
        self._provider_throttle_seconds = max(provider_throttle_seconds, 0)

    def list_run_outreach(
        self,
        *,
        user: AuthenticatedUser,
        run_id: str,
        status: str | None,
        limit: int,
        offset: int,
    ) -> dict:
        self._require_run_owner(run_id=run_id, user_id=user.user_id)

        outreach_rows = self._repository.list_outreach_for_run(
            run_id=run_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        company_name_by_id = self._company_name_by_id(run_id=run_id)

        response_rows: list[dict] = []
        for row in outreach_rows:
            normalized = dict(row)
            normalized["company_name"] = company_name_by_id.get(str(row.get("company_id")))
            response_rows.append(normalized)

        return {
            "outreach": response_rows,
        }

    def get_outreach(self, *, user: AuthenticatedUser, outreach_id: str) -> dict:
        row = self._require_outreach_owner(user=user, outreach_id=outreach_id)
        return row

    def update_outreach(
        self,
        *,
        user: AuthenticatedUser,
        outreach_id: str,
        subject: str | None,
        message_content: str | None,
        status: str | None,
        review_notes: str | None,
    ) -> dict:
        row = self._require_outreach_owner(user=user, outreach_id=outreach_id)

        current_status = str(row.get("status") or "")
        if current_status not in OUTREACH_REVIEWABLE_STATUSES:
            raise ApiError(
                status_code=409,
                code="INVALID_STATUS_TRANSITION",
                message="Outreach cannot be edited from current status.",
                details={
                    "current_status": current_status,
                },
            )

        fields: dict[str, object] = {}

        if subject is not None:
            normalized_subject = subject.strip()
            if not normalized_subject:
                raise ApiError(
                    status_code=422,
                    code="VALIDATION_ERROR",
                    message="subject must not be empty when provided.",
                )
            fields["subject"] = normalized_subject

        if message_content is not None:
            normalized_body = message_content.strip()
            if not normalized_body:
                raise ApiError(
                    status_code=422,
                    code="VALIDATION_ERROR",
                    message="message_content must not be empty when provided.",
                )
            fields["message_content"] = normalized_body

        if status is not None:
            fields["status"] = status

        if review_notes is not None:
            normalized_notes = review_notes.strip()
            fields["review_notes"] = normalized_notes or None

        if not fields:
            return {
                "outreach_id": outreach_id,
                "status": current_status,
                "message": "Outreach updated successfully",
            }

        fields["updated_at"] = _utc_now_iso()
        self._repository.update_outreach(outreach_id=outreach_id, fields=fields)

        updated = self._repository.get_outreach(outreach_id=outreach_id)
        updated_status = str(updated.get("status") if updated is not None else fields.get("status") or current_status)

        return {
            "outreach_id": outreach_id,
            "status": updated_status,
            "message": "Outreach updated successfully",
        }

    def regenerate_outreach(
        self,
        *,
        user: AuthenticatedUser,
        outreach_id: str,
        critique: str,
        message_preferences_override: dict | None,
    ) -> dict:
        outreach = self._require_outreach_owner(user=user, outreach_id=outreach_id)

        current_status = str(outreach.get("status") or "")
        if current_status in {OUTREACH_STATUS_SENDING, OUTREACH_STATUS_SENT}:
            raise ApiError(
                status_code=409,
                code="INVALID_STATUS_TRANSITION",
                message="Outreach cannot be regenerated after send has started.",
                details={
                    "current_status": current_status,
                },
            )

        run = self._repository.get_run_for_user(
            run_id=str(outreach.get("run_id")),
            user_id=user.user_id,
        )
        if run is None:
            raise ApiError(
                status_code=404,
                code="NOT_FOUND",
                message="Run not found.",
            )

        company = self._repository.get_company(company_id=str(outreach.get("company_id")))
        if company is None:
            raise ApiError(
                status_code=404,
                code="NOT_FOUND",
                message="Company not found.",
            )

        founder = {
            "name": outreach.get("founder_name"),
            "email": outreach.get("founder_email"),
        }

        try:
            regenerated = self._gemini_client.regenerate_outreach_draft(
                company=company,
                founder=founder,
                profile_snapshot=run.get("profile_snapshot") or {},
                critique=critique,
                message_preferences_override=message_preferences_override,
            )
        except ProviderError as exc:
            logger.warning(
                "outreach_regeneration_failed",
                extra={"outreach_id": outreach_id, "run_id": run["id"], "user_id": user.user_id},
            )
            self._repository.update_outreach(
                outreach_id=outreach_id,
                fields={
                    "error_message": exc.message,
                    "updated_at": _utc_now_iso(),
                },
            )
            raise ApiError(
                status_code=502,
                code=exc.code,
                message=exc.message,
            ) from exc

        self._repository.update_outreach(
            outreach_id=outreach_id,
            fields={
                "subject": regenerated["subject"],
                "message_content": regenerated["message_content"],
                "status": OUTREACH_STATUS_DRAFT,
                "review_notes": f"Regenerated with critique: {critique.strip()}",
                "error_message": None,
                "updated_at": _utc_now_iso(),
            },
        )
        logger.info("outreach_regenerated", extra={"outreach_id": outreach_id, "run_id": run["id"], "user_id": user.user_id})

        return {
            "outreach_id": outreach_id,
            "subject": regenerated["subject"],
            "message_content": regenerated["message_content"],
            "status": OUTREACH_STATUS_DRAFT,
            "message": "Message regenerated successfully",
        }

    def get_review_summary(self, *, user: AuthenticatedUser, run_id: str) -> dict:
        self._require_run_owner(run_id=run_id, user_id=user.user_id)

        counts = {
            status: self._repository.count_outreach_for_run_by_status(run_id=run_id, status=status)
            for status in REVIEW_SUMMARY_STATUSES
        }

        return {
            "run_id": run_id,
            "counts": counts,
        }

    def send_approved(self, *, user: AuthenticatedUser, run_id: str) -> dict:
        run = self._require_run_owner(run_id=run_id, user_id=user.user_id)

        approved_rows = self._repository.list_outreach_for_run(
            run_id=run_id,
            status=OUTREACH_STATUS_APPROVED,
            limit=1000,
            offset=0,
        )
        approved_count = len(approved_rows)

        used_today = self._repository.count_outreach_sent_today(user_id=user.user_id)
        remaining_quota = self._sends_per_day_limit - used_today
        if remaining_quota <= 0 or approved_count > remaining_quota:
            logger.warning(
                "send_quota_rejected",
                extra={"run_id": run_id, "user_id": user.user_id, "approved_count": approved_count},
            )
            raise ApiError(
                status_code=429,
                code="QUOTA_EXCEEDED",
                message="Daily sending quota exceeded.",
                details={
                    "daily_limit": self._sends_per_day_limit,
                    "used_today": used_today,
                    "approved_count": approved_count,
                },
            )

        if approved_count == 0:
            return {
                "run_id": run_id,
                "sent_count": 0,
                "failed_count": 0,
                "results": [],
            }

        self._repository.update_run(
            run_id=run_id,
            fields={
                "status": RUN_STATUS_SENDING,
                "error_message": None,
            },
        )

        sent_count = 0
        failed_count = 0
        results: list[dict] = []

        for row in approved_rows:
            row_id = str(row.get("id"))

            latest = self._repository.get_outreach_for_user(
                outreach_id=row_id,
                user_id=user.user_id,
            )
            if latest is None:
                continue
            if str(latest.get("status") or "") != OUTREACH_STATUS_APPROVED:
                continue

            self._repository.update_outreach(
                outreach_id=row_id,
                fields={
                    "status": OUTREACH_STATUS_SENDING,
                    "error_message": None,
                    "updated_at": _utc_now_iso(),
                },
            )

            try:
                self._send_with_retry(outreach=latest)
                sent_at = _utc_now_iso()
                self._repository.update_outreach(
                    outreach_id=row_id,
                    fields={
                        "status": OUTREACH_STATUS_SENT,
                        "sent_at": sent_at,
                        "error_message": None,
                        "updated_at": sent_at,
                    },
                )
                sent_count += 1
                results.append(
                    {
                        "outreach_id": row_id,
                        "status": OUTREACH_STATUS_SENT,
                        "error_message": None,
                    }
                )
                logger.info("outreach_sent", extra={"outreach_id": row_id, "run_id": run_id, "user_id": user.user_id})
            except ProviderError as exc:
                failed_count += 1
                self._repository.update_outreach(
                    outreach_id=row_id,
                    fields={
                        "status": OUTREACH_STATUS_FAILED,
                        "error_message": exc.message,
                        "updated_at": _utc_now_iso(),
                    },
                )
                results.append(
                    {
                        "outreach_id": row_id,
                        "status": OUTREACH_STATUS_FAILED,
                        "error_message": exc.message,
                    }
                )
                logger.warning(
                    "outreach_send_failed",
                    extra={"outreach_id": row_id, "run_id": run_id, "user_id": user.user_id},
                )

            if self._provider_throttle_seconds > 0:
                time.sleep(self._provider_throttle_seconds)

        has_errors = failed_count > 0
        final_status = RUN_STATUS_COMPLETED_WITH_ERRORS if has_errors else RUN_STATUS_COMPLETED
        final_error = None
        if has_errors:
            final_error = f"Send completed with failures: failed_count={failed_count}"

        self._repository.update_run(
            run_id=run_id,
            fields={
                "status": final_status,
                "error_message": final_error,
                "completed_at": _utc_now_iso(),
            },
        )

        return {
            "run_id": run_id,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "results": results,
        }

    def send_single(self, *, user: AuthenticatedUser, outreach_id: str, confirm_send: bool) -> dict:
        if not confirm_send:
            raise ApiError(
                status_code=400,
                code="VALIDATION_ERROR",
                message="confirm_send must be true to send outreach.",
            )

        outreach = self._require_outreach_owner(user=user, outreach_id=outreach_id)
        if str(outreach.get("status") or "") != OUTREACH_STATUS_APPROVED:
            raise ApiError(
                status_code=409,
                code="INVALID_STATUS_TRANSITION",
                message="Only approved outreach can be sent.",
                details={"status": outreach.get("status")},
            )

        used_today = self._repository.count_outreach_sent_today(user_id=user.user_id)
        if used_today >= self._sends_per_day_limit:
            raise ApiError(
                status_code=429,
                code="QUOTA_EXCEEDED",
                message="Daily sending quota exceeded.",
                details={
                    "daily_limit": self._sends_per_day_limit,
                    "used_today": used_today,
                },
            )

        self._repository.update_outreach(
            outreach_id=outreach_id,
            fields={
                "status": OUTREACH_STATUS_SENDING,
                "error_message": None,
                "updated_at": _utc_now_iso(),
            },
        )

        try:
            self._send_with_retry(outreach=outreach)
        except ProviderError as exc:
            self._repository.update_outreach(
                outreach_id=outreach_id,
                fields={
                    "status": OUTREACH_STATUS_FAILED,
                    "error_message": exc.message,
                    "updated_at": _utc_now_iso(),
                },
            )
            raise ApiError(
                status_code=502,
                code=exc.code,
                message=exc.message,
            ) from exc

        sent_at = _utc_now_iso()
        self._repository.update_outreach(
            outreach_id=outreach_id,
            fields={
                "status": OUTREACH_STATUS_SENT,
                "sent_at": sent_at,
                "error_message": None,
                "updated_at": sent_at,
            },
        )
        logger.info("outreach_sent_single", extra={"outreach_id": outreach_id, "user_id": user.user_id})

        return {
            "outreach_id": outreach_id,
            "status": OUTREACH_STATUS_SENT,
            "sent_at": sent_at,
        }

    def _send_with_retry(self, *, outreach: dict) -> None:
        outreach_id = str(outreach.get("id"))

        attempt = 1
        while True:
            try:
                self._gmail_client.send_message(
                    outreach_id=outreach_id,
                    to_email=outreach.get("founder_email"),
                    subject=outreach.get("subject"),
                    message_content=outreach.get("message_content"),
                )
                return
            except ProviderError as exc:
                if attempt >= self._send_retry_attempts or exc.code not in RETRYABLE_GMAIL_CODES:
                    raise

                backoff_delay = self._send_retry_base_delay_seconds * (2 ** (attempt - 1))
                jitter = random.uniform(0, self._send_retry_max_jitter_seconds)
                time.sleep(backoff_delay + jitter)
                attempt += 1

    def _company_name_by_id(self, *, run_id: str) -> dict[str, str]:
        companies = self._repository.get_companies_for_run(run_id=run_id)
        return {
            str(company["id"]): str(company["name"])
            for company in companies
            if company.get("id") is not None and company.get("name") is not None
        }

    def _require_run_owner(self, *, run_id: str, user_id: str) -> dict:
        run = self._repository.get_run_for_user(run_id=run_id, user_id=user_id)
        if run is None:
            raise ApiError(
                status_code=404,
                code="NOT_FOUND",
                message="Run not found.",
            )

        run_status = str(run.get("status") or "")
        if run_status not in {
            RUN_STATUS_MESSAGES_GENERATED,
            RUN_STATUS_COMPLETED,
            RUN_STATUS_COMPLETED_WITH_ERRORS,
            RUN_STATUS_SENDING,
        }:
            raise ApiError(
                status_code=409,
                code="INVALID_STATUS_TRANSITION",
                message="Run is not ready for outreach review or sending.",
                details={"run_status": run_status},
            )

        return run

    def _require_outreach_owner(self, *, user: AuthenticatedUser, outreach_id: str) -> dict:
        row = self._repository.get_outreach_for_user(
            outreach_id=outreach_id,
            user_id=user.user_id,
        )
        if row is None:
            raise ApiError(
                status_code=404,
                code="NOT_FOUND",
                message="Outreach not found.",
            )
        return row


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()
