"""Run endpoints for Phase 2."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Request

from app.middleware.auth import AuthenticatedUser, require_current_user
from app.schemas.responses import success_response
from app.schemas.runs import GenerateMessagesRequest, RunCreateRequest
from app.services.outreach_generation_service import OutreachGenerationService
from app.services.run_service import RunService


router = APIRouter(prefix="/runs", tags=["runs"])


def _get_run_service(request: Request) -> RunService:
    return request.app.state.run_service


def _get_outreach_generation_service(request: Request) -> OutreachGenerationService:
    return request.app.state.outreach_generation_service


@router.post("")
def create_run(
    payload: RunCreateRequest,
    background_tasks: BackgroundTasks,
    user: AuthenticatedUser = Depends(require_current_user),
    run_service: RunService = Depends(_get_run_service),
) -> dict:
    result = run_service.create_run(user=user, selected_batches=payload.selected_batches)
    background_tasks.add_task(
        run_service.process_run,
        run_id=result["run_id"],
        selected_batches=payload.selected_batches,
    )
    return success_response(result)


@router.get("/{run_id}/status")
def get_run_status(
    run_id: str,
    user: AuthenticatedUser = Depends(require_current_user),
    run_service: RunService = Depends(_get_run_service),
) -> dict:
    return success_response(run_service.get_run_status(run_id=run_id, user=user))


@router.post("/{run_id}/generate-messages")
def generate_messages(
    run_id: str,
    payload: GenerateMessagesRequest,
    user: AuthenticatedUser = Depends(require_current_user),
    outreach_generation_service: OutreachGenerationService = Depends(_get_outreach_generation_service),
) -> dict:
    return success_response(
        outreach_generation_service.generate_messages(
            user=user,
            run_id=run_id,
            founder_selection_strategy=payload.founder_selection_strategy,
            max_messages=payload.max_messages,
        )
    )
