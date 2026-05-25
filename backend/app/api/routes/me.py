"""Authenticated user routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.middleware.auth import AuthenticatedUser, require_current_user
from app.schemas.responses import success_response


router = APIRouter()


@router.get("/me")
def get_current_user_profile(
    current_user: AuthenticatedUser = Depends(require_current_user),
) -> dict:
    return success_response(
        {
            "user": {
                "id": current_user.user_id,
                "email": current_user.email,
            },
            "has_candidate_profile": False,
            "onboarding_complete": False,
        }
    )
