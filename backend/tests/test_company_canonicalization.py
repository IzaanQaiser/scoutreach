import os
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, delete, inspect, select, update
from sqlalchemy.orm import Session, sessionmaker

from backend.db.company_canonicalization import (
    CompanyCanonicalizationAmbiguityError,
    canonicalize_company,
    get_canonical_company_view,
)
from backend.db.repositories.company import create_company
from backend.db.repositories.job_posting import create_job_posting
from backend.db.session import create_db_engine, create_session_factory
from backend.models.company import Company
from backend.models.job_posting import JobPosting


TEST_SOURCES = ["canon-a", "canon-b", "canon-c", "speedrun", "topstartups"]


@pytest.fixture(scope="module")
def postgres_runtime() -> Iterator[tuple[Engine, sessionmaker[Session]]]:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for persistence tests")

    environment = pytest.MonkeyPatch()
    environment.setenv("DATABASE_URL", database_url)
    engine = create_db_engine(database_url)
    try:
        command.upgrade(Config("alembic.ini"), "head")
        yield engine, create_session_factory(engine)
    except Exception:
        pytest.fail(
            "Dedicated test PostgreSQL company canonicalization setup failed",
            pytrace=False,
        )
    finally:
        engine.dispose()
        environment.undo()


@pytest.fixture
def session_factory(
    postgres_runtime: tuple[Engine, sessionmaker[Session]],
) -> Iterator[sessionmaker[Session]]:
    _, factory = postgres_runtime
    with factory.begin() as session:
        session.execute(
            delete(JobPosting).where(JobPosting.source.in_(TEST_SOURCES))
        )
        session.execute(
            update(Company)
            .where(Company.source.in_(TEST_SOURCES))
            .values(canonical_company_id=None)
        )
        session.execute(delete(Company).where(Company.source.in_(TEST_SOURCES)))
    yield factory
    with factory.begin() as session:
        session.execute(
            delete(JobPosting).where(JobPosting.source.in_(TEST_SOURCES))
        )
        session.execute(
            update(Company)
            .where(Company.source.in_(TEST_SOURCES))
            .values(canonical_company_id=None)
        )
        session.execute(delete(Company).where(Company.source.in_(TEST_SOURCES)))


def create_test_company(
    session: Session,
    *,
    source: str,
    name: str,
    normalized_name: str,
    domain: str | None,
    website: str | None = None,
) -> Company:
    return create_company(
        session,
        name=name,
        normalized_name=normalized_name,
        source=source,
        domain=domain,
        website=website,
        source_external_id=f"{source}-{name}",
        source_metadata={"provider": source},
    )


def test_migration_adds_nullable_canonical_company_index(
    postgres_runtime: tuple[Engine, sessionmaker[Session]],
) -> None:
    engine, _ = postgres_runtime
    inspector = inspect(engine)

    columns = {column["name"]: column for column in inspector.get_columns("companies")}
    indexes = {index["name"] for index in inspector.get_indexes("companies")}

    assert columns["canonical_company_id"]["nullable"] is True
    assert "ix_companies_canonical_company_id" in indexes


def test_equal_normalized_domains_merge_without_losing_provenance(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory.begin() as session:
        first = create_test_company(
            session,
            source="canon-a",
            name="Domain One",
            normalized_name="domain one",
            domain="WWW.Example.COM.",
        )
        second = create_test_company(
            session,
            source="canon-b",
            name="Different Display Name",
            normalized_name="different display name",
            domain="https://example.com/about",
        )
        first_id, second_id = first.id, second.id
        result = canonicalize_company(session, second_id)

        assert result.canonical_company_id == first_id
        assert result.merged_company_ids == [second_id]

    with session_factory() as session:
        first = session.get(Company, first_id)
        second = session.get(Company, second_id)
        assert first is not None and second is not None
        assert first.canonical_company_id is None
        assert second.canonical_company_id == first_id
        assert first.source == "canon-a"
        assert second.source == "canon-b"
        assert first.source_metadata == {"provider": "canon-a"}
        assert second.source_metadata == {"provider": "canon-b"}


def test_different_domains_do_not_fallback_to_same_name(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory.begin() as session:
        first = create_test_company(
            session,
            source="canon-a",
            name="Same Name",
            normalized_name="same name",
            domain="first.example",
        )
        second = create_test_company(
            session,
            source="canon-b",
            name="Same Name",
            normalized_name="same name",
            domain="second.example",
        )
        result = canonicalize_company(session, second.id)

        assert result.canonical_company_id == second.id
        assert result.merged_company_ids == []
        assert first.canonical_company_id is None
        assert second.canonical_company_id is None


def test_domainless_speedrun_and_topstartups_merge_with_canonical_job_view(
    session_factory: sessionmaker[Session],
) -> None:
    older = datetime.now(timezone.utc) - timedelta(days=1)
    newer = datetime.now(timezone.utc)
    with session_factory.begin() as session:
        speedrun = create_test_company(
            session,
            source="speedrun",
            name="Acme Labs",
            normalized_name="acme labs",
            domain=None,
        )
        topstartups = create_test_company(
            session,
            source="topstartups",
            name="Acme Labs",
            normalized_name="acme labs",
            domain="www.acme.example.",
            website="https://acme.example",
        )
        speedrun_id, topstartups_id = speedrun.id, topstartups.id
        speedrun_job = create_job_posting(
            session,
            company_id=speedrun.id,
            external_id="speedrun-job",
            title="Speedrun Role",
            source="speedrun",
            active=True,
            seen_at=older,
        )
        topstartups_job = create_job_posting(
            session,
            company_id=topstartups.id,
            external_id="topstartups-job",
            title="Fresh Role",
            source="topstartups",
            active=True,
            seen_at=newer,
        )
        speedrun_job_id = speedrun_job.id
        topstartups_job_id = topstartups_job.id

        first_result = canonicalize_company(session, speedrun.id)
        second_result = canonicalize_company(session, topstartups.id)

        assert first_result.canonical_company_id == speedrun_id
        assert first_result.merged_company_ids == [topstartups_id]
        assert second_result == first_result

    with session_factory() as session:
        view = get_canonical_company_view(session, topstartups_id)
        speedrun_job = session.get(JobPosting, speedrun_job_id)
        topstartups_job = session.get(JobPosting, topstartups_job_id)

        assert view.canonical_company_id == speedrun_id
        assert view.member_company_ids == [speedrun_id, topstartups_id]
        assert view.preferred_domain == "www.acme.example."
        assert view.preferred_website == "https://acme.example"
        assert [job.id for job in view.jobs] == [topstartups_job_id, speedrun_job_id]
        assert view.freshest_job is not None
        assert view.freshest_job.id == topstartups_job_id
        assert speedrun_job is not None and topstartups_job is not None
        assert speedrun_job.company_id == speedrun_id
        assert topstartups_job.company_id == topstartups_id
        assert speedrun_job.source == "speedrun"
        assert topstartups_job.source == "topstartups"


def test_ambiguous_name_fallback_across_distinct_domains_errors(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory.begin() as session:
        domainless = create_test_company(
            session,
            source="canon-a",
            name="Ambiguous",
            normalized_name="ambiguous",
            domain=None,
        )
        create_test_company(
            session,
            source="canon-b",
            name="Ambiguous",
            normalized_name="ambiguous",
            domain="one.example",
        )
        create_test_company(
            session,
            source="canon-c",
            name="Ambiguous",
            normalized_name="ambiguous",
            domain="two.example",
        )

        with pytest.raises(CompanyCanonicalizationAmbiguityError):
            canonicalize_company(session, domainless.id)

        companies = list(
            session.scalars(
                select(Company).where(Company.source.in_(TEST_SOURCES))
            )
        )
        assert all(company.canonical_company_id is None for company in companies)
