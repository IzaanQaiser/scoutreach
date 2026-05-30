"""Outreach generation service for Phase 5."""

from __future__ import annotations

from datetime import UTC, datetime
import time

from app.db.run_repository import RunRepository
from app.integrations.gemini_client import GeminiDossierClient
from app.integrations.provider_errors import ProviderError
from app.middleware.auth import AuthenticatedUser
from app.middleware.errors import ApiError
from app.models.statuses import (
    COMPANY_STATUS_ACCEPTED,
    OUTREACH_STATUS_DRAFT,
    OUTREACH_STATUS_GENERATION_FAILED,
    RUN_STATUS_COMPLETED,
    RUN_STATUS_COMPLETED_WITH_ERRORS,
    RUN_STATUS_MESSAGES_GENERATED,
    RUN_STATUS_MESSAGES_GENERATING,
)
from app.utils.provider_resilience import call_with_backoff


DEFAULT_MESSAGES_PER_DAY_LIMIT = 350
DEFAULT_GEMINI_MAX_ATTEMPTS = 3
DEFAULT_GEMINI_BASE_DELAY_SECONDS = 0.2
DEFAULT_GEMINI_MAX_JITTER_SECONDS = 0.2
DEFAULT_GEMINI_THROTTLE_SECONDS = 0.05

GEMINI_RETRYABLE_CODES = {
    "GEMINI_RATE_LIMITED",
    "GEMINI_TRANSIENT",
}


class OutreachGenerationService:
    def __init__(
        self,
        *,
        repository: RunRepository,
        gemini_client: GeminiDossierClient,
        messages_per_day_limit: int = DEFAULT_MESSAGES_PER_DAY_LIMIT,
        gemini_max_attempts: int = DEFAULT_GEMINI_MAX_ATTEMPTS,
        gemini_base_delay_seconds: float = DEFAULT_GEMINI_BASE_DELAY_SECONDS,
        gemini_max_jitter_seconds: float = DEFAULT_GEMINI_MAX_JITTER_SECONDS,
        gemini_throttle_seconds: float = DEFAULT_GEMINI_THROTTLE_SECONDS,
    ) -> None:
        self._repository = repository
        self._gemini_client = gemini_client
        self._messages_per_day_limit = messages_per_day_limit
        self._gemini_max_attempts = max(gemini_max_attempts, 1)
        self._gemini_base_delay_seconds = max(gemini_base_delay_seconds, 0)
        self._gemini_max_jitter_seconds = max(gemini_max_jitter_seconds, 0)
        self._gemini_throttle_seconds = max(gemini_throttle_seconds, 0)

    def generate_messages(
        self,
        *,
        user: AuthenticatedUser,
        run_id: str,
        founder_selection_strategy: str,
        max_messages: int,
    ) -> dict:
        run = self._repository.get_run_for_user(run_id=run_id, user_id=user.user_id)
        if run is None:
            raise ApiError(status_code=404, code="NOT_FOUND", message="Run not found.")

        run_status = str(run.get("status") or "")
        if run_status not in {RUN_STATUS_COMPLETED, RUN_STATUS_COMPLETED_WITH_ERRORS, RUN_STATUS_MESSAGES_GENERATED}:
            raise ApiError(
                status_code=409,
                code="INVALID_STATUS_TRANSITION",
                message="Run is not ready for message generation.",
                details={"run_status": run_status},
            )

        used_today = self._repository.count_outreach_created_today(user_id=user.user_id)
        remaining_quota = self._messages_per_day_limit - used_today
        if remaining_quota <= 0:
            raise ApiError(
                status_code=429,
                code="QUOTA_EXCEEDED",
                message="Daily message generation quota exceeded.",
                details={"daily_limit": self._messages_per_day_limit},
            )

        effective_limit = min(max_messages, remaining_quota)

        accepted_companies = self._repository.list_companies_for_run(
            run_id=run_id,
            status=COMPANY_STATUS_ACCEPTED,
            limit=1000,
            offset=0,
        )

        self._repository.update_run(
            run_id=run_id,
            fields={
                "status": RUN_STATUS_MESSAGES_GENERATING,
                "error_message": None,
            },
        )

        generated_count = 0
        generation_failed_count = 0
        processed_messages = 0

        for company in accepted_companies:
            if processed_messages >= effective_limit:
                break

            selected_founders = self._select_founders(
                founders=company.get("founders") or [],
                strategy=founder_selection_strategy,
            )

            for founder in selected_founders:
                if processed_messages >= effective_limit:
                    break

                try:
                    draft = call_with_backoff(
                        operation=lambda: self._gemini_client.generate_outreach_draft(
                            company=company,
                            founder=founder,
                            profile_snapshot=run.get("profile_snapshot") or {},
                        ),
                        retryable_codes=GEMINI_RETRYABLE_CODES,
                        max_attempts=self._gemini_max_attempts,
                        base_delay_seconds=self._gemini_base_delay_seconds,
                        max_jitter_seconds=self._gemini_max_jitter_seconds,
                    )
                    self._repository.insert_outreach(
                        payload={
                            "user_id": user.user_id,
                            "run_id": run_id,
                            "company_id": company["id"],
                            "founder_name": founder.get("name"),
                            "founder_email": founder.get("email"),
                            "subject": draft["subject"],
                            "message_content": draft["message_content"],
                            "status": OUTREACH_STATUS_DRAFT,
                            "review_notes": None,
                            "error_message": None,
                            "sent_at": None,
                        }
                    )
                    generated_count += 1
                    if self._gemini_throttle_seconds > 0:
                        time.sleep(self._gemini_throttle_seconds)
                except ProviderError as exc:
                    self._repository.insert_outreach(
                        payload={
                            "user_id": user.user_id,
                            "run_id": run_id,
                            "company_id": company["id"],
                            "founder_name": founder.get("name"),
                            "founder_email": founder.get("email"),
                            "subject": None,
                            "message_content": None,
                            "status": OUTREACH_STATUS_GENERATION_FAILED,
                            "review_notes": None,
                            "error_message": exc.message,
                            "sent_at": None,
                        }
                    )
                    generation_failed_count += 1

                processed_messages += 1

        run_error_message = None
        if generation_failed_count > 0:
            run_error_message = (
                "Message generation completed with failures: "
                f"generation_failed_count={generation_failed_count}"
            )

        self._repository.update_run(
            run_id=run_id,
            fields={
                "status": RUN_STATUS_MESSAGES_GENERATED,
                "completed_at": datetime.now(UTC).isoformat(),
                "error_message": run_error_message,
            },
        )

        return {
            "run_id": run_id,
            "status": RUN_STATUS_MESSAGES_GENERATED,
            "generated_count": generated_count,
            "generation_failed_count": generation_failed_count,
            "message": "Messages generated successfully",
        }

    def _select_founders(self, *, founders: list[dict], strategy: str) -> list[dict]:
        if not founders:
            return [{}]

        with_email = [founder for founder in founders if founder.get("email")]

        if strategy == "all_verified_founders":
            if with_email:
                return with_email
            return [founders[0]]

        # MVP: manual-selected mode currently falls back to first available founder.
        if strategy in {"first_verified_email", "manual_selected_founders"}:
            if with_email:
                return [with_email[0]]
            return [founders[0]]

        return [founders[0]]
