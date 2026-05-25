from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.statuses import (
    COMPANY_STATUS_DOSSIER_FAILED,
    COMPANY_STATUS_PENDING_REVIEW,
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


def _wait_for_terminal_status(client: TestClient, run_id: str) -> dict:
    for _ in range(10):
        response = client.get(f"/runs/{run_id}/status", headers=AUTH_HEADERS)
        assert response.status_code == 200
        payload = response.json()["data"]
        if payload["status"] in TERMINAL_RUN_STATUSES:
            return payload
    raise AssertionError("Run did not reach terminal status.")


def test_dossier_failure_sets_company_status_and_preserves_run(client: TestClient) -> None:
    run_id = _create_run(client, ["DOSSIER_FAIL"])
    status_payload = _wait_for_terminal_status(client, run_id)

    assert status_payload["status"] == RUN_STATUS_COMPLETED_WITH_ERRORS
    assert "dossier_failed=1" in str(status_payload["error_message"])

    companies = client.app.state.run_repository.get_companies_for_run(run_id=run_id)
    assert len(companies) == 1
    assert companies[0]["status"] == COMPANY_STATUS_DOSSIER_FAILED
    assert companies[0]["dossier"] == {}
    assert companies[0]["raw_scraped_data"]["provider_errors"]["gemini"]["code"] == "GEMINI_FAILED"


def test_hunter_empty_email_result_remains_reviewable(client: TestClient) -> None:
    run_id = _create_run(client, ["HUNTER_EMPTY"])
    status_payload = _wait_for_terminal_status(client, run_id)

    assert status_payload["status"] == RUN_STATUS_COMPLETED
    assert status_payload["error_message"] is None

    companies = client.app.state.run_repository.get_companies_for_run(run_id=run_id)
    assert len(companies) == 1
    assert companies[0]["status"] == COMPANY_STATUS_PENDING_REVIEW
    founder = companies[0]["founders"][0]
    assert founder["email_lookup_status"] == "empty"
    assert founder["email"] is None


def test_hunter_failure_stores_error_metadata_without_stopping_run(client: TestClient) -> None:
    run_id = _create_run(client, ["HUNTER_ERROR", "W25"])
    status_payload = _wait_for_terminal_status(client, run_id)

    assert status_payload["status"] == RUN_STATUS_COMPLETED_WITH_ERRORS
    assert "hunter_failed=1" in str(status_payload["error_message"])

    companies = client.app.state.run_repository.get_companies_for_run(run_id=run_id)
    assert len(companies) == 2

    hunter_error_company = next(company for company in companies if "hunter-error" in company["domain"])
    assert hunter_error_company["status"] == COMPANY_STATUS_PENDING_REVIEW
    assert hunter_error_company["raw_scraped_data"]["provider_errors"]["hunter"]["code"] == "HUNTER_FAILED"
    assert hunter_error_company["founders"][0]["email_lookup_status"] == "failed"

    success_company = next(company for company in companies if "example-w25" in company["domain"])
    assert success_company["status"] == COMPANY_STATUS_PENDING_REVIEW
    assert success_company["founders"][0]["email_lookup_status"] == "success"
