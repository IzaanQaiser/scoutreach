"""Authenticated user routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.middleware.auth import AuthenticatedUser, require_current_user
from app.schemas.account import MeUpdateRequest
from app.schemas.responses import success_response
from app.services.account_service import AccountService


router = APIRouter()


def _get_account_service(request: Request) -> AccountService:
    return request.app.state.account_service


@router.get("/me")
def get_current_user_profile(
    current_user: AuthenticatedUser = Depends(require_current_user),
    account_service: AccountService = Depends(_get_account_service),
) -> dict:
    return success_response(account_service.get_me(user=current_user))


@router.patch("/me")
def update_current_user_profile(
    payload: MeUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_current_user),
    account_service: AccountService = Depends(_get_account_service),
) -> dict:
    return success_response(
        account_service.update_me(
            user=current_user,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
    )
