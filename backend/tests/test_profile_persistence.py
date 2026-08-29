import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db.repositories.profile_artifact import (
    create_profile_artifact,
    get_profile_artifact,
)
from backend.db.repositories.profile_fact import create_profile_fact, get_profile_fact
from backend.db.session import create_db_engine


@pytest.fixture(scope="module")
def postgres_engine() -> Iterator[Engine]:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for persistence tests")

    environment = pytest.MonkeyPatch()
    environment.setenv("DATABASE_URL", database_url)
    engine = create_db_engine(database_url)
    try:
        command.upgrade(Config("alembic.ini"), "head")
        yield engine
    except Exception:
        pytest.fail(
            "Dedicated test PostgreSQL profile migration or persistence setup failed",
            pytrace=False,
        )
    finally:
        engine.dispose()
        environment.undo()


@pytest.fixture
def db_session(postgres_engine: Engine) -> Iterator[Session]:
    with postgres_engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, autoflush=False, expire_on_commit=False) as session:
            yield session
        if transaction.is_active:
            transaction.rollback()


def test_migration_to_head_creates_profile_tables(postgres_engine: Engine) -> None:
    table_names = set(inspect(postgres_engine).get_table_names())

    assert {"profile_artifacts", "profile_facts"}.issubset(table_names)


def test_profile_artifact_round_trip(db_session: Session) -> None:
    artifact = create_profile_artifact(
        db_session,
        type="resume",
        content_text="Built distributed systems.",
        content_hash="resume-hash-round-trip",
        url="https://example.test/resume",
        source_metadata={"filename": "resume.pdf"},
    )
    artifact_id = artifact.id
    db_session.expunge(artifact)

    loaded = get_profile_artifact(db_session, artifact_id)

    assert loaded is not None
    assert loaded.type == "resume"
    assert loaded.content_text == "Built distributed systems."
    assert loaded.source_metadata == {"filename": "resume.pdf"}
    assert loaded.refreshed_at.tzinfo is not None


def test_profile_fact_round_trip_and_evidence_relationship(
    db_session: Session,
) -> None:
    artifact = create_profile_artifact(
        db_session,
        type="github",
        content_text="Maintains an open-source database driver.",
        content_hash="github-hash-fact-round-trip",
    )
    fact = create_profile_fact(
        db_session,
        artifact_id=artifact.id,
        category="experience",
        claim="Maintains open-source infrastructure",
        evidence_text="Maintains an open-source database driver.",
        importance=0.87,
    )
    fact_id = fact.id
    db_session.expunge(fact)

    loaded = get_profile_fact(db_session, fact_id)

    assert loaded is not None
    assert loaded.artifact_id == artifact.id
    assert loaded.evidence_text == "Maintains an open-source database driver."
    assert loaded.importance == pytest.approx(0.87)
    assert loaded.created_at.tzinfo is not None


def test_profile_fact_requires_existing_artifact(db_session: Session) -> None:
    with pytest.raises(IntegrityError):
        create_profile_fact(
            db_session,
            artifact_id=-1,
            category="experience",
            claim="Untraceable claim",
            evidence_text="Untraceable evidence",
        )


def test_profile_fact_requires_evidence_text(db_session: Session) -> None:
    artifact = create_profile_artifact(
        db_session,
        type="manual",
        content_text="Manual profile note.",
        content_hash="manual-hash-required-evidence",
    )

    with pytest.raises(IntegrityError):
        create_profile_fact(
            db_session,
            artifact_id=artifact.id,
            category="note",
            claim="A claim without evidence",
            evidence_text=None,  # type: ignore[arg-type]
        )


def test_duplicate_type_and_content_hash_is_rejected(db_session: Session) -> None:
    artifact_values = {
        "type": "website",
        "content_text": "Identical website snapshot.",
        "content_hash": "duplicate-website-hash",
    }
    create_profile_artifact(db_session, **artifact_values)

    with pytest.raises(IntegrityError):
        create_profile_artifact(db_session, **artifact_values)


def test_same_content_hash_is_allowed_across_artifact_types(
    db_session: Session,
) -> None:
    first = create_profile_artifact(
        db_session,
        type="website",
        content_text="Shared content.",
        content_hash="cross-type-shared-hash",
    )
    second = create_profile_artifact(
        db_session,
        type="manual",
        content_text="Shared content.",
        content_hash="cross-type-shared-hash",
    )

    assert first.id != second.id


def test_profile_artifact_type_is_constrained(db_session: Session) -> None:
    with pytest.raises(IntegrityError):
        create_profile_artifact(
            db_session,
            type="unsupported",
            content_text="Unsupported artifact.",
            content_hash="unsupported-type-hash",
        )
