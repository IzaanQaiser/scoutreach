"""Company review endpoints for Phase 4."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.middleware.auth import AuthenticatedUser, require_current_user
from app.schemas.companies import CompanyFilterStatus, CompanyStatusUpdateRequest
from app.schemas.responses import success_response
from app.services.company_service import CompanyService


router = APIRouter(tags=["companies"])


def _get_company_service(request: Request) -> CompanyService:
    return request.app.state.company_service


@router.get("/runs/{run_id}/companies")
def list_run_companies(
    run_id: str,
    status: CompanyFilterStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: AuthenticatedUser = Depends(require_current_user),
    company_service: CompanyService = Depends(_get_company_service),
) -> dict:
    return success_response(
        company_service.list_run_companies(
            user=user,
            run_id=run_id,
            status=status,
            limit=limit,
            offset=offset,
        )
    )


@router.patch("/companies/{company_id}")
def update_company_status(
    company_id: str,
    payload: CompanyStatusUpdateRequest,
    user: AuthenticatedUser = Depends(require_current_user),
    company_service: CompanyService = Depends(_get_company_service),
) -> dict:
    return success_response(
        company_service.update_company_status(
            user=user,
            company_id=company_id,
            status=payload.status,
        )
    )


@router.get("/runs/{run_id}/companies/pending-count")
def get_pending_count(
    run_id: str,
    user: AuthenticatedUser = Depends(require_current_user),
    company_service: CompanyService = Depends(_get_company_service),
) -> dict:
    return success_response(
        company_service.get_pending_count(
            user=user,
            run_id=run_id,
        )
    )
