import importlib

from fastapi.testclient import TestClient

from backend.api.config import Settings
from backend.api.main import app


ENV_NAMES = (
    "DATABASE_URL",
    "LLM_PROVIDER",
    "LLM_MODEL",
    "HUNTER_API_KEY",
    "GMAIL_CLIENT_ID",
    "GMAIL_CLIENT_SECRET",
    "APP_BASE_URL",
)


def test_health_contract() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "outreach-api"}


def test_explicit_env_parsing(monkeypatch) -> None:
    values = {
        "DATABASE_URL": "postgresql://localhost/outreach",
        "LLM_PROVIDER": "configured-later",
        "LLM_MODEL": "configured-later",
        "HUNTER_API_KEY": "hunter-secret",
        "GMAIL_CLIENT_ID": "gmail-client-id",
        "GMAIL_CLIENT_SECRET": "gmail-client-secret",
        "APP_BASE_URL": "http://localhost:5173",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    parsed = Settings()

    assert parsed.database_url == values["DATABASE_URL"]
    assert parsed.llm_provider == values["LLM_PROVIDER"]
    assert parsed.llm_model == values["LLM_MODEL"]
    assert parsed.hunter_api_key is not None
    assert parsed.hunter_api_key.get_secret_value() == values["HUNTER_API_KEY"]
    assert parsed.gmail_client_id == values["GMAIL_CLIENT_ID"]
    assert parsed.gmail_client_secret is not None
    assert parsed.gmail_client_secret.get_secret_value() == values["GMAIL_CLIENT_SECRET"]
    assert str(parsed.app_base_url) == "http://localhost:5173/"


def test_missing_integration_config_does_not_break_app(monkeypatch) -> None:
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)

    config_module = importlib.reload(importlib.import_module("backend.api.config"))
    main_module = importlib.reload(importlib.import_module("backend.api.main"))

    assert all(
        getattr(config_module.settings, field_name) is None
        for field_name in config_module.Settings.model_fields
    )
    response = TestClient(main_module.app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "outreach-api"}
