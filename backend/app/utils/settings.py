"""Environment settings for the ScoutReach backend."""

from __future__ import annotations

import os
from dataclasses import dataclass


VALID_ENVIRONMENTS = {"development", "test", "staging", "production"}


@dataclass(frozen=True)
class Settings:
    environment: str
    supabase_url: str
    supabase_service_role_key: str
    allow_dev_auth: bool
    dev_auth_token: str
    dev_auth_user_id: str
    dev_auth_email: str

    @property
    def is_development_like(self) -> bool:
        return self.environment in {"development", "test"}


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    environment = os.getenv("SCOUTREACH_ENV", "development").strip().lower()

    settings = Settings(
        environment=environment,
        supabase_url=os.getenv("SUPABASE_URL", "").strip(),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
        allow_dev_auth=_as_bool(os.getenv("ALLOW_DEV_AUTH"), default=(environment == "development")),
        dev_auth_token=os.getenv("DEV_AUTH_TOKEN", "local-dev-token").strip(),
        dev_auth_user_id=os.getenv("DEV_AUTH_USER_ID", "00000000-0000-0000-0000-000000000001").strip(),
        dev_auth_email=os.getenv("DEV_AUTH_EMAIL", "dev@scoutreach.local").strip(),
    )

    validate_required_settings(settings)
    return settings


def validate_required_settings(settings: Settings) -> None:
    if settings.environment not in VALID_ENVIRONMENTS:
        raise RuntimeError(
            "Invalid SCOUTREACH_ENV. Expected one of: "
            f"{', '.join(sorted(VALID_ENVIRONMENTS))}."
        )

    missing = []
    if not settings.supabase_url:
        missing.append("SUPABASE_URL")
    if not settings.supabase_service_role_key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")

    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Copy backend/.env.example and set values."
        )

    if settings.allow_dev_auth and not settings.is_development_like:
        raise RuntimeError("ALLOW_DEV_AUTH cannot be enabled outside development/test environments.")
