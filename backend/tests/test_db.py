import importlib
import os

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.db.base import Base
from backend.db.migrations.metadata import target_metadata
from backend.db.session import (
    DatabaseConfigurationError,
    create_db_engine,
    create_session_factory,
)


def test_engine_and_session_factory_are_constructed_without_connecting(
    monkeypatch,
) -> None:
    def unexpected_connect(*args, **kwargs):
        raise AssertionError("Database connection attempted during construction")

    monkeypatch.setattr(psycopg, "connect", unexpected_connect)

    engine = create_db_engine("postgresql://user:password@localhost/outreach")
    session_factory = create_session_factory(engine)

    assert engine.url.drivername == "postgresql+psycopg"
    assert session_factory.kw["bind"] is engine


def test_base_and_alembic_metadata_are_empty_and_shared() -> None:
    assert target_metadata is Base.metadata
    assert len(Base.metadata.tables) == 0


def test_database_configuration_errors_do_not_expose_credentials(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(DatabaseConfigurationError, match="DATABASE_URL is required"):
        create_db_engine()

    credential = "raw-password"
    with pytest.raises(DatabaseConfigurationError) as error:
        create_db_engine(
            f"postgresql+missing://user:{credential}@localhost/outreach"
        )
    assert credential not in str(error.value)


def test_non_postgres_database_url_is_rejected() -> None:
    database_url = "sqlite:///tmp/test.db"

    with pytest.raises(DatabaseConfigurationError) as error:
        create_db_engine(database_url)

    assert database_url not in str(error.value)


def test_missing_database_url_does_not_break_app_or_health(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    main_module = importlib.reload(importlib.import_module("backend.api.main"))
    response = TestClient(main_module.app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "outreach-api"}


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_dedicated_postgres_connectivity_and_alembic_smoke(monkeypatch) -> None:
    database_url = os.environ["TEST_DATABASE_URL"]
    monkeypatch.setenv("DATABASE_URL", database_url)

    try:
        engine = create_db_engine(database_url)
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
        command.upgrade(Config("alembic.ini"), "head")
    except Exception:
        pytest.fail(
            "Dedicated test PostgreSQL connectivity/Alembic smoke check failed",
            pytrace=False,
        )
    finally:
        if "engine" in locals():
            engine.dispose()
