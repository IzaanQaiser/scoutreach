from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.statuses import RUN_STATUS_COMPLETED, RUN_STATUS_COMPLETED_WITH_ERRORS, RUN_STATUS_SCRAPING


AUTH_HEADERS = {"Authorization": "Bearer local-dev-token"}


def _create_run(client: TestClient, selected_batches: list[str]) -> dict:
    response = client.post(
        "/runs",
        json={"selected_batches": selected_batches},
        headers=AUTH_HEADERS,
    )
    return {"response": response, "payload": response.json()}


def test_create_run_and_status_polling_flow(client: TestClient) -> None:
    created = _create_run(client, ["W25"])
    assert created["response"].status_code == 200
    assert created["payload"]["success"] is True

    run_id = created["payload"]["data"]["run_id"]
    assert run_id
    assert created["payload"]["data"]["status"] == "running"

    status_response = client.get(f"/runs/{run_id}/status", headers=AUTH_HEADERS)
    assert status_response.status_code == 200

    status_payload = status_response.json()["data"]
    assert status_payload["run_id"] == run_id
    assert status_payload["status"] in {RUN_STATUS_SCRAPING, RUN_STATUS_COMPLETED}
    assert status_payload["companies_scraped"] >= 1


def test_run_creation_rate_limited_after_daily_limit(client: TestClient) -> None:
    for _ in range(3):
        created = _create_run(client, ["W25"])
        assert created["response"].status_code == 200

    blocked = _create_run(client, ["W25"])
    assert blocked["response"].status_code == 429
    assert blocked["payload"]["success"] is False
    assert blocked["payload"]["error"]["code"] == "RATE_LIMITED"


def test_run_status_enforces_ownership(client: TestClient) -> None:
    repository = client.app.state.run_repository
    repository.ensure_user_exists(user_id="00000000-0000-0000-0000-000000000099", email="other@user.local")

    foreign_run = repository.create_run(
        user_id="00000000-0000-0000-0000-000000000099",
        selected_batches=["S24"],
        profile_snapshot={},
        status="running",
        progress=0,
    )

    response = client.get(f"/runs/{foreign_run['id']}/status", headers=AUTH_HEADERS)
    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "NOT_FOUND"


def test_partial_scrape_failure_does_not_fail_run(client: TestClient) -> None:
    created = _create_run(client, ["FAIL_ONE", "W25"])
    assert created["response"].status_code == 200

    run_id = created["payload"]["data"]["run_id"]
    repository = client.app.state.run_repository
    assert repository.count_companies_for_run(run_id=run_id) == 3

    status_response = client.get(f"/runs/{run_id}/status", headers=AUTH_HEADERS)
    assert status_response.status_code == 200
    status_payload = status_response.json()["data"]
    assert status_payload["status"] == RUN_STATUS_COMPLETED_WITH_ERRORS
    assert status_payload["companies_scraped"] == 3

