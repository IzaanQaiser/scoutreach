from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.api.config import Settings


class DatabaseConfigurationError(RuntimeError):
    pass


def _database_url(explicit_url: str | None) -> str:
    database_url = explicit_url or Settings().database_url
    if not database_url:
        raise DatabaseConfigurationError("DATABASE_URL is required for database operations.")
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql+psycopg://"):
        return database_url
    raise DatabaseConfigurationError(
        "DATABASE_URL must use PostgreSQL with the psycopg driver."
    )


def create_db_engine(database_url: str | None = None) -> Engine:
    try:
        return create_engine(_database_url(database_url))
    except DatabaseConfigurationError:
        raise
    except Exception:
        raise DatabaseConfigurationError(
            "DATABASE_URL is invalid or its database driver is unavailable."
        ) from None


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
