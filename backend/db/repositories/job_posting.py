from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.models.job_posting import JobPosting


def create_job_posting(
    session: Session,
    *,
    company_id: int,
    external_id: str,
    title: str,
    source: str,
    active: bool,
    seen_at: datetime,
    function: str | None = None,
    location: str | None = None,
    url: str | None = None,
    raw_metadata: dict[str, object] | None = None,
) -> JobPosting:
    job_posting = JobPosting(
        company_id=company_id,
        external_id=external_id,
        title=title,
        source=source,
        function=function,
        location=location,
        url=url,
        active=active,
        raw_metadata=raw_metadata or {},
        seen_at=seen_at,
    )
    session.add(job_posting)
    session.flush()
    return job_posting


def upsert_job_posting(
    session: Session,
    *,
    company_id: int,
    external_id: str,
    title: str,
    source: str,
    active: bool,
    seen_at: datetime,
    function: str | None = None,
    location: str | None = None,
    url: str | None = None,
    raw_metadata: dict[str, object] | None = None,
) -> JobPosting:
    statement = (
        insert(JobPosting)
        .values(
            company_id=company_id,
            external_id=external_id,
            title=title,
            source=source,
            function=function,
            location=location,
            url=url,
            active=active,
            raw_metadata=raw_metadata or {},
            seen_at=seen_at,
        )
        .on_conflict_do_update(
            index_elements=[JobPosting.source, JobPosting.external_id],
            set_={
                "company_id": company_id,
                "title": title,
                "function": function,
                "location": location,
                "url": url,
                "active": active,
                "raw_metadata": raw_metadata or {},
                "seen_at": seen_at,
            },
        )
        .returning(JobPosting)
    )
    return session.scalars(
        statement,
        execution_options={"populate_existing": True},
    ).one()


def get_job_posting(session: Session, job_posting_id: int) -> JobPosting | None:
    return session.get(JobPosting, job_posting_id)
