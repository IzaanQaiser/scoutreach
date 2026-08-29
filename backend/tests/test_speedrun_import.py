import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

from backend.db.repositories.job_posting import create_job_posting
from backend.db.session import create_db_engine, create_session_factory
from backend.models.company import Company
from backend.models.job_posting import JobPosting
from backend.sources.speedrun import import_speedrun
from backend.sources.speedrun.exceptions import SpeedrunTimeoutError
from backend.sources.speedrun.types import (
    SpeedrunCompany,
    SpeedrunCompanyDetail,
    SpeedrunCompanyJob,
    SpeedrunCompanyWithJobs,
)


class FakeSpeedrunClient:
    def __init__(
        self,
        company: SpeedrunCompany,
        detail: SpeedrunCompanyDetail | Exception,
    ) -> None:
        self.company = company
        self.detail = detail
        self.requested_limit: int | None = None

    def list_companies(self, limit: int) -> list[SpeedrunCompany]:
        self.requested_limit = limit
        return [self.company]

    def get_company(self, slug: str) -> SpeedrunCompanyDetail:
        assert slug == self.company.slug
        if isinstance(self.detail, Exception):
            raise self.detail
        return self.detail


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
            "Dedicated test PostgreSQL Speedrun import setup failed",
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
            delete(JobPosting).where(
                JobPosting.source.in_(["speedrun", "other-source"])
            )
        )
        session.execute(
            delete(Company).where(
                Company.source.in_(["speedrun", "other-source"])
            )
        )
    yield factory
    with factory.begin() as session:
        session.execute(
            delete(JobPosting).where(
                JobPosting.source.in_(["speedrun", "other-source"])
            )
        )
        session.execute(
            delete(Company).where(
                Company.source.in_(["speedrun", "other-source"])
            )
        )


def make_company(*, open_roles: int = 2) -> SpeedrunCompany:
    return SpeedrunCompany(
        slug="acme-labs",
        name="  Acme   Labs  ",
        url="https://speedrun-talent-network.com/companies/acme-labs",
        tier="speedrun",
        open_roles=open_roles,
        cohort="SR007",
        location="San Francisco",
        industries=["developer-tools", "ai"],
        blurb="Infrastructure for builders.",
        logo="https://cdn.example/acme.png",
    )


def make_job(job_id: str, title: str) -> SpeedrunCompanyJob:
    return SpeedrunCompanyJob(
        id=job_id,
        title=title,
        url=f"https://speedrun-talent-network.com/jobs/{job_id}",
        location="Remote",
        workplace_type="Remote",
        employment_type="FullTime",
        comp_summary="$150k-$200k",
        comp_min=150000,
        comp_max=200000,
        comp_period="year",
        published_at="2026-08-29T00:00:00Z",
    )


def make_detail(
    jobs: list[SpeedrunCompanyJob],
    *,
    open_roles: int | None = None,
) -> SpeedrunCompanyDetail:
    company = make_company(open_roles=len(jobs) if open_roles is None else open_roles)
    return SpeedrunCompanyDetail(
        company=SpeedrunCompanyWithJobs(**company.model_dump(), jobs=jobs),
        source="scoutreach",
    )


def test_import_is_idempotent_and_tracks_live_speedrun_roles(
    session_factory: sessionmaker[Session],
) -> None:
    first_client = FakeSpeedrunClient(
        make_company(),
        make_detail([make_job("job-1", "Engineer"), make_job("job-2", "Designer")]),
    )
    with session_factory.begin() as session:
        import_speedrun(session, first_client, 25)
    assert first_client.requested_limit == 25

    with session_factory.begin() as session:
        company = session.scalar(
            select(Company).where(
                Company.source == "speedrun",
                Company.source_external_id == "acme-labs",
            )
        )
        assert company is not None
        company_id = company.id
        assert company.normalized_name == "acme labs"
        assert company.description == "Infrastructure for builders."
        assert company.domain is None
        assert company.website is None
        assert company.stage is None
        assert company.source_metadata == {
            "url": "https://speedrun-talent-network.com/companies/acme-labs",
            "tier": "speedrun",
            "open_roles": 2,
            "cohort": "SR007",
            "industries": ["developer-tools", "ai"],
            "logo": "https://cdn.example/acme.png",
        }
        jobs = {
            job.external_id: job
            for job in session.scalars(
                select(JobPosting).where(JobPosting.source == "speedrun")
            )
        }
        first_job_id = jobs["job-1"].id
        second_job_id = jobs["job-2"].id
        first_seen_at = jobs["job-1"].seen_at
        assert jobs["job-1"].raw_metadata == {
            "workplace_type": "Remote",
            "employment_type": "FullTime",
            "comp_summary": "$150k-$200k",
            "comp_min": 150000.0,
            "comp_max": 200000.0,
            "comp_period": "year",
            "published_at": "2026-08-29T00:00:00Z",
        }
        create_job_posting(
            session,
            company_id=company_id,
            external_id="job-2",
            title="Other-source role",
            source="other-source",
            active=True,
            seen_at=first_seen_at,
        )

    second_client = FakeSpeedrunClient(
        make_company(open_roles=1),
        make_detail([make_job("job-1", "Senior Engineer")]),
    )
    with session_factory.begin() as session:
        import_speedrun(session, second_client, 25)

    with session_factory() as session:
        company = session.scalar(
            select(Company).where(Company.source == "speedrun")
        )
        assert company is not None
        assert company.id == company_id
        speedrun_jobs = {
            job.external_id: job
            for job in session.scalars(
                select(JobPosting).where(JobPosting.source == "speedrun")
            )
        }
        assert speedrun_jobs["job-1"].id == first_job_id
        assert speedrun_jobs["job-1"].title == "Senior Engineer"
        assert speedrun_jobs["job-1"].seen_at > first_seen_at
        assert speedrun_jobs["job-1"].active is True
        assert speedrun_jobs["job-2"].id == second_job_id
        assert speedrun_jobs["job-2"].active is False
        other_job = session.scalar(
            select(JobPosting).where(JobPosting.source == "other-source")
        )
        assert other_job is not None
        assert other_job.active is True

    third_client = FakeSpeedrunClient(
        make_company(open_roles=2),
        make_detail(
            [make_job("job-1", "Senior Engineer"), make_job("job-2", "Designer")]
        ),
    )
    with session_factory.begin() as session:
        import_speedrun(session, third_client, 25)

    with session_factory() as session:
        reappeared = session.scalar(
            select(JobPosting).where(
                JobPosting.source == "speedrun",
                JobPosting.external_id == "job-2",
            )
        )
        assert reappeared is not None
        assert reappeared.id == second_job_id
        assert reappeared.active is True


def test_failed_detail_fetch_does_not_mark_roles_inactive(
    session_factory: sessionmaker[Session],
) -> None:
    company = make_company(open_roles=1)
    with session_factory.begin() as session:
        import_speedrun(
            session,
            FakeSpeedrunClient(company, make_detail([make_job("job-1", "Engineer")])),
            10,
        )

    with session_factory() as session:
        existing = session.scalar(
            select(JobPosting).where(
                JobPosting.source == "speedrun",
                JobPosting.external_id == "job-1",
            )
        )
        assert existing is not None
        assert existing.active is True

    failing_client = FakeSpeedrunClient(
        company,
        SpeedrunTimeoutError("Speedrun request timed out"),
    )
    with session_factory.begin() as session:
        with pytest.raises(SpeedrunTimeoutError):
            import_speedrun(session, failing_client, 10)

    with session_factory() as session:
        unchanged = session.scalar(
            select(JobPosting).where(
                JobPosting.source == "speedrun",
                JobPosting.external_id == "job-1",
            )
        )
        assert unchanged is not None
        assert unchanged.active is True
