"""Persistence layer for run and company Phase 2-4 workflows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from supabase import Client

from app.models.statuses import RUN_ACTIVE_STATUSES


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class RunRepository(ABC):
    @abstractmethod
    def ensure_user_exists(self, *, user_id: str, email: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_profile_snapshot(self, *, user_id: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def count_runs_created_today(self, *, user_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def has_active_run(self, *, user_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create_run(
        self,
        *,
        user_id: str,
        selected_batches: list[str],
        profile_snapshot: dict,
        status: str,
        progress: int,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_run_for_user(self, *, run_id: str, user_id: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def get_run(self, *, run_id: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def update_run(self, *, run_id: str, fields: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def insert_company(self, *, payload: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def count_companies_for_run(self, *, run_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def count_companies_for_run_by_status(self, *, run_id: str, status: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_companies_for_run(self, *, run_id: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_companies_for_run(
        self,
        *,
        run_id: str,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_company(self, *, company_id: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def update_company(self, *, company_id: str, fields: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def insert_outreach(self, *, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def count_outreach_created_today(self, *, user_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def count_outreach_for_run_by_status(self, *, run_id: str, status: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def count_outreach_sent_today(self, *, user_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def insert_outreach_regeneration_event(self, *, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def count_outreach_regenerations_today(self, *, user_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_outreach_for_run(self, *, run_id: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_outreach_for_run(
        self,
        *,
        run_id: str,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_outreach(self, *, outreach_id: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def get_outreach_for_user(self, *, outreach_id: str, user_id: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def update_outreach(self, *, outreach_id: str, fields: dict) -> None:
        raise NotImplementedError


class InMemoryRunRepository(RunRepository):
    def __init__(self) -> None:
        self._lock = Lock()
        self._users: dict[str, dict] = {}
        self._candidate_profiles: dict[str, dict] = {}
        self._runs: dict[str, dict] = {}
        self._companies: list[dict] = []
        self._outreach: list[dict] = []
        self._outreach_regeneration_events: list[dict] = []

    def ensure_user_exists(self, *, user_id: str, email: str) -> None:
        with self._lock:
            self._users[user_id] = {
                "id": user_id,
                "email": email,
                "message_preferences": self._users.get(user_id, {}).get("message_preferences", {}),
            }

    def get_profile_snapshot(self, *, user_id: str) -> dict:
        with self._lock:
            candidate_profile = self._candidate_profiles.get(user_id, {})
            user = self._users.get(user_id, {})

        snapshot = dict(candidate_profile) if candidate_profile else {}
        if user.get("message_preferences"):
            snapshot["message_preferences"] = user["message_preferences"]
        return snapshot

    def count_runs_created_today(self, *, user_id: str) -> int:
        today = datetime.now(UTC).date()
        with self._lock:
            runs = [row for row in self._runs.values() if row["user_id"] == user_id]
        return sum(datetime.fromisoformat(row["created_at"]).date() == today for row in runs)

    def has_active_run(self, *, user_id: str) -> bool:
        with self._lock:
            return any(
                row["user_id"] == user_id and row["status"] in RUN_ACTIVE_STATUSES
                for row in self._runs.values()
            )

    def create_run(
        self,
        *,
        user_id: str,
        selected_batches: list[str],
        profile_snapshot: dict,
        status: str,
        progress: int,
    ) -> dict:
        with self._lock:
            run_id = str(uuid4())
            now_iso = _utc_now_iso()
            row = {
                "id": run_id,
                "user_id": user_id,
                "selected_batches": selected_batches,
                "status": status,
                "progress": progress,
                "profile_snapshot": profile_snapshot,
                "error_message": None,
                "started_at": now_iso,
                "completed_at": None,
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            self._runs[run_id] = row
            return dict(row)

    def get_run_for_user(self, *, run_id: str, user_id: str) -> dict | None:
        with self._lock:
            run = self._runs.get(run_id)
            if run is None or run["user_id"] != user_id:
                return None
            return dict(run)

    def get_run(self, *, run_id: str) -> dict | None:
        with self._lock:
            run = self._runs.get(run_id)
            return dict(run) if run else None

    def update_run(self, *, run_id: str, fields: dict) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                return
            run.update(fields)
            run["updated_at"] = _utc_now_iso()

    def insert_company(self, *, payload: dict) -> None:
        with self._lock:
            row = dict(payload)
            row["id"] = str(uuid4())
            row["created_at"] = _utc_now_iso()
            row["updated_at"] = row["created_at"]
            self._companies.append(row)

    def count_companies_for_run(self, *, run_id: str) -> int:
        with self._lock:
            return sum(company["run_id"] == run_id for company in self._companies)

    def count_companies_for_run_by_status(self, *, run_id: str, status: str) -> int:
        with self._lock:
            return sum(
                company["run_id"] == run_id and company.get("status") == status
                for company in self._companies
            )

    def get_companies_for_run(self, *, run_id: str) -> list[dict]:
        with self._lock:
            return [dict(company) for company in self._companies if company["run_id"] == run_id]

    def list_companies_for_run(
        self,
        *,
        run_id: str,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        with self._lock:
            rows = [dict(company) for company in self._companies if company["run_id"] == run_id]

        if status is not None:
            rows = [row for row in rows if row.get("status") == status]

        rows.sort(key=lambda row: str(row.get("created_at", "")))
        return rows[offset : offset + limit]

    def get_company(self, *, company_id: str) -> dict | None:
        with self._lock:
            for company in self._companies:
                if company["id"] == company_id:
                    return dict(company)
        return None

    def update_company(self, *, company_id: str, fields: dict) -> None:
        with self._lock:
            for company in self._companies:
                if company["id"] == company_id:
                    company.update(fields)
                    company["updated_at"] = _utc_now_iso()
                    return

    def insert_outreach(self, *, payload: dict) -> dict:
        with self._lock:
            row = dict(payload)
            row["id"] = str(uuid4())
            row["created_at"] = _utc_now_iso()
            row["updated_at"] = row["created_at"]
            self._outreach.append(row)
            return dict(row)

    def count_outreach_created_today(self, *, user_id: str) -> int:
        today = datetime.now(UTC).date()
        with self._lock:
            rows = [row for row in self._outreach if row["user_id"] == user_id]
        return sum(datetime.fromisoformat(row["created_at"]).date() == today for row in rows)

    def count_outreach_for_run_by_status(self, *, run_id: str, status: str) -> int:
        with self._lock:
            return sum(
                row["run_id"] == run_id and row.get("status") == status
                for row in self._outreach
            )

    def count_outreach_sent_today(self, *, user_id: str) -> int:
        today = datetime.now(UTC).date()
        with self._lock:
            rows = [row for row in self._outreach if row["user_id"] == user_id and row.get("status") == "sent"]
        return sum(
            row.get("sent_at") is not None and datetime.fromisoformat(str(row["sent_at"])).date() == today
            for row in rows
        )

    def insert_outreach_regeneration_event(self, *, payload: dict) -> dict:
        with self._lock:
            row = dict(payload)
            row["id"] = str(uuid4())
            row["created_at"] = _utc_now_iso()
            self._outreach_regeneration_events.append(row)
            return dict(row)

    def count_outreach_regenerations_today(self, *, user_id: str) -> int:
        today = datetime.now(UTC).date()
        with self._lock:
            rows = [row for row in self._outreach_regeneration_events if row["user_id"] == user_id]
        return sum(datetime.fromisoformat(row["created_at"]).date() == today for row in rows)

    def get_outreach_for_run(self, *, run_id: str) -> list[dict]:
        with self._lock:
            return [dict(row) for row in self._outreach if row["run_id"] == run_id]

    def list_outreach_for_run(
        self,
        *,
        run_id: str,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        with self._lock:
            rows = [dict(row) for row in self._outreach if row["run_id"] == run_id]

        if status is not None:
            rows = [row for row in rows if row.get("status") == status]

        rows.sort(key=lambda row: str(row.get("created_at", "")))
        return rows[offset : offset + limit]

    def get_outreach(self, *, outreach_id: str) -> dict | None:
        with self._lock:
            for row in self._outreach:
                if row["id"] == outreach_id:
                    return dict(row)
        return None

    def get_outreach_for_user(self, *, outreach_id: str, user_id: str) -> dict | None:
        with self._lock:
            for row in self._outreach:
                if row["id"] == outreach_id and row["user_id"] == user_id:
                    return dict(row)
        return None

    def update_outreach(self, *, outreach_id: str, fields: dict) -> None:
        with self._lock:
            for row in self._outreach:
                if row["id"] == outreach_id:
                    row.update(fields)
                    row["updated_at"] = _utc_now_iso()
                    return


def _rows(response: object) -> list[dict]:
    if hasattr(response, "data"):
        data = getattr(response, "data")
        if isinstance(data, list):
            return data
        if data is None:
            return []
        if isinstance(data, dict):
            return [data]

    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]

    return []


class SupabaseRunRepository(RunRepository):
    def __init__(self, client: Client) -> None:
        self._client = client

    def ensure_user_exists(self, *, user_id: str, email: str) -> None:
        payload = {"id": user_id, "email": email}
        self._client.table("users").upsert(payload, on_conflict="id").execute()

    def get_profile_snapshot(self, *, user_id: str) -> dict:
        profile_rows = _rows(
            self._client.table("candidate_profile").select("*").eq("user_id", user_id).limit(1).execute()
        )
        user_rows = _rows(self._client.table("users").select("message_preferences").eq("id", user_id).limit(1).execute())

        snapshot = dict(profile_rows[0]) if profile_rows else {}
        if user_rows and user_rows[0].get("message_preferences") is not None:
            snapshot["message_preferences"] = user_rows[0].get("message_preferences")
        return snapshot

    def count_runs_created_today(self, *, user_id: str) -> int:
        day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        rows = _rows(
            self._client.table("runs").select("id").eq("user_id", user_id).gte("created_at", day_start).execute()
        )
        return len(rows)

    def has_active_run(self, *, user_id: str) -> bool:
        rows = _rows(self._client.table("runs").select("status").eq("user_id", user_id).execute())
        return any(row.get("status") in RUN_ACTIVE_STATUSES for row in rows)

    def create_run(
        self,
        *,
        user_id: str,
        selected_batches: list[str],
        profile_snapshot: dict,
        status: str,
        progress: int,
    ) -> dict:
        run_id = str(uuid4())
        payload = {
            "id": run_id,
            "user_id": user_id,
            "selected_batches": selected_batches,
            "status": status,
            "progress": progress,
            "profile_snapshot": profile_snapshot,
            "started_at": _utc_now_iso(),
        }
        rows = _rows(self._client.table("runs").insert(payload).execute())
        if rows:
            return dict(rows[0])

        payload["created_at"] = payload["started_at"]
        payload["updated_at"] = payload["started_at"]
        payload["completed_at"] = None
        payload["error_message"] = None
        return payload

    def get_run_for_user(self, *, run_id: str, user_id: str) -> dict | None:
        rows = _rows(
            self._client.table("runs").select("*").eq("id", run_id).eq("user_id", user_id).limit(1).execute()
        )
        return dict(rows[0]) if rows else None

    def get_run(self, *, run_id: str) -> dict | None:
        rows = _rows(self._client.table("runs").select("*").eq("id", run_id).limit(1).execute())
        return dict(rows[0]) if rows else None

    def update_run(self, *, run_id: str, fields: dict) -> None:
        self._client.table("runs").update(fields).eq("id", run_id).execute()

    def insert_company(self, *, payload: dict) -> None:
        self._client.table("companies").insert(payload).execute()

    def count_companies_for_run(self, *, run_id: str) -> int:
        rows = _rows(self._client.table("companies").select("id").eq("run_id", run_id).execute())
        return len(rows)

    def count_companies_for_run_by_status(self, *, run_id: str, status: str) -> int:
        rows = _rows(
            self._client.table("companies").select("id").eq("run_id", run_id).eq("status", status).execute()
        )
        return len(rows)

    def get_companies_for_run(self, *, run_id: str) -> list[dict]:
        rows = _rows(self._client.table("companies").select("*").eq("run_id", run_id).execute())
        return [dict(row) for row in rows]

    def list_companies_for_run(
        self,
        *,
        run_id: str,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        query = self._client.table("companies").select("*").eq("run_id", run_id).order("created_at")
        if status is not None:
            query = query.eq("status", status)
        if limit > 0:
            query = query.range(offset, offset + limit - 1)
        rows = _rows(query.execute())
        return [dict(row) for row in rows]

    def get_company(self, *, company_id: str) -> dict | None:
        rows = _rows(self._client.table("companies").select("*").eq("id", company_id).limit(1).execute())
        return dict(rows[0]) if rows else None

    def update_company(self, *, company_id: str, fields: dict) -> None:
        self._client.table("companies").update(fields).eq("id", company_id).execute()

    def insert_outreach(self, *, payload: dict) -> dict:
        rows = _rows(self._client.table("outreach").insert(payload).execute())
        if rows:
            return dict(rows[0])

        now_iso = _utc_now_iso()
        return {
            **payload,
            "id": str(uuid4()),
            "created_at": now_iso,
            "updated_at": now_iso,
        }

    def count_outreach_created_today(self, *, user_id: str) -> int:
        day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        rows = _rows(
            self._client.table("outreach").select("id").eq("user_id", user_id).gte("created_at", day_start).execute()
        )
        return len(rows)

    def count_outreach_for_run_by_status(self, *, run_id: str, status: str) -> int:
        rows = _rows(
            self._client.table("outreach").select("id").eq("run_id", run_id).eq("status", status).execute()
        )
        return len(rows)

    def count_outreach_sent_today(self, *, user_id: str) -> int:
        day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        rows = _rows(
            self._client.table("outreach")
            .select("id")
            .eq("user_id", user_id)
            .eq("status", "sent")
            .gte("sent_at", day_start)
            .execute()
        )
        return len(rows)

    def insert_outreach_regeneration_event(self, *, payload: dict) -> dict:
        rows = _rows(self._client.table("outreach_regeneration_events").insert(payload).execute())
        if rows:
            return dict(rows[0])

        return {
            **payload,
            "id": str(uuid4()),
            "created_at": _utc_now_iso(),
        }

    def count_outreach_regenerations_today(self, *, user_id: str) -> int:
        day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        rows = _rows(
            self._client.table("outreach_regeneration_events")
            .select("id")
            .eq("user_id", user_id)
            .gte("created_at", day_start)
            .execute()
        )
        return len(rows)

    def get_outreach_for_run(self, *, run_id: str) -> list[dict]:
        rows = _rows(self._client.table("outreach").select("*").eq("run_id", run_id).execute())
        return [dict(row) for row in rows]

    def list_outreach_for_run(
        self,
        *,
        run_id: str,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        query = self._client.table("outreach").select("*").eq("run_id", run_id).order("created_at")
        if status is not None:
            query = query.eq("status", status)
        if limit > 0:
            query = query.range(offset, offset + limit - 1)
        rows = _rows(query.execute())
        return [dict(row) for row in rows]

    def get_outreach(self, *, outreach_id: str) -> dict | None:
        rows = _rows(self._client.table("outreach").select("*").eq("id", outreach_id).limit(1).execute())
        return dict(rows[0]) if rows else None

    def get_outreach_for_user(self, *, outreach_id: str, user_id: str) -> dict | None:
        rows = _rows(
            self._client.table("outreach").select("*").eq("id", outreach_id).eq("user_id", user_id).limit(1).execute()
        )
        return dict(rows[0]) if rows else None

    def update_outreach(self, *, outreach_id: str, fields: dict) -> None:
        self._client.table("outreach").update(fields).eq("id", outreach_id).execute()
