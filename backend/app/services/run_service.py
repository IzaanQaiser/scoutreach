"""Run orchestration service for Phase 2/3."""

from __future__ import annotations

from datetime import UTC, datetime
import logging

from app.db.run_repository import RunRepository
from app.integrations.gemini_client import GeminiDossierClient
from app.integrations.hunter_client import HunterEmailClient
from app.integrations.playwright_scraper import PlaywrightYcScraper, ScrapedCompany
from app.integrations.provider_errors import ProviderError
from app.middleware.auth import AuthenticatedUser
from app.middleware.errors import ApiError
from app.models.statuses import (
    COMPANY_STATUS_DOSSIER_FAILED,
    COMPANY_STATUS_PENDING_REVIEW,
    COMPANY_STATUS_SCRAPE_FAILED,
    RUN_STATUS_COMPLETED,
    RUN_STATUS_COMPLETED_WITH_ERRORS,
    RUN_STATUS_DOSSIER_GENERATING,
    RUN_STATUS_ENRICHING,
    RUN_STATUS_FAILED,
    RUN_STATUS_RUNNING,
    RUN_STATUS_SCRAPING,
)


logger = logging.getLogger(__name__)

DEFAULT_RUNS_PER_DAY_LIMIT = 3


class RunService:
    def __init__(
        self,
        *,
        repository: RunRepository,
        scraper: PlaywrightYcScraper,
        gemini_client: GeminiDossierClient,
        hunter_client: HunterEmailClient,
        runs_per_day_limit: int = DEFAULT_RUNS_PER_DAY_LIMIT,
    ) -> None:
        self._repository = repository
        self._scraper = scraper
        self._gemini_client = gemini_client
        self._hunter_client = hunter_client
        self._runs_per_day_limit = runs_per_day_limit

    def create_run(self, *, user: AuthenticatedUser, selected_batches: list[str]) -> dict:
        self._repository.ensure_user_exists(user_id=user.user_id, email=user.email)

        if self._repository.count_runs_created_today(user_id=user.user_id) >= self._runs_per_day_limit:
            logger.warning("run_quota_rejected", extra={"user_id": user.user_id})
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

        logger.info("run_created", extra={"run_id": run["id"], "user_id": user.user_id})

        return {
            "run_id": run["id"],
            "status": run["status"],
            "progress": run["progress"],
            "message": "Run started successfully",
        }

    def process_run(self, *, run_id: str, selected_batches: list[str]) -> None:
        failure_counts = {
            "scrape_failed": 0,
            "dossier_failed": 0,
            "hunter_failed": 0,
        }

        try:
            self._repository.update_run(
                run_id=run_id,
                fields={
                    "status": RUN_STATUS_SCRAPING,
                    "progress": 0,
                    "error_message": None,
                },
            )
            logger.info("scrape_started", extra={"run_id": run_id})

            scraped_companies = list(self._scraper.scrape_batches(selected_batches))
            total_companies = len(scraped_companies)

            for index, company in enumerate(scraped_companies, start=1):
                company_payload = self._build_company_payload(
                    run_id=run_id,
                    company=company,
                    failure_counts=failure_counts,
                )
                self._repository.insert_company(payload=company_payload)

                progress = int((index / total_companies) * 100) if total_companies > 0 else 100
                self._repository.update_run(
                    run_id=run_id,
                    fields={
                        "status": RUN_STATUS_SCRAPING,
                        "progress": min(progress, 99),
                    },
                )

            has_errors = any(count > 0 for count in failure_counts.values())
            final_status = RUN_STATUS_COMPLETED_WITH_ERRORS if has_errors else RUN_STATUS_COMPLETED
            final_error_message = self._build_error_summary(failure_counts) if has_errors else None

            self._repository.update_run(
                run_id=run_id,
                fields={
                    "status": final_status,
                    "progress": 100,
                    "completed_at": datetime.now(UTC).isoformat(),
                    "error_message": final_error_message,
                },
            )
            logger.info("scrape_completed", extra={"run_id": run_id, "status": final_status})
        except Exception as exc:  # pragma: no cover - defensive hard-failure path
            logger.exception("run_processing_failed", extra={"run_id": run_id})
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

    def _build_company_payload(
        self,
        *,
        run_id: str,
        company: ScrapedCompany,
        failure_counts: dict[str, int],
    ) -> dict:
        founders_payload = [dict(founder) for founder in company.founders]
        raw_scraped_data = dict(company.raw_scraped_data)

        payload = {
            "run_id": run_id,
            "name": company.name,
            "yc_url": company.yc_url,
            "website_url": company.website_url,
            "domain": company.domain,
            "batch": company.batch,
            "founders": founders_payload,
            "raw_scraped_data": raw_scraped_data,
            "website_content": {},
            "tags": [],
            "dossier": {},
            "status": COMPANY_STATUS_PENDING_REVIEW,
            "fit_score": None,
        }

        if company.scrape_failed:
            failure_counts["scrape_failed"] += 1
            logger.warning("scrape_company_failed", extra={"run_id": run_id, "company": company.name})
            payload["status"] = COMPANY_STATUS_SCRAPE_FAILED
            payload["raw_scraped_data"] = {
                **raw_scraped_data,
                "provider_errors": {
                    "scrape": {
                        "code": "SCRAPE_FAILED",
                        "message": company.failure_reason or "Scrape failed.",
                    }
                },
            }
            return payload

        provider_errors: dict[str, dict[str, str]] = {}

        self._repository.update_run(
            run_id=run_id,
            fields={
                "status": RUN_STATUS_DOSSIER_GENERATING,
            },
        )

        try:
            payload["dossier"] = self._gemini_client.generate_company_dossier(
                company_name=company.name,
                batch=company.batch,
                tags=[],
                founders=founders_payload,
                website_content={},
                raw_scraped_data=raw_scraped_data,
            )
        except ProviderError as exc:
            failure_counts["dossier_failed"] += 1
            logger.warning("dossier_generation_failed", extra={"run_id": run_id, "company": company.name})
            payload["status"] = COMPANY_STATUS_DOSSIER_FAILED
            provider_errors[exc.provider] = {
                "code": exc.code,
                "message": exc.message,
            }

        if payload["status"] == COMPANY_STATUS_PENDING_REVIEW:
            self._repository.update_run(
                run_id=run_id,
                fields={
                    "status": RUN_STATUS_ENRICHING,
                },
            )

            try:
                payload["founders"] = self._hunter_client.enrich_founders(
                    founders=founders_payload,
                    domain=company.domain,
                )
            except ProviderError as exc:
                failure_counts["hunter_failed"] += 1
                logger.warning("hunter_lookup_failed", extra={"run_id": run_id, "company": company.name})
                provider_errors[exc.provider] = {
                    "code": exc.code,
                    "message": exc.message,
                }
                payload["founders"] = self._hunter_client.mark_lookup_failed(
                    founders=founders_payload,
                    error_message=exc.message,
                )

        if provider_errors:
            payload["raw_scraped_data"] = {
                **raw_scraped_data,
                "provider_errors": provider_errors,
            }

        return payload

    def _build_error_summary(self, failure_counts: dict[str, int]) -> str:
        return (
            "Provider/processing errors: "
            f"scrape_failed={failure_counts['scrape_failed']}, "
            f"dossier_failed={failure_counts['dossier_failed']}, "
            f"hunter_failed={failure_counts['hunter_failed']}"
        )
