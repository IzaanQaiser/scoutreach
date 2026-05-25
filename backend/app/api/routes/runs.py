"""Run endpoints for Phase 2."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Request

from app.middleware.auth import AuthenticatedUser, require_current_user
from app.schemas.responses import success_response
from app.schemas.runs import RunCreateRequest
from app.services.run_service import RunService


router = APIRouter(prefix="/runs", tags=["runs"])


def _get_run_service(request: Request) -> RunService:
    return request.app.state.run_service


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

