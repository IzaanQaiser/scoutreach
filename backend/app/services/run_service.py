"""Run orchestration service for Phase 2."""

from __future__ import annotations

from datetime import UTC, datetime

from app.db.run_repository import RunRepository
from app.integrations.playwright_scraper import PlaywrightYcScraper
from app.middleware.auth import AuthenticatedUser
from app.middleware.errors import ApiError
from app.models.statuses import (
    COMPANY_STATUS_PENDING_REVIEW,
    COMPANY_STATUS_SCRAPE_FAILED,
    RUN_STATUS_COMPLETED,
    RUN_STATUS_COMPLETED_WITH_ERRORS,
    RUN_STATUS_FAILED,
    RUN_STATUS_RUNNING,
    RUN_STATUS_SCRAPING,
)

DEFAULT_RUNS_PER_DAY_LIMIT = 3


class RunService:
    def __init__(
        self,
        *,
        repository: RunRepository,
        scraper: PlaywrightYcScraper,
        runs_per_day_limit: int = DEFAULT_RUNS_PER_DAY_LIMIT,
    ) -> None:
        self._repository = repository
        self._scraper = scraper
        self._runs_per_day_limit = runs_per_day_limit

    def create_run(self, *, user: AuthenticatedUser, selected_batches: list[str]) -> dict:
        self._repository.ensure_user_exists(user_id=user.user_id, email=user.email)

        if self._repository.count_runs_created_today(user_id=user.user_id) >= self._runs_per_day_limit:
            raise ApiError(
                status_code=429,
                code="RATE_LIMITED",
                message="Daily run limit reached.",
                details={"limit": self._runs_per_day_limit},
            )

        if self._repository.has_active_run(user_id=user.user_id):
            raise ApiError(
                status_code=409,
                code="RUN_ALREADY_ACTIVE",
                message="An active run already exists.",
            )

        profile_snapshot = self._repository.get_profile_snapshot(user_id=user.user_id)
        run = self._repository.create_run(
            user_id=user.user_id,
            selected_batches=selected_batches,
            profile_snapshot=profile_snapshot,
            status=RUN_STATUS_RUNNING,
            progress=0,
        )

        return {
            "run_id": run["id"],
            "status": run["status"],
            "progress": run["progress"],
            "message": "Run started successfully",
        }

    def process_run(self, *, run_id: str, selected_batches: list[str]) -> None:
        try:
            scraped = list(self._scraper.scrape_batches(selected_batches))
            total = len(scraped)
            completed = 0

            self._repository.update_run(
                run_id=run_id,
                fields={
                    "status": RUN_STATUS_SCRAPING,
                    "progress": 0,
                    "error_message": None,
                },
            )

            for company in scraped:
                if company.scrape_failed:
                    self._repository.insert_company(
                        payload={
                            "run_id": run_id,
                            "name": company.name,
                            "yc_url": company.yc_url,
                            "website_url": company.website_url,
                            "domain": company.domain,
                            "batch": company.batch,
                            "founders": company.founders,
                            "raw_scraped_data": {
                                **company.raw_scraped_data,
                                "scrape_error": company.failure_reason,
                            },
                            "website_content": {},
                            "tags": [],
                            "dossier": {},
                            "status": COMPANY_STATUS_SCRAPE_FAILED,
                            "fit_score": None,
                        }
                    )
                else:
                    self._repository.insert_company(
                        payload={
                            "run_id": run_id,
                            "name": company.name,
                            "yc_url": company.yc_url,
                            "website_url": company.website_url,
                            "domain": company.domain,
                            "batch": company.batch,
                            "founders": company.founders,
                            "raw_scraped_data": company.raw_scraped_data,
                            "website_content": {},
                            "tags": [],
                            "dossier": {},
                            "status": COMPANY_STATUS_PENDING_REVIEW,
                            "fit_score": None,
                        }
                    )

                completed += 1
                progress = int((completed / total) * 100) if total > 0 else 100
                self._repository.update_run(
                    run_id=run_id,
                    fields={
                        "status": RUN_STATUS_SCRAPING,
                        "progress": min(progress, 99),
                    },
                )

            failed_count = self._repository.count_companies_for_run_by_status(
                run_id=run_id,
                status=COMPANY_STATUS_SCRAPE_FAILED,
            )
            final_status = RUN_STATUS_COMPLETED_WITH_ERRORS if failed_count > 0 else RUN_STATUS_COMPLETED

            self._repository.update_run(
                run_id=run_id,
                fields={
                    "status": final_status,
                    "progress": 100,
                    "completed_at": datetime.now(UTC).isoformat(),
                    "error_message": None,
                },
            )
        except Exception as exc:  # pragma: no cover - defensive hard-failure path
            self._repository.update_run(
                run_id=run_id,
                fields={
                    "status": RUN_STATUS_FAILED,
                    "error_message": str(exc),
                    "completed_at": datetime.now(UTC).isoformat(),
                },
            )

    def get_run_status(self, *, run_id: str, user: AuthenticatedUser) -> dict:
        run = self._repository.get_run_for_user(run_id=run_id, user_id=user.user_id)
        if run is None:
            raise ApiError(
                status_code=404,
                code="NOT_FOUND",
                message="Run not found.",
            )

        companies_scraped = self._repository.count_companies_for_run(run_id=run_id)
        selected_batches = run.get("selected_batches") or []
        companies_total_estimate = max(len(selected_batches), companies_scraped)

        return {
            "run_id": run["id"],
            "status": run["status"],
            "progress": run["progress"],
            "error_message": run.get("error_message"),
            "companies_scraped": companies_scraped,
            "companies_total_estimate": companies_total_estimate,
            "messages_generated": 0,
            "messages_sent": 0,
        }

