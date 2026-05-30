"""Account and onboarding service."""

from __future__ import annotations

from datetime import UTC, datetime

from app.db.run_repository import RunRepository
from app.integrations.gemini_client import GeminiDossierClient
from app.integrations.provider_errors import ProviderError
from app.middleware.auth import AuthenticatedUser
from app.middleware.errors import ApiError
from app.schemas.account import OnboardingStep, OnboardingStatus
from app.utils.provider_resilience import call_with_backoff


DEFAULT_CALIBRATION_EVENTS_PER_DAY_LIMIT = 30
DEFAULT_GEMINI_MAX_ATTEMPTS = 3
DEFAULT_GEMINI_BASE_DELAY_SECONDS = 0.2
DEFAULT_GEMINI_MAX_JITTER_SECONDS = 0.2
CALIBRATION_EXAMPLE_COUNT = 5
CALIBRATION_MAX_LOOPS = 3

GEMINI_RETRYABLE_CODES = {
    "GEMINI_RATE_LIMITED",
    "GEMINI_TRANSIENT",
}

STEP_ORDER: list[OnboardingStep] = [
    "auth",
    "name",
    "profile_sources",
    "targets",
    "message_preferences",
    "calibration",
    "done",
]

FINAL_ONBOARDING_STATUSES: set[OnboardingStatus] = {
    "completed",
    "completed_after_cap",
    "skipped_calibration",
}


class AccountService:
    def __init__(
        self,
        *,
        repository: RunRepository,
        gemini_client: GeminiDossierClient,
        calibration_events_per_day_limit: int = DEFAULT_CALIBRATION_EVENTS_PER_DAY_LIMIT,
        gemini_max_attempts: int = DEFAULT_GEMINI_MAX_ATTEMPTS,
        gemini_base_delay_seconds: float = DEFAULT_GEMINI_BASE_DELAY_SECONDS,
        gemini_max_jitter_seconds: float = DEFAULT_GEMINI_MAX_JITTER_SECONDS,
    ) -> None:
        self._repository = repository
        self._gemini_client = gemini_client
        self._calibration_events_per_day_limit = calibration_events_per_day_limit
        self._gemini_max_attempts = max(gemini_max_attempts, 1)
        self._gemini_base_delay_seconds = max(gemini_base_delay_seconds, 0)
        self._gemini_max_jitter_seconds = max(gemini_max_jitter_seconds, 0)

    def get_me(self, *, user: AuthenticatedUser) -> dict:
        user_row = self._require_user_row(user=user)

        return {
            "user": self._serialize_user(user_row),
            "has_candidate_profile": self._repository.has_candidate_profile(user_id=user.user_id),
            "onboarding_complete": str(user_row.get("onboarding_status") or "") in FINAL_ONBOARDING_STATUSES,
        }

    def update_me(self, *, user: AuthenticatedUser, first_name: str | None, last_name: str | None) -> dict:
        user_row = self._require_user_row(user=user)

        fields: dict[str, object] = {}
        if first_name is not None:
            fields["first_name"] = first_name.strip()
        if last_name is not None:
            fields["last_name"] = last_name.strip()

        if not fields:
            return {"message": "Profile updated successfully"}

        fields["onboarding_status"] = "in_progress"
        fields["onboarding_step"] = self._max_step(user_row.get("onboarding_step"), "profile_sources")
        self._repository.update_user(user_id=user.user_id, fields=fields)

        return {
            "message": "Profile updated successfully",
            "onboarding_step": fields["onboarding_step"],
        }

    def get_candidate_profile(self, *, user: AuthenticatedUser) -> dict:
        self._require_user_row(user=user)
        profile = self._repository.get_candidate_profile(user_id=user.user_id)
        if profile is None:
            return {
                "user_id": user.user_id,
                "resume": None,
                "skills": {},
                "github_url": None,
                "github_content": {},
                "linkedin_url": None,
                "linkedin_content": {},
                "portfolio_url": None,
                "portfolio_content": {},
                "bio": None,
                "extra_context": None,
                "target_roles": [],
                "job_preferences": {},
            }
        return profile

    def upsert_candidate_profile(
        self,
        *,
        user: AuthenticatedUser,
        fields: dict,
    ) -> dict:
        user_row = self._require_user_row(user=user)
        profile = self._repository.upsert_candidate_profile(user_id=user.user_id, fields=fields)

        target_roles = profile.get("target_roles") if isinstance(profile, dict) else []
        job_preferences = profile.get("job_preferences") if isinstance(profile, dict) else {}
        has_targets = isinstance(target_roles, list) and len(target_roles) > 0
        has_industry = isinstance(job_preferences, dict) and bool(job_preferences.get("industries"))

        next_step: OnboardingStep = "targets"
        if has_targets and has_industry:
            next_step = "message_preferences"

        self._repository.update_user(
            user_id=user.user_id,
            fields={
                "onboarding_status": "in_progress",
                "onboarding_step": self._max_step(user_row.get("onboarding_step"), next_step),
            },
        )

        return {"message": "Candidate profile saved successfully"}

    def get_settings(self, *, user: AuthenticatedUser) -> dict:
        user_row = self._require_user_row(user=user)
        return {
            "auto_send_enabled": bool(user_row.get("auto_send_enabled", False)),
            "message_preferences": user_row.get("message_preferences") or {},
        }

    def update_settings(self, *, user: AuthenticatedUser, auto_send_enabled: bool | None, message_preferences: dict | None) -> dict:
        user_row = self._require_user_row(user=user)

        fields: dict[str, object] = {}
        if auto_send_enabled is not None:
            fields["auto_send_enabled"] = bool(auto_send_enabled)
        if message_preferences is not None:
            fields["message_preferences"] = message_preferences

        if fields:
            fields["onboarding_status"] = "in_progress"
            fields["onboarding_step"] = self._max_step(user_row.get("onboarding_step"), "calibration")
            self._repository.update_user(user_id=user.user_id, fields=fields)

        return {"message": "Settings updated successfully"}

    def get_onboarding_state(self, *, user: AuthenticatedUser) -> dict:
        user_row = self._require_user_row(user=user)

        onboarding_status = str(user_row.get("onboarding_status") or "not_started")
        onboarding_step = str(user_row.get("onboarding_step") or "auth")
        calibration_loop_count = int(user_row.get("calibration_loop_count") or 0)
        calibration_last_result = user_row.get("calibration_last_result")

        return {
            "status": onboarding_status,
            "step": onboarding_step,
            "onboarding_complete": onboarding_status in FINAL_ONBOARDING_STATUSES,
            "calibration_loop_count": calibration_loop_count,
            "calibration_last_result": calibration_last_result,
        }

    def generate_onboarding_examples(self, *, user: AuthenticatedUser, loop_index: int) -> dict:
        user_row = self._require_user_row(user=user)
        self._enforce_calibration_quota(user_id=user.user_id)

        examples = self._build_example_messages(
            user_id=user.user_id,
            feedback_hint="",
            loop_index=loop_index,
        )

        self._repository.insert_onboarding_calibration_event(
            payload={
                "user_id": user.user_id,
                "event_type": "examples_generated",
                "loop_index": loop_index,
                "feedback": {},
            }
        )

        self._repository.update_user(
            user_id=user.user_id,
            fields={
                "onboarding_status": "in_progress",
                "onboarding_step": self._max_step(user_row.get("onboarding_step"), "calibration"),
            },
        )

        return {
            "loop_index": loop_index,
            "examples": examples,
            "max_loops": CALIBRATION_MAX_LOOPS,
        }

    def submit_onboarding_feedback(self, *, user: AuthenticatedUser, loop_index: int, rejected_examples: list[dict]) -> dict:
        user_row = self._require_user_row(user=user)

        normalized_loop = max(loop_index, int(user_row.get("calibration_loop_count") or 0))
        normalized_rejected = [dict(item) for item in rejected_examples if isinstance(item, dict)]

        self._repository.insert_onboarding_calibration_event(
            payload={
                "user_id": user.user_id,
                "event_type": "feedback_submitted",
                "loop_index": normalized_loop,
                "feedback": {"rejected_examples": normalized_rejected},
            }
        )

        if not normalized_rejected:
            return self.complete_onboarding(user=user, completion_mode="completed")

        next_loop = normalized_loop + 1
        if next_loop >= CALIBRATION_MAX_LOOPS:
            return self.complete_onboarding(user=user, completion_mode="completed_after_cap")

        self._enforce_calibration_quota(user_id=user.user_id)

        feedback_hint = " ".join(
            [
                str(item.get("position_industry_feedback") or "").strip()
                + " "
                + str(item.get("subject_feedback") or "").strip()
                + " "
                + str(item.get("body_feedback") or "").strip()
                for item in normalized_rejected
            ]
        ).strip()

        examples = self._build_example_messages(
            user_id=user.user_id,
            feedback_hint=feedback_hint,
            loop_index=next_loop,
        )

        self._repository.insert_onboarding_calibration_event(
            payload={
                "user_id": user.user_id,
                "event_type": "examples_generated",
                "loop_index": next_loop,
                "feedback": {"source": "feedback"},
            }
        )

        self._repository.update_user(
            user_id=user.user_id,
            fields={
                "calibration_loop_count": next_loop,
                "calibration_last_result": "partial_reject",
                "onboarding_status": "in_progress",
                "onboarding_step": "calibration",
            },
        )

        return {
            "loop_index": next_loop,
            "examples": examples,
            "max_loops": CALIBRATION_MAX_LOOPS,
            "message": "Generated a refreshed example set based on your feedback.",
        }

    def complete_onboarding(self, *, user: AuthenticatedUser, completion_mode: str) -> dict:
        self._require_user_row(user=user)

        if completion_mode not in {"completed", "completed_after_cap", "skipped_calibration"}:
            raise ApiError(
                status_code=422,
                code="VALIDATION_ERROR",
                message="Invalid onboarding completion mode.",
            )

        event_type = "completed"
        if completion_mode == "skipped_calibration":
            event_type = "skipped"

        now_iso = datetime.now(UTC).isoformat()
        status_map = {
            "completed": "completed",
            "completed_after_cap": "completed_after_cap",
            "skipped_calibration": "skipped_calibration",
        }

        self._repository.insert_onboarding_calibration_event(
            payload={
                "user_id": user.user_id,
                "event_type": event_type,
                "loop_index": 0,
                "feedback": {"completion_mode": completion_mode},
            }
        )

        self._repository.update_user(
            user_id=user.user_id,
            fields={
                "onboarding_status": status_map[completion_mode],
                "onboarding_step": "done",
                "onboarding_completed_at": now_iso,
                "calibration_last_result": completion_mode,
            },
        )

        return {
            "message": "Onboarding completed successfully",
            "status": status_map[completion_mode],
            "step": "done",
            "onboarding_complete": True,
        }

    def _enforce_calibration_quota(self, *, user_id: str) -> None:
        used_today = self._repository.count_onboarding_calibration_events_today(user_id=user_id)
        if used_today >= self._calibration_events_per_day_limit:
            raise ApiError(
                status_code=429,
                code="QUOTA_EXCEEDED",
                message="Daily onboarding calibration quota exceeded.",
                details={
                    "daily_limit": self._calibration_events_per_day_limit,
                    "used_today": used_today,
                },
            )

    def _build_example_messages(self, *, user_id: str, feedback_hint: str, loop_index: int) -> list[dict]:
        profile_snapshot = self._repository.get_profile_snapshot(user_id=user_id)
        target_roles = profile_snapshot.get("target_roles")
        role = "technical roles"
        if isinstance(target_roles, list) and target_roles:
            role = str(target_roles[0]).strip() or role

        job_preferences = profile_snapshot.get("job_preferences")
        industry = "technology"
        if isinstance(job_preferences, dict):
            industries = job_preferences.get("industries")
            if isinstance(industries, list) and industries:
                industry = str(industries[0]).strip() or industry

        examples: list[dict] = []
        for index in range(CALIBRATION_EXAMPLE_COUNT):
            company_name = f"Example {industry.title()} Co {loop_index + 1}-{index + 1}"
            founder_name = f"Founder {index + 1}"
            founder = {"name": founder_name, "email": None}
            company = {"name": company_name, "domain": f"example-{loop_index + 1}-{index + 1}.test"}

            draft = self._generate_with_retry(
                company=company,
                founder=founder,
                profile_snapshot=profile_snapshot,
            )
            message_content = draft["message_content"]
            if feedback_hint:
                message_content = f"{message_content}\n\nRefinement hint: {feedback_hint}"

            examples.append(
                {
                    "example_id": f"loop-{loop_index + 1}-example-{index + 1}",
                    "founder_name": founder_name,
                    "company_name": company_name,
                    "target_role_context": role,
                    "industry_context": industry,
                    "subject": draft["subject"],
                    "message_content": message_content,
                }
            )

        return examples

    def _generate_with_retry(self, *, company: dict, founder: dict, profile_snapshot: dict) -> dict:
        try:
            return call_with_backoff(
                operation=lambda: self._gemini_client.generate_outreach_draft(
                    company=company,
                    founder=founder,
                    profile_snapshot=profile_snapshot,
                ),
                retryable_codes=GEMINI_RETRYABLE_CODES,
                max_attempts=self._gemini_max_attempts,
                base_delay_seconds=self._gemini_base_delay_seconds,
                max_jitter_seconds=self._gemini_max_jitter_seconds,
            )
        except ProviderError as exc:
            raise ApiError(
                status_code=502,
                code=exc.code,
                message=exc.message,
            ) from exc

    def _require_user_row(self, *, user: AuthenticatedUser) -> dict:
        self._repository.ensure_user_exists(user_id=user.user_id, email=user.email)
        user_row = self._repository.get_user(user_id=user.user_id)
        if user_row is None:
            raise ApiError(
                status_code=500,
                code="INTERNAL_SERVER_ERROR",
                message="Failed to resolve user row.",
            )
        return user_row

    def _serialize_user(self, user_row: dict) -> dict:
        return {
            "id": user_row.get("id"),
            "email": user_row.get("email"),
            "premium_status": bool(user_row.get("premium_status", False)),
            "tokens_used": int(user_row.get("tokens_used", 0)),
            "auto_send_enabled": bool(user_row.get("auto_send_enabled", False)),
            "message_preferences": user_row.get("message_preferences") or {},
            "first_name": user_row.get("first_name"),
            "last_name": user_row.get("last_name"),
            "onboarding_status": user_row.get("onboarding_status"),
            "onboarding_step": user_row.get("onboarding_step"),
            "onboarding_completed_at": user_row.get("onboarding_completed_at"),
            "created_at": user_row.get("created_at"),
            "updated_at": user_row.get("updated_at"),
        }

    def _max_step(self, current: object, target: OnboardingStep) -> OnboardingStep:
        current_str = str(current or "auth")
        try:
            current_index = STEP_ORDER.index(current_str)  # type: ignore[arg-type]
        except ValueError:
            current_index = 0
        target_index = STEP_ORDER.index(target)
        return STEP_ORDER[max(current_index, target_index)]
