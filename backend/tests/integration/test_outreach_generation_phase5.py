from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.statuses import (
    OUTREACH_STATUS_DRAFT,
    OUTREACH_STATUS_GENERATION_FAILED,
    RUN_STATUS_COMPLETED,
    RUN_STATUS_COMPLETED_WITH_ERRORS,
    RUN_STATUS_FAILED,
    RUN_STATUS_MESSAGES_GENERATED,
)


AUTH_HEADERS = {"Authorization": "Bearer local-dev-token"}
TERMINAL_SCRAPE_STATUSES = {
    RUN_STATUS_COMPLETED,
    RUN_STATUS_COMPLETED_WITH_ERRORS,
    RUN_STATUS_FAILED,
}


def _create_run(client: TestClient, selected_batches: list[str]) -> str:
    response = client.post(
        "/runs",
        json={"selected_batches": selected_batches},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    return response.json()["data"]["run_id"]


def _wait_for_scrape_completion(client: TestClient, run_id: str) -> None:
    for _ in range(20):
        response = client.get(f"/runs/{run_id}/status", headers=AUTH_HEADERS)
        assert response.status_code == 200
        status = response.json()["data"]["status"]
        if status in TERMINAL_SCRAPE_STATUSES:
            return
    raise AssertionError("Run did not finish scrape pipeline.")


def _set_company_status(client: TestClient, company_id: str, status: str) -> None:
    response = client.patch(
        f"/companies/{company_id}",
        json={"status": status},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200


def test_generate_messages_uses_accepted_companies_only(client: TestClient) -> None:
    run_id = _create_run(client, ["W25", "S24"])
    _wait_for_scrape_completion(client, run_id)

    queue_response = client.get(f"/runs/{run_id}/companies?status=pending_review", headers=AUTH_HEADERS)
    assert queue_response.status_code == 200
    queue = queue_response.json()["data"]["companies"]
    assert len(queue) == 2

    _set_company_status(client, queue[0]["id"], "accepted")
    _set_company_status(client, queue[1]["id"], "rejected")

    generate_response = client.post(
        f"/runs/{run_id}/generate-messages",
        json={"founder_selection_strategy": "first_verified_email", "max_messages": 25},
        headers=AUTH_HEADERS,
    )
    assert generate_response.status_code == 200

    payload = generate_response.json()["data"]
    assert payload["status"] == RUN_STATUS_MESSAGES_GENERATED
    assert payload["generated_count"] == 1
    assert payload["generation_failed_count"] == 0

    outreach_rows = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)
    assert len(outreach_rows) == 1
    assert outreach_rows[0]["status"] == OUTREACH_STATUS_DRAFT
    assert outreach_rows[0]["company_id"] == queue[0]["id"]


def test_generated_draft_contains_required_fields_and_linkage(client: TestClient) -> None:
    run_id = _create_run(client, ["W25"])
    _wait_for_scrape_completion(client, run_id)

    queue_response = client.get(f"/runs/{run_id}/companies?status=pending_review", headers=AUTH_HEADERS)
    company = queue_response.json()["data"]["companies"][0]
    _set_company_status(client, company["id"], "accepted")

    generate_response = client.post(
        f"/runs/{run_id}/generate-messages",
        json={"founder_selection_strategy": "first_verified_email", "max_messages": 1},
        headers=AUTH_HEADERS,
    )
    assert generate_response.status_code == 200

    outreach_rows = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)
    assert len(outreach_rows) == 1
    row = outreach_rows[0]

    assert row["status"] == OUTREACH_STATUS_DRAFT
    assert row["user_id"] == "00000000-0000-0000-0000-000000000001"
    assert row["run_id"] == run_id
    assert row["company_id"] == company["id"]
    assert isinstance(row["subject"], str) and row["subject"].strip()
    assert isinstance(row["message_content"], str) and row["message_content"].strip()


def test_generation_failure_persists_generation_failed_row(client: TestClient) -> None:
    run_id = _create_run(client, ["MESSAGE_FAIL"])
    _wait_for_scrape_completion(client, run_id)

    queue_response = client.get(f"/runs/{run_id}/companies?status=pending_review", headers=AUTH_HEADERS)
    company = queue_response.json()["data"]["companies"][0]
    _set_company_status(client, company["id"], "accepted")

    generate_response = client.post(
        f"/runs/{run_id}/generate-messages",
        json={"founder_selection_strategy": "first_verified_email", "max_messages": 5},
        headers=AUTH_HEADERS,
    )
    assert generate_response.status_code == 200

    payload = generate_response.json()["data"]
    assert payload["generated_count"] == 0
    assert payload["generation_failed_count"] == 1

    outreach_rows = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)
    assert len(outreach_rows) == 1
    assert outreach_rows[0]["status"] == OUTREACH_STATUS_GENERATION_FAILED
    assert outreach_rows[0]["error_message"]


def test_generate_messages_blocks_ownership_and_quota(client: TestClient) -> None:
    repository = client.app.state.run_repository

    repository.ensure_user_exists(user_id="00000000-0000-0000-0000-000000000099", email="other@user.local")
    foreign_run = repository.create_run(
        user_id="00000000-0000-0000-0000-000000000099",
        selected_batches=["S24"],
        profile_snapshot={},
        status=RUN_STATUS_COMPLETED,
        progress=100,
    )

    forbidden = client.post(
        f"/runs/{foreign_run['id']}/generate-messages",
        json={"founder_selection_strategy": "first_verified_email", "max_messages": 1},
        headers=AUTH_HEADERS,
    )
    assert forbidden.status_code == 404
    assert forbidden.json()["error"]["code"] == "NOT_FOUND"

    run_id = _create_run(client, ["W25"])
    _wait_for_scrape_completion(client, run_id)
    queue_response = client.get(f"/runs/{run_id}/companies?status=pending_review", headers=AUTH_HEADERS)
    company = queue_response.json()["data"]["companies"][0]
    _set_company_status(client, company["id"], "accepted")

    client.app.state.outreach_generation_service._messages_per_day_limit = 0

    quota_response = client.post(
        f"/runs/{run_id}/generate-messages",
        json={"founder_selection_strategy": "first_verified_email", "max_messages": 1},
        headers=AUTH_HEADERS,
    )
    assert quota_response.status_code == 429
    assert quota_response.json()["error"]["code"] == "QUOTA_EXCEEDED"
