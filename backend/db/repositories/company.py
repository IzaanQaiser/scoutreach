from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.models.company import Company


def create_company(
    session: Session,
    *,
    name: str,
    normalized_name: str,
    source: str,
    domain: str | None = None,
    website: str | None = None,
    description: str | None = None,
    stage: str | None = None,
    location: str | None = None,
    source_external_id: str | None = None,
    source_metadata: dict[str, object] | None = None,
) -> Company:
    company = Company(
        name=name,
        normalized_name=normalized_name,
        source=source,
        domain=domain,
        website=website,
        description=description,
        stage=stage,
        location=location,
        source_external_id=source_external_id,
        source_metadata=source_metadata or {},
    )
    session.add(company)
    session.flush()
    return company


def upsert_company(
    session: Session,
    *,
    name: str,
    normalized_name: str,
    source: str,
    domain: str | None = None,
    website: str | None = None,
    description: str | None = None,
    stage: str | None = None,
    location: str | None = None,
    source_external_id: str | None = None,
    source_metadata: dict[str, object] | None = None,
) -> Company:
    if source_external_id is None:
        return create_company(
            session,
            name=name,
            normalized_name=normalized_name,
            source=source,
            domain=domain,
            website=website,
            description=description,
            stage=stage,
            location=location,
            source_external_id=source_external_id,
            source_metadata=source_metadata,
        )

    statement = (
        insert(Company)
        .values(
            name=name,
            normalized_name=normalized_name,
            source=source,
            domain=domain,
            website=website,
            description=description,
            stage=stage,
            location=location,
            source_external_id=source_external_id,
            source_metadata=source_metadata or {},
        )
        .on_conflict_do_update(
            index_elements=[Company.source, Company.source_external_id],
            index_where=Company.source_external_id.is_not(None),
            set_={
                "name": name,
                "normalized_name": normalized_name,
                "domain": domain,
                "website": website,
                "description": description,
                "stage": stage,
                "location": location,
                "source_metadata": source_metadata or {},
                "updated_at": func.now(),
            },
        )
        .returning(Company)
    )
    return session.scalars(
        statement,
        execution_options={"populate_existing": True},
    ).one()


def get_company(session: Session, company_id: int) -> Company | None:
    return session.get(Company, company_id)
