import os
from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, delete, func, inspect, select
from sqlalchemy.orm import Session, sessionmaker

from backend.db.repositories.company import (
    create_company,
    get_company,
    upsert_company,
)
from backend.db.repositories.job_posting import (
    create_job_posting,
    get_job_posting,
    upsert_job_posting,
)
from backend.db.session import create_db_engine, create_session_factory
from backend.models.company import Company
from backend.models.job_posting import JobPosting


@pytest.fixture(scope="module")
def postgres_runtime() -> Iterator[tuple[Engine, sessionmaker[Session]]]:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for persistence tests")

    environment = pytest.MonkeyPatch()
    environment.setenv("DATABASE_URL", database_url)
    engine = create_db_engine(database_url)
    try:
        command.downgrade(Config("alembic.ini"), "base")
        command.upgrade(Config("alembic.ini"), "head")
        yield engine, create_session_factory(engine)
    except Exception:
        pytest.fail(
            "Dedicated test PostgreSQL migration or persistence setup failed",
            pytrace=False,
        )
    finally:
        engine.dispose()
        environment.undo()


@pytest.fixture
def db_session(
    postgres_runtime: tuple[Engine, sessionmaker[Session]],
) -> Iterator[Session]:
    _, session_factory = postgres_runtime
    with session_factory() as session:
        session.execute(delete(JobPosting))
        session.execute(delete(Company))
        session.commit()
        yield session
        session.rollback()
        session.execute(delete(JobPosting))
        session.execute(delete(Company))
        session.commit()


def test_migration_creates_companies_and_job_postings(
    postgres_runtime: tuple[Engine, sessionmaker[Session]],
) -> None:
    engine, _ = postgres_runtime

    table_names = set(inspect(engine).get_table_names())

    assert {"companies", "job_postings"}.issubset(table_names)


def test_company_round_trip(db_session: Session) -> None:
    company = create_company(
        db_session,
        name="Example Labs",
        normalized_name="example labs",
        source="test-source",
        domain="example.test",
        website="https://example.test",
        description="A test company",
        stage="seed",
        location="Vancouver",
        source_external_id="company-1",
        source_metadata={"origin": "fixture"},
    )
    company_id = company.id
    db_session.commit()
    db_session.expunge_all()

    loaded = get_company(db_session, company_id)

    assert loaded is not None
    assert loaded.name == "Example Labs"
    assert loaded.source_metadata == {"origin": "fixture"}
    assert loaded.created_at.tzinfo is not None
    assert loaded.updated_at.tzinfo is not None


def test_job_posting_round_trip(db_session: Session) -> None:
    company = create_company(
        db_session,
        name="Job Company",
        normalized_name="job company",
        source="test-source",
    )
    seen_at = datetime.now(timezone.utc)
    job = create_job_posting(
        db_session,
        company_id=company.id,
        external_id="job-1",
        title="Founding Engineer",
        source="test-source",
        function="Engineering",
        location="Remote",
        url="https://example.test/jobs/1",
        active=True,
        raw_metadata={"level": "senior"},
        seen_at=seen_at,
    )
    job_id = job.id
    db_session.commit()
    db_session.expunge_all()

    loaded = get_job_posting(db_session, job_id)

    assert loaded is not None
    assert loaded.title == "Founding Engineer"
    assert loaded.raw_metadata == {"level": "senior"}
    assert loaded.seen_at.tzinfo is not None


def test_repeated_job_upsert_updates_one_row(db_session: Session) -> None:
    company = create_company(
        db_session,
        name="Upsert Jobs",
        normalized_name="upsert jobs",
        source="test-source",
    )
    first = upsert_job_posting(
        db_session,
        company_id=company.id,
        external_id="stable-job",
        title="Engineer",
        source="test-source",
        active=True,
        seen_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    first_id = first.id
    second = upsert_job_posting(
        db_session,
        company_id=company.id,
        external_id="stable-job",
        title="Senior Engineer",
        source="test-source",
        active=False,
        location="Vancouver",
        seen_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        raw_metadata={"updated": True},
    )
    db_session.commit()

    count = db_session.scalar(select(func.count()).select_from(JobPosting))

    assert second.id == first_id
    assert count == 1
    assert second.title == "Senior Engineer"
    assert second.active is False
    assert second.location == "Vancouver"
    assert second.raw_metadata == {"updated": True}


def test_same_source_company_external_id_upsert_is_stable(
    db_session: Session,
) -> None:
    first = upsert_company(
        db_session,
        name="Original Company",
        normalized_name="original company",
        source="test-source",
        source_external_id="stable-company",
    )
    first_id = first.id
    second = upsert_company(
        db_session,
        name="Renamed Company",
        normalized_name="renamed company",
        source="test-source",
        domain="renamed.test",
        source_external_id="stable-company",
        source_metadata={"updated": True},
    )
    db_session.commit()

    count = db_session.scalar(select(func.count()).select_from(Company))

    assert second.id == first_id
    assert count == 1
    assert second.name == "Renamed Company"
    assert second.domain == "renamed.test"


def test_company_without_external_id_is_not_identity_merged(
    db_session: Session,
) -> None:
    first = upsert_company(
        db_session,
        name="No External ID",
        normalized_name="no external id",
        source="test-source",
        domain="same.test",
    )
    second = upsert_company(
        db_session,
        name="No External ID",
        normalized_name="no external id",
        source="test-source",
        domain="same.test",
    )
    db_session.commit()

    assert first.id != second.id
    assert db_session.scalar(select(func.count()).select_from(Company)) == 2
