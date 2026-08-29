import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db.repositories.company import create_company
from backend.db.repositories.contact import create_contact, get_contact
from backend.db.repositories.contact_method import (
    create_contact_method,
    get_contact_method,
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
            "Dedicated test PostgreSQL contact migration or persistence setup failed",
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


def create_test_company(session: Session, suffix: str):
    return create_company(
        session,
        name=f"Contact Company {suffix}",
        normalized_name=f"contact company {suffix}",
        source="contact-test",
        source_external_id=f"contact-company-{suffix}",
    )


def test_migration_to_head_creates_contact_tables(postgres_engine: Engine) -> None:
    table_names = set(inspect(postgres_engine).get_table_names())

    assert {"contacts", "contact_methods"}.issubset(table_names)


def test_contact_round_trip(db_session: Session) -> None:
    company = create_test_company(db_session, "round-trip")
    contact = create_contact(
        db_session,
        company_id=company.id,
        name="Ada Founder",
        source="manual",
        title="Founder",
        role_category="executive",
        linkedin_url="https://linkedin.example/ada",
        source_confidence=0.91,
    )
    contact_id = contact.id
    db_session.expunge(contact)

    loaded = get_contact(db_session, contact_id)

    assert loaded is not None
    assert loaded.company_id == company.id
    assert loaded.name == "Ada Founder"
    assert loaded.role_category == "executive"
    assert loaded.source_confidence == pytest.approx(0.91)
    assert loaded.created_at.tzinfo is not None
    assert loaded.updated_at.tzinfo is not None


def test_contact_method_round_trip(db_session: Session) -> None:
    company = create_test_company(db_session, "method-round-trip")
    contact = create_contact(
        db_session,
        company_id=company.id,
        name="Lin Contact",
        source="manual",
    )
    method = create_contact_method(
        db_session,
        contact_id=contact.id,
        type="email",
        value="lin@example.test",
        source="manual",
        verification_status="verified",
        confidence=0.98,
        is_primary=True,
    )
    method_id = method.id
    db_session.expunge(method)

    loaded = get_contact_method(db_session, method_id)

    assert loaded is not None
    assert loaded.contact_id == contact.id
    assert loaded.type == "email"
    assert loaded.value == "lin@example.test"
    assert loaded.verification_status == "verified"
    assert loaded.confidence == pytest.approx(0.98)
    assert loaded.is_primary is True
    assert loaded.created_at.tzinfo is not None


def test_duplicate_contact_method_identity_is_rejected(db_session: Session) -> None:
    company = create_test_company(db_session, "duplicate")
    contact = create_contact(
        db_session,
        company_id=company.id,
        name="Duplicate Contact",
        source="manual",
    )
    method_values = {
        "contact_id": contact.id,
        "type": "email",
        "value": "duplicate@example.test",
        "source": "manual",
    }
    create_contact_method(db_session, **method_values)

    with pytest.raises(IntegrityError):
        create_contact_method(db_session, **method_values)


def test_same_method_value_is_allowed_for_different_contacts(
    db_session: Session,
) -> None:
    company = create_test_company(db_session, "shared-value")
    first_contact = create_contact(
        db_session,
        company_id=company.id,
        name="First Contact",
        source="manual",
    )
    second_contact = create_contact(
        db_session,
        company_id=company.id,
        name="Second Contact",
        source="manual",
    )

    first_method = create_contact_method(
        db_session,
        contact_id=first_contact.id,
        type="linkedin",
        value="https://linkedin.example/shared",
        source="manual",
    )
    second_method = create_contact_method(
        db_session,
        contact_id=second_contact.id,
        type="linkedin",
        value="https://linkedin.example/shared",
        source="manual",
    )

    assert first_method.id != second_method.id


def test_contact_requires_existing_company(db_session: Session) -> None:
    with pytest.raises(IntegrityError):
        create_contact(
            db_session,
            company_id=-1,
            name="Orphan Contact",
            source="manual",
        )
