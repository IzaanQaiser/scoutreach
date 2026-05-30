"""Account and onboarding endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.middleware.auth import AuthenticatedUser, require_current_user
from app.schemas.account import (
    CandidateProfileUpsertRequest,
    OnboardingCompleteRequest,
    OnboardingExampleFeedbackRequest,
    OnboardingGenerateExamplesRequest,
    SettingsUpdateRequest,
)
from app.schemas.responses import success_response
from app.services.account_service import AccountService


router = APIRouter(tags=["account"])


def _get_account_service(request: Request) -> AccountService:
    return request.app.state.account_service


@router.get("/candidate-profile")
def get_candidate_profile(
    user: AuthenticatedUser = Depends(require_current_user),
    account_service: AccountService = Depends(_get_account_service),
) -> dict:
    return success_response(account_service.get_candidate_profile(user=user))


@router.put("/candidate-profile")
def upsert_candidate_profile(
    payload: CandidateProfileUpsertRequest,
    user: AuthenticatedUser = Depends(require_current_user),
    account_service: AccountService = Depends(_get_account_service),
) -> dict:
    return success_response(
        account_service.upsert_candidate_profile(
            user=user,
            fields=payload.model_dump(),
        )
    )


@router.get("/settings")
def get_settings(
    user: AuthenticatedUser = Depends(require_current_user),
    account_service: AccountService = Depends(_get_account_service),
) -> dict:
    return success_response(account_service.get_settings(user=user))


@router.patch("/settings")
def patch_settings(
    payload: SettingsUpdateRequest,
    user: AuthenticatedUser = Depends(require_current_user),
    account_service: AccountService = Depends(_get_account_service),
) -> dict:
    return success_response(
        account_service.update_settings(
            user=user,
            auto_send_enabled=payload.auto_send_enabled,
            message_preferences=payload.message_preferences,
        )
    )


@router.get("/onboarding/state")
def get_onboarding_state(
    user: AuthenticatedUser = Depends(require_current_user),
    account_service: AccountService = Depends(_get_account_service),
) -> dict:
    return success_response(account_service.get_onboarding_state(user=user))


@router.post("/onboarding/example-messages")
def generate_onboarding_example_messages(
    payload: OnboardingGenerateExamplesRequest,
    user: AuthenticatedUser = Depends(require_current_user),
    account_service: AccountService = Depends(_get_account_service),
) -> dict:
    return success_response(
        account_service.generate_onboarding_examples(
            user=user,
            loop_index=payload.loop_index,
        )
    )


@router.post("/onboarding/example-feedback")
def submit_onboarding_feedback(
    payload: OnboardingExampleFeedbackRequest,
    user: AuthenticatedUser = Depends(require_current_user),
    account_service: AccountService = Depends(_get_account_service),
) -> dict:
    return success_response(
        account_service.submit_onboarding_feedback(
            user=user,
            loop_index=payload.loop_index,
            rejected_examples=[item.model_dump() for item in payload.rejected_examples],
        )
    )


@router.post("/onboarding/complete")
def complete_onboarding(
    payload: OnboardingCompleteRequest,
    user: AuthenticatedUser = Depends(require_current_user),
    account_service: AccountService = Depends(_get_account_service),
) -> dict:
    return success_response(
        account_service.complete_onboarding(
            user=user,
            completion_mode=payload.completion_mode,
        )
    )
