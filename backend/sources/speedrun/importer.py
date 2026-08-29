from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy.orm import Session

from backend.db.repositories.company import upsert_company
from backend.db.repositories.job_posting import (
    deactivate_missing_job_postings,
    upsert_job_posting,
)
from backend.sources.speedrun.types import SpeedrunCompany, SpeedrunCompanyDetail


SOURCE = "speedrun"


class SpeedrunImportClient(Protocol):
    def list_companies(self, limit: int) -> list[SpeedrunCompany]: ...

    def get_company(self, slug: str) -> SpeedrunCompanyDetail: ...


def import_speedrun(
    session: Session,
    client: SpeedrunImportClient,
    limit: int,
) -> None:
    companies = client.list_companies(limit)

    for listed_company in companies:
        detail = client.get_company(listed_company.slug)
        provider_company = detail.company
        company = upsert_company(
            session,
            name=provider_company.name,
            normalized_name=_normalize_name(provider_company.name),
            source=SOURCE,
            description=provider_company.blurb,
            location=provider_company.location,
            source_external_id=provider_company.slug,
            source_metadata={
                "url": provider_company.url,
                "tier": provider_company.tier,
                "open_roles": provider_company.open_roles,
                "cohort": provider_company.cohort,
                "industries": provider_company.industries,
                "logo": provider_company.logo,
            },
        )

        seen_at = datetime.now(timezone.utc)
        live_external_ids: set[str] = set()
        for provider_job in provider_company.jobs:
            external_id = str(provider_job.id)
            live_external_ids.add(external_id)
            upsert_job_posting(
                session,
                company_id=company.id,
                external_id=external_id,
                title=provider_job.title,
                source=SOURCE,
                location=provider_job.location,
                url=provider_job.url,
                active=True,
                seen_at=seen_at,
                raw_metadata=provider_job.model_dump(
                    exclude={"id", "title", "location", "url"}
                ),
            )

        deactivate_missing_job_postings(
            session,
            company_id=company.id,
            source=SOURCE,
            live_external_ids=live_external_ids,
        )


def _normalize_name(name: str) -> str:
    return " ".join(name.split()).lower()
