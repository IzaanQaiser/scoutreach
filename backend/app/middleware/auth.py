"""Authentication dependency for protected API routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client

from app.middleware.errors import ApiError
from app.utils.settings import Settings


http_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    email: str


def _unauthorized(message: str = "Authentication required.") -> ApiError:
    return ApiError(
        status_code=401,
        code="UNAUTHORIZED",
        message=message,
    )


def _extract_user(auth_response: Any) -> tuple[str, str] | None:
    """Extract user id/email from supabase auth response variants."""
    user = None

    if hasattr(auth_response, "user") and auth_response.user is not None:
        user = auth_response.user
    elif hasattr(auth_response, "data") and auth_response.data is not None:
        data = auth_response.data
        if isinstance(data, dict):
            user = data.get("user")
        elif hasattr(data, "user"):
            user = data.user
    elif isinstance(auth_response, dict):
        user = auth_response.get("user")

    if user is None:
        return None

    user_id = getattr(user, "id", None)
    email = getattr(user, "email", None)

    if isinstance(user, dict):
        user_id = user.get("id")
        email = user.get("email")

    if not user_id:
        return None

    return str(user_id), str(email or "")


def _resolve_with_supabase(token: str, supabase_client: Client) -> AuthenticatedUser:
    try:
        auth_response = supabase_client.auth.get_user(token)
    except Exception as exc:  # pragma: no cover - dependency/network failure path
        raise _unauthorized("Token verification failed.") from exc

    extracted = _extract_user(auth_response)
    if extracted is None:
        raise _unauthorized("Invalid or expired token.")

    user_id, email = extracted
    return AuthenticatedUser(user_id=user_id, email=email)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> AuthenticatedUser:
    if credentials is None or not credentials.credentials:
        raise _unauthorized()

    settings: Settings = request.app.state.settings
    token = credentials.credentials

    if settings.allow_dev_auth and token == settings.dev_auth_token:
        return AuthenticatedUser(
            user_id=settings.dev_auth_user_id,
            email=settings.dev_auth_email,
        )

    supabase_client: Client = request.app.state.supabase_client
    return _resolve_with_supabase(token=token, supabase_client=supabase_client)


def require_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(http_bearer),
) -> AuthenticatedUser:
    return get_current_user(request=request, credentials=credentials)
