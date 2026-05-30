from __future__ import annotations

from pathlib import Path


MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def _read(name: str) -> str:
    return (MIGRATIONS_DIR / name).read_text(encoding="utf-8").lower()


def test_core_migration_files_exist() -> None:
    assert (MIGRATIONS_DIR / "0001_core_tables_up.sql").exists()
    assert (MIGRATIONS_DIR / "0001_core_tables_down.sql").exists()
    assert (MIGRATIONS_DIR / "0002_outreach_regeneration_events_up.sql").exists()
    assert (MIGRATIONS_DIR / "0002_outreach_regeneration_events_down.sql").exists()


def test_up_migration_creates_core_tables_and_constraints() -> None:
    up_sql = _read("0001_core_tables_up.sql")

    for table in ["users", "candidate_profile", "runs", "companies", "outreach"]:
        assert f"create table if not exists {table}" in up_sql

    assert "email text not null unique" in up_sql
    assert "candidate_profile (" in up_sql
    assert "user_id uuid primary key references users(id) on delete cascade" in up_sql
    assert "run_id uuid not null references runs(id) on delete cascade" in up_sql
    assert "company_id uuid not null references companies(id) on delete cascade" in up_sql
    assert "check (progress >= 0 and progress <= 100)" in up_sql


def test_down_migration_drops_core_tables() -> None:
    down_sql = _read("0001_core_tables_down.sql")

    for table in ["outreach", "companies", "runs", "candidate_profile", "users"]:
        assert f"drop table if exists {table}" in down_sql


def test_regeneration_event_migration_creates_and_drops_table() -> None:
    up_sql = _read("0002_outreach_regeneration_events_up.sql")
    down_sql = _read("0002_outreach_regeneration_events_down.sql")

    assert "create table if not exists outreach_regeneration_events" in up_sql
    assert "user_id uuid not null references users(id) on delete cascade" in up_sql
    assert "run_id uuid not null references runs(id) on delete cascade" in up_sql
    assert "outreach_id uuid not null references outreach(id) on delete cascade" in up_sql
    assert "drop table if exists outreach_regeneration_events" in down_sql
