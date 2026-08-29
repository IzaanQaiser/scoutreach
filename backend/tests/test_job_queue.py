import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, delete, inspect
from sqlalchemy.orm import Session, sessionmaker

from backend.db.repositories.job import (
    JobProgressError,
    JobStateError,
    claim_next,
    enqueue,
    fail,
    get_job,
    set_progress,
    succeed,
)
from backend.db.session import create_db_engine, create_session_factory
from backend.jobs.worker import run_worker_iteration
from backend.models.job import Job


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
            "Dedicated test PostgreSQL job migration or persistence setup failed",
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
        session.execute(delete(Job))
    yield factory
    with factory.begin() as session:
        session.execute(delete(Job))


def test_migration_to_head_creates_jobs_table(
    postgres_runtime: tuple[Engine, sessionmaker[Session]],
) -> None:
    engine, _ = postgres_runtime

    assert "jobs" in inspect(engine).get_table_names()


def test_enqueue_and_get_are_durable(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory.begin() as session:
        job = enqueue(
            session,
            type="fake",
            payload={"company_id": 42},
            progress_total=3,
        )
        job_id = job.id

    with session_factory() as new_session:
        loaded = get_job(new_session, job_id)

        assert loaded is not None
        assert loaded.type == "fake"
        assert loaded.payload == {"company_id": 42}
        assert loaded.status == "PENDING"
        assert loaded.progress_current == 0
        assert loaded.progress_total == 3
        assert loaded.created_at.tzinfo is not None


def test_oldest_pending_job_is_claimed_once(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory.begin() as session:
        oldest = enqueue(session, type="oldest")
        newer = enqueue(session, type="newer")
        oldest_id = oldest.id
        newer_id = newer.id

    with session_factory.begin() as session:
        first_claim = claim_next(session)
        assert first_claim is not None
        assert first_claim.id == oldest_id
        assert first_claim.status == "RUNNING"
        assert first_claim.started_at is not None

    with session_factory.begin() as session:
        second_claim = claim_next(session)
        assert second_claim is not None
        assert second_claim.id == newer_id
        succeed(session, second_claim.id)

    with session_factory.begin() as session:
        assert claim_next(session) is None


def test_progress_requires_running_and_respects_total(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory.begin() as session:
        job = enqueue(session, type="progress", progress_total=5)
        job_id = job.id

    with session_factory.begin() as session:
        with pytest.raises(JobStateError):
            set_progress(session, job_id, 1)

    with session_factory.begin() as session:
        claim_next(session)
        updated = set_progress(session, job_id, 3)
        assert updated.progress_current == 3
        with pytest.raises(JobProgressError):
            set_progress(session, job_id, 6)


def test_succeed_finishes_job_and_completes_progress(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory.begin() as session:
        job_id = enqueue(session, type="success", progress_total=4).id

    with session_factory.begin() as session:
        running = claim_next(session)
        assert running is not None
        running.error = "previous error"
        session.flush()
        completed = succeed(session, job_id)

        assert completed.status == "SUCCEEDED"
        assert completed.error is None
        assert completed.progress_current == 4
        assert completed.finished_at is not None

    with session_factory.begin() as session:
        assert claim_next(session) is None


def test_fail_persists_error_and_finishes_job(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory.begin() as session:
        job_id = enqueue(session, type="failure").id

    with session_factory.begin() as session:
        claim_next(session)
        failed = fail(session, job_id, "handler failed")

        assert failed.status == "FAILED"
        assert failed.error == "handler failed"
        assert failed.finished_at is not None

    with session_factory() as new_session:
        persisted = get_job(new_session, job_id)
        assert persisted is not None
        assert persisted.status == "FAILED"
        assert persisted.error == "handler failed"


def test_one_worker_iteration_with_fake_handler_succeeds(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory.begin() as session:
        job_id = enqueue(session, type="fake-handler", payload={"value": 7}).id

    handled: list[tuple[int, dict[str, object]]] = []

    def fake_handler(claimed_job_id: int, payload: dict[str, object]) -> None:
        handled.append((claimed_job_id, payload))

    assert run_worker_iteration(
        session_factory,
        handlers={"fake-handler": fake_handler},
    )

    with session_factory() as session:
        completed = get_job(session, job_id)
        assert completed is not None
        assert completed.status == "SUCCEEDED"
    assert handled == [(job_id, {"value": 7})]


def test_unknown_handler_fails_job_explicitly(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory.begin() as session:
        job_id = enqueue(session, type="unknown-handler").id

    assert run_worker_iteration(session_factory, handlers={})

    with session_factory() as session:
        failed = get_job(session, job_id)
        assert failed is not None
        assert failed.status == "FAILED"
        assert failed.error == "Unknown job type: unknown-handler"
