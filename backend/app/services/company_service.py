"""Company review service for Phase 4."""

from __future__ import annotations

from datetime import UTC, datetime

from app.db.run_repository import RunRepository
from app.middleware.auth import AuthenticatedUser
from app.middleware.errors import ApiError
from app.models.statuses import COMPANY_REVIEW_STATUSES, COMPANY_STATUS_PENDING_REVIEW


class CompanyService:
    def __init__(self, *, repository: RunRepository) -> None:
        self._repository = repository

    def list_run_companies(
        self,
        *,
        user: AuthenticatedUser,
        run_id: str,
        status: str | None,
        limit: int,
        offset: int,
    ) -> dict:
        self._require_run_owner(run_id=run_id, user_id=user.user_id)
        companies = self._repository.list_companies_for_run(
            run_id=run_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        return {"companies": companies}

    def get_pending_count(self, *, user: AuthenticatedUser, run_id: str) -> dict:
        self._require_run_owner(run_id=run_id, user_id=user.user_id)
        pending_count = self._repository.count_companies_for_run_by_status(
            run_id=run_id,
            status=COMPANY_STATUS_PENDING_REVIEW,
        )
        return {
            "run_id": run_id,
            "pending_count": pending_count,
        }

    def update_company_status(self, *, user: AuthenticatedUser, company_id: str, status: str) -> dict:
        company = self._repository.get_company(company_id=company_id)
        if company is None:
            raise ApiError(
                status_code=404,
                code="NOT_FOUND",
                message="Company not found.",
            )

        run_id = str(company["run_id"])
        self._require_run_owner(run_id=run_id, user_id=user.user_id)

        current_status = str(company.get("status", ""))
        if current_status not in COMPANY_REVIEW_STATUSES:
            raise ApiError(
                status_code=409,
                code="INVALID_STATUS_TRANSITION",
                message="Company status cannot be updated from current state.",
                details={"current_status": current_status, "requested_status": status},
            )

        self._repository.update_company(
            company_id=company_id,
            fields={
                "status": status,
                "updated_at": datetime.now(UTC).isoformat(),
            },
        )

        return {
            "company_id": company_id,
            "status": status,
            "message": "Company status updated successfully",
        }

    def _require_run_owner(self, *, run_id: str, user_id: str) -> None:
        run = self._repository.get_run_for_user(run_id=run_id, user_id=user_id)
        if run is None:
            raise ApiError(
                status_code=404,
                code="NOT_FOUND",
                message="Run not found.",
            )
