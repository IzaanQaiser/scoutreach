from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("SCOUTREACH_ENV", "test")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
    monkeypatch.setenv("ALLOW_DEV_AUTH", "true")
    monkeypatch.setenv("DEV_AUTH_TOKEN", "local-dev-token")
    monkeypatch.setenv("DEV_AUTH_USER_ID", "00000000-0000-0000-0000-000000000001")
    monkeypatch.setenv("DEV_AUTH_EMAIL", "dev@scoutreach.local")

    from app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
