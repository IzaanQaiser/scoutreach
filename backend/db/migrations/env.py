from alembic import context

from backend.db.migrations.metadata import target_metadata
from backend.db.session import create_db_engine


def run_migrations_offline() -> None:
    engine = create_db_engine()
    context.configure(
        url=engine.url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_db_engine()
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)

            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
