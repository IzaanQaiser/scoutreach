from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.statuses import (
    COMPANY_STATUS_ACCEPTED,
    COMPANY_STATUS_DOSSIER_FAILED,
    COMPANY_STATUS_PENDING_REVIEW,
    COMPANY_STATUS_REJECTED,
    RUN_STATUS_COMPLETED,
    RUN_STATUS_COMPLETED_WITH_ERRORS,
    RUN_STATUS_FAILED,
)


AUTH_HEADERS = {"Authorization": "Bearer local-dev-token"}
TERMINAL_RUN_STATUSES = {
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


def _wait_for_terminal_run_status(client: TestClient, run_id: str) -> None:
    for _ in range(20):
        response = client.get(f"/runs/{run_id}/status", headers=AUTH_HEADERS)
        assert response.status_code == 200
        payload = response.json()["data"]
        if payload["status"] in TERMINAL_RUN_STATUSES:
            return
    raise AssertionError("Run did not reach terminal status.")


def test_pending_queue_returns_owned_run_companies_only(client: TestClient) -> None:
    run_id = _create_run(client, ["W25"])
    _wait_for_terminal_run_status(client, run_id)

    response = client.get(f"/runs/{run_id}/companies?status=pending_review", headers=AUTH_HEADERS)
    assert response.status_code == 200
    payload = response.json()["data"]
    assert len(payload["companies"]) == 1
    assert payload["companies"][0]["run_id"] == run_id

    repository = client.app.state.run_repository
    repository.ensure_user_exists(user_id="00000000-0000-0000-0000-000000000099", email="other@user.local")
    foreign_run = repository.create_run(
        user_id="00000000-0000-0000-0000-000000000099",
        selected_batches=["S24"],
        profile_snapshot={},
        status=RUN_STATUS_COMPLETED,
        progress=100,
    )
    repository.insert_company(
        payload={
            "run_id": foreign_run["id"],
            "name": "Foreign Company",
            "yc_url": "https://www.ycombinator.com/companies/foreign-company",
            "website_url": "https://foreign-company.com",
            "domain": "foreign-company.com",
            "batch": "S24",
            "founders": [],
            "raw_scraped_data": {},
            "website_content": {},
            "tags": [],
            "dossier": {},
            "status": COMPANY_STATUS_PENDING_REVIEW,
            "fit_score": None,
        }
    )

    forbidden = client.get(f"/runs/{foreign_run['id']}/companies?status=pending_review", headers=AUTH_HEADERS)
    assert forbidden.status_code == 404
    assert forbidden.json()["error"]["code"] == "NOT_FOUND"


def test_accept_reject_updates_persist_and_pending_count_is_accurate(client: TestClient) -> None:
    run_id = _create_run(client, ["W25", "S24"])
    _wait_for_terminal_run_status(client, run_id)

    pending_count_response = client.get(f"/runs/{run_id}/companies/pending-count", headers=AUTH_HEADERS)
    assert pending_count_response.status_code == 200
    assert pending_count_response.json()["data"]["pending_count"] == 2

    pending_response = client.get(f"/runs/{run_id}/companies?status=pending_review", headers=AUTH_HEADERS)
    assert pending_response.status_code == 200
    companies = pending_response.json()["data"]["companies"]
    assert len(companies) == 2

    first_id = companies[0]["id"]
    second_id = companies[1]["id"]

    accept_response = client.patch(
        f"/companies/{first_id}",
        json={"status": "accepted"},
        headers=AUTH_HEADERS,
    )
    assert accept_response.status_code == 200
    assert accept_response.json()["data"]["status"] == COMPANY_STATUS_ACCEPTED

    reject_response = client.patch(
        f"/companies/{second_id}",
        json={"status": "rejected"},
        headers=AUTH_HEADERS,
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["data"]["status"] == COMPANY_STATUS_REJECTED

    after_count_response = client.get(f"/runs/{run_id}/companies/pending-count", headers=AUTH_HEADERS)
    assert after_count_response.status_code == 200
    assert after_count_response.json()["data"]["pending_count"] == 0

    accepted_response = client.get(f"/runs/{run_id}/companies?status=accepted", headers=AUTH_HEADERS)
    assert accepted_response.status_code == 200
    accepted = accepted_response.json()["data"]["companies"]
    assert len(accepted) == 1
    assert accepted[0]["status"] == COMPANY_STATUS_ACCEPTED

    rejected_response = client.get(f"/runs/{run_id}/companies?status=rejected", headers=AUTH_HEADERS)
    assert rejected_response.status_code == 200
    rejected = rejected_response.json()["data"]["companies"]
    assert len(rejected) == 1
    assert rejected[0]["status"] == COMPANY_STATUS_REJECTED


def test_invalid_transition_is_rejected(client: TestClient) -> None:
    run_id = _create_run(client, ["DOSSIER_FAIL"])
    _wait_for_terminal_run_status(client, run_id)

    failed_response = client.get(f"/runs/{run_id}/companies?status=dossier_failed", headers=AUTH_HEADERS)
    assert failed_response.status_code == 200
    failed_companies = failed_response.json()["data"]["companies"]
    assert len(failed_companies) == 1
    assert failed_companies[0]["status"] == COMPANY_STATUS_DOSSIER_FAILED

    patch_response = client.patch(
        f"/companies/{failed_companies[0]['id']}",
        json={"status": "accepted"},
        headers=AUTH_HEADERS,
    )
    assert patch_response.status_code == 409
    payload = patch_response.json()
    assert payload["error"]["code"] == "INVALID_STATUS_TRANSITION"


def test_company_patch_enforces_ownership(client: TestClient) -> None:
    repository = client.app.state.run_repository
    repository.ensure_user_exists(user_id="00000000-0000-0000-0000-000000000099", email="other@user.local")
    foreign_run = repository.create_run(
        user_id="00000000-0000-0000-0000-000000000099",
        selected_batches=["S24"],
        profile_snapshot={},
        status=RUN_STATUS_COMPLETED,
        progress=100,
    )
    repository.insert_company(
        payload={
            "run_id": foreign_run["id"],
            "name": "Foreign Swipe Company",
            "yc_url": "https://www.ycombinator.com/companies/foreign-swipe",
            "website_url": "https://foreign-swipe.com",
            "domain": "foreign-swipe.com",
            "batch": "S24",
            "founders": [],
            "raw_scraped_data": {},
            "website_content": {},
            "tags": [],
            "dossier": {},
            "status": COMPANY_STATUS_PENDING_REVIEW,
            "fit_score": None,
        }
    )
    foreign_company = repository.get_companies_for_run(run_id=foreign_run["id"])[0]

    response = client.patch(
        f"/companies/{foreign_company['id']}",
        json={"status": "accepted"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
