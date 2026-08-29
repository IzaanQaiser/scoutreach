import os
from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db.repositories.company import create_company
from backend.db.repositories.contact import create_contact
from backend.db.repositories.outreach_draft import (
    create_outreach_draft,
    get_outreach_draft,
)
from backend.db.repositories.outreach_send import (
    create_outreach_send,
    get_outreach_send,
)
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
            "Dedicated test PostgreSQL outreach migration or persistence setup failed",
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


def create_test_contact(session: Session, suffix: str):
    company = create_company(
        session,
        name=f"Outreach Company {suffix}",
        normalized_name=f"outreach company {suffix}",
        source="outreach-test",
        source_external_id=f"outreach-company-{suffix}",
    )
    return create_contact(
        session,
        company_id=company.id,
        name=f"Outreach Contact {suffix}",
        source="outreach-test",
    )


def create_test_draft(session: Session, suffix: str):
    contact = create_test_contact(session, suffix)
    return create_outreach_draft(
        session,
        contact_id=contact.id,
        status="READY",
        subject=f"Subject {suffix}",
        body=f"Body {suffix}",
        research_snapshot={"company": suffix},
        profile_fact_ids=[1, 2],
        model_metadata={"model": "test-model"},
    )


def test_migration_to_head_creates_outreach_tables(postgres_engine: Engine) -> None:
    table_names = set(inspect(postgres_engine).get_table_names())

    assert {"outreach_drafts", "outreach_sends"}.issubset(table_names)


def test_outreach_draft_round_trip(db_session: Session) -> None:
    draft = create_test_draft(db_session, "draft-round-trip")
    draft_id = draft.id
    db_session.expunge(draft)

    loaded = get_outreach_draft(db_session, draft_id)

    assert loaded is not None
    assert loaded.status == "READY"
    assert loaded.subject == "Subject draft-round-trip"
    assert loaded.body == "Body draft-round-trip"
    assert loaded.created_at.tzinfo is not None
    assert loaded.updated_at.tzinfo is not None


def test_outreach_send_round_trip(db_session: Session) -> None:
    draft = create_test_draft(db_session, "send-round-trip")
    sent_at = datetime.now(timezone.utc)
    send = create_outreach_send(
        db_session,
        draft_id=draft.id,
        recipient="founder@example.test",
        subject="Exact sent subject",
        body="Exact sent body",
        sent_at=sent_at,
        provider="gmail",
        idempotency_key="send-round-trip-key",
        gmail_message_id="gmail-message-1",
        gmail_thread_id="gmail-thread-1",
        provider_metadata={"attempt": 1},
        research_snapshot={"company": "send-time"},
        profile_fact_ids=[3, 4],
    )
    send_id = send.id
    db_session.expunge(send)

    loaded = get_outreach_send(db_session, send_id)

    assert loaded is not None
    assert loaded.recipient == "founder@example.test"
    assert loaded.subject == "Exact sent subject"
    assert loaded.body == "Exact sent body"
    assert loaded.sent_at == sent_at
    assert loaded.provider == "gmail"
    assert loaded.gmail_message_id == "gmail-message-1"
    assert loaded.gmail_thread_id == "gmail-thread-1"
    assert loaded.provider_metadata == {"attempt": 1}


def test_duplicate_idempotency_key_is_rejected(db_session: Session) -> None:
    draft = create_test_draft(db_session, "duplicate-key")
    send_values = {
        "draft_id": draft.id,
        "recipient": "duplicate@example.test",
        "subject": "Duplicate subject",
        "body": "Duplicate body",
        "sent_at": datetime.now(timezone.utc),
        "provider": "manual-linkedin",
        "idempotency_key": "duplicate-idempotency-key",
    }
    create_outreach_send(db_session, **send_values)

    with pytest.raises(IntegrityError):
        create_outreach_send(db_session, **send_values)


def test_draft_json_snapshots_round_trip_unchanged(db_session: Session) -> None:
    contact = create_test_contact(db_session, "draft-snapshots")
    research_snapshot = {
        "company": {"stage": "seed"},
        "signals": ["hiring", "open-source"],
    }
    profile_fact_ids = [11, 12, 13]
    model_metadata = {"provider": "later", "temperature": 0.2}
    draft = create_outreach_draft(
        db_session,
        contact_id=contact.id,
        status="PENDING",
        research_snapshot=research_snapshot,
        profile_fact_ids=profile_fact_ids,
        model_metadata=model_metadata,
    )
    draft_id = draft.id
    db_session.expunge(draft)

    loaded = get_outreach_draft(db_session, draft_id)

    assert loaded is not None
    assert loaded.research_snapshot == research_snapshot
    assert loaded.profile_fact_ids == profile_fact_ids
    assert loaded.model_metadata == model_metadata


def test_send_snapshots_remain_independent_of_draft_mutation(
    db_session: Session,
) -> None:
    contact = create_test_contact(db_session, "send-snapshots")
    original_research = {"company": {"stage": "series-a"}}
    original_fact_ids = [21, 22]
    draft = create_outreach_draft(
        db_session,
        contact_id=contact.id,
        status="READY",
        subject="Draft subject",
        body="Draft body",
        research_snapshot=original_research,
        profile_fact_ids=original_fact_ids,
    )
    send = create_outreach_send(
        db_session,
        draft_id=draft.id,
        recipient="snapshot@example.test",
        subject="Sent subject",
        body="Sent body",
        sent_at=datetime.now(timezone.utc),
        provider="manual-linkedin",
        idempotency_key="send-snapshot-key",
        research_snapshot=original_research,
        profile_fact_ids=original_fact_ids,
    )
    send_id = send.id

    draft.research_snapshot = {"company": {"stage": "changed"}}
    draft.profile_fact_ids = [99]
    db_session.flush()
    db_session.expunge_all()

    loaded_send = get_outreach_send(db_session, send_id)

    assert loaded_send is not None
    assert loaded_send.research_snapshot == original_research
    assert loaded_send.profile_fact_ids == original_fact_ids


def test_outreach_draft_status_is_constrained(db_session: Session) -> None:
    contact = create_test_contact(db_session, "invalid-status")

    with pytest.raises(IntegrityError):
        create_outreach_draft(
            db_session,
            contact_id=contact.id,
            status="INVALID",
        )
