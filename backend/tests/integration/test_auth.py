from __future__ import annotations

from fastapi.testclient import TestClient


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/me")

    assert response.status_code == 401
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "UNAUTHORIZED"


def test_me_returns_user_for_valid_dev_token(client: TestClient) -> None:
    response = client.get(
        "/me",
        headers={"Authorization": "Bearer local-dev-token"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["user"]["id"] == "00000000-0000-0000-0000-000000000001"
    assert payload["data"]["user"]["email"] == "dev@scoutreach.local"
