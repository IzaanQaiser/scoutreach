from __future__ import annotations

from fastapi.testclient import TestClient


def test_healthcheck_returns_success(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"
