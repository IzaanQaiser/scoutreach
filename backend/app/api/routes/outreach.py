"""Outreach review/regenerate/send endpoints for Phase 6."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.middleware.auth import AuthenticatedUser, require_current_user
from app.schemas.outreach import (
    OutreachFilterStatus,
    OutreachRegenerateRequest,
    OutreachUpdateRequest,
    SendApprovedRequest,
    SendSingleRequest,
)
from app.schemas.responses import success_response
from app.services.outreach_service import OutreachService


router = APIRouter(tags=["outreach"])


def _get_outreach_service(request: Request) -> OutreachService:
    return request.app.state.outreach_service


@router.get("/runs/{run_id}/outreach")
def list_run_outreach(
    run_id: str,
    status: OutreachFilterStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: AuthenticatedUser = Depends(require_current_user),
    outreach_service: OutreachService = Depends(_get_outreach_service),
) -> dict:
    return success_response(
        outreach_service.list_run_outreach(
            user=user,
            run_id=run_id,
            status=status,
            limit=limit,
            offset=offset,
        )
    )


@router.get("/outreach/{outreach_id}")
def get_outreach(
    outreach_id: str,
    user: AuthenticatedUser = Depends(require_current_user),
    outreach_service: OutreachService = Depends(_get_outreach_service),
) -> dict:
    return success_response(
        outreach_service.get_outreach(
            user=user,
            outreach_id=outreach_id,
        )
    )


@router.patch("/outreach/{outreach_id}")
def update_outreach(
    outreach_id: str,
    payload: OutreachUpdateRequest,
    user: AuthenticatedUser = Depends(require_current_user),
    outreach_service: OutreachService = Depends(_get_outreach_service),
) -> dict:
    return success_response(
        outreach_service.update_outreach(
            user=user,
            outreach_id=outreach_id,
            subject=payload.subject,
            message_content=payload.message_content,
            status=payload.status,
            review_notes=payload.review_notes,
        )
    )


@router.post("/outreach/{outreach_id}/regenerate")
def regenerate_outreach(
    outreach_id: str,
    payload: OutreachRegenerateRequest,
    user: AuthenticatedUser = Depends(require_current_user),
    outreach_service: OutreachService = Depends(_get_outreach_service),
) -> dict:
    return success_response(
        outreach_service.regenerate_outreach(
            user=user,
            outreach_id=outreach_id,
            critique=payload.critique,
            message_preferences_override=payload.message_preferences_override,
        )
    )


@router.get("/runs/{run_id}/outreach/review-summary")
def get_review_summary(
    run_id: str,
    user: AuthenticatedUser = Depends(require_current_user),
    outreach_service: OutreachService = Depends(_get_outreach_service),
) -> dict:
    return success_response(
        outreach_service.get_review_summary(
            user=user,
            run_id=run_id,
        )
    )


@router.post("/runs/{run_id}/send-approved")
def send_approved(
    run_id: str,
    _: SendApprovedRequest,
    user: AuthenticatedUser = Depends(require_current_user),
    outreach_service: OutreachService = Depends(_get_outreach_service),
) -> dict:
    return success_response(
        outreach_service.send_approved(
            user=user,
            run_id=run_id,
        )
    )


@router.post("/outreach/{outreach_id}/send")
def send_single_outreach(
    outreach_id: str,
    payload: SendSingleRequest,
    user: AuthenticatedUser = Depends(require_current_user),
    outreach_service: OutreachService = Depends(_get_outreach_service),
) -> dict:
    return success_response(
        outreach_service.send_single(
            user=user,
            outreach_id=outreach_id,
            confirm_send=payload.confirm_send,
        )
    )
