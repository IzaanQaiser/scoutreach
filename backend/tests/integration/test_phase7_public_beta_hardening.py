from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app.models.statuses import (
    OUTREACH_STATUS_APPROVED,
    OUTREACH_STATUS_DRAFT,
    OUTREACH_STATUS_FAILED,
    OUTREACH_STATUS_SENT,
    RUN_STATUS_COMPLETED,
    RUN_STATUS_COMPLETED_WITH_ERRORS,
    RUN_STATUS_FAILED,
    RUN_STATUS_MESSAGES_GENERATED,
)
from app.utils import provider_resilience


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


def _accept_all_pending_companies(client: TestClient, run_id: str) -> None:
    queue_response = client.get(f"/runs/{run_id}/companies?status=pending_review", headers=AUTH_HEADERS)
    assert queue_response.status_code == 200
    for company in queue_response.json()["data"]["companies"]:
        response = client.patch(
            f"/companies/{company['id']}",
            json={"status": "accepted"},
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200


def _generate_messages(client: TestClient, run_id: str, *, max_messages: int = 25) -> None:
    response = client.post(
        f"/runs/{run_id}/generate-messages",
        json={"founder_selection_strategy": "first_verified_email", "max_messages": max_messages},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200


def _approve_all_outreach_for_run(client: TestClient, run_id: str) -> None:
    rows = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)
    for row in rows:
        response = client.patch(
            f"/outreach/{row['id']}",
            json={"status": "approved"},
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200


def test_generation_quota_rejection_does_not_mutate_state(client: TestClient) -> None:
    run_id = _create_run(client, ["W25"])
    _wait_for_scrape_completion(client, run_id)
    _accept_all_pending_companies(client, run_id)

    client.app.state.outreach_generation_service._messages_per_day_limit = 0

    response = client.post(
        f"/runs/{run_id}/generate-messages",
        json={"founder_selection_strategy": "first_verified_email", "max_messages": 1},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "QUOTA_EXCEEDED"

    status_payload = client.get(f"/runs/{run_id}/status", headers=AUTH_HEADERS).json()["data"]
    assert status_payload["status"] in {RUN_STATUS_COMPLETED, RUN_STATUS_COMPLETED_WITH_ERRORS}

    outreach_rows = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)
    assert outreach_rows == []


def test_regeneration_quota_rejection_preserves_existing_draft(client: TestClient) -> None:
    run_id = _create_run(client, ["W25"])
    _wait_for_scrape_completion(client, run_id)
    _accept_all_pending_companies(client, run_id)
    _generate_messages(client, run_id, max_messages=1)

    outreach_row = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)[0]
    baseline_subject = outreach_row["subject"]
    baseline_message = outreach_row["message_content"]

    client.app.state.outreach_service._regenerations_per_day_limit = 0

    response = client.post(
        f"/outreach/{outreach_row['id']}/regenerate",
        json={"critique": "shorter please", "message_preferences_override": {"tone": "casual"}},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "QUOTA_EXCEEDED"

    detail = client.get(f"/outreach/{outreach_row['id']}", headers=AUTH_HEADERS).json()["data"]
    assert detail["status"] == OUTREACH_STATUS_DRAFT
    assert detail["subject"] == baseline_subject
    assert detail["message_content"] == baseline_message


def test_send_quota_rejection_does_not_partially_mutate_state(client: TestClient) -> None:
    run_id = _create_run(client, ["W25", "S24"])
    _wait_for_scrape_completion(client, run_id)
    _accept_all_pending_companies(client, run_id)
    _generate_messages(client, run_id, max_messages=2)
    _approve_all_outreach_for_run(client, run_id)

    client.app.state.outreach_service._sends_per_day_limit = 1

    response = client.post(
        f"/runs/{run_id}/send-approved",
        json={"send_mode": "approved_only"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "QUOTA_EXCEEDED"

    rows = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)
    assert len(rows) == 2
    assert all(row["status"] == OUTREACH_STATUS_APPROVED for row in rows)

    status_payload = client.get(f"/runs/{run_id}/status", headers=AUTH_HEADERS).json()["data"]
    assert status_payload["status"] == RUN_STATUS_MESSAGES_GENERATED


def test_retry_backoff_and_throttle_behavior_for_transient_send_errors(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_id = _create_run(client, ["W25"])
    _wait_for_scrape_completion(client, run_id)
    _accept_all_pending_companies(client, run_id)
    _generate_messages(client, run_id, max_messages=1)

    outreach_row = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)[0]
    client.app.state.run_repository.update_outreach(
        outreach_id=outreach_row["id"],
        fields={"founder_email": "rate-limit@gmail-429.test"},
    )
    approve = client.patch(
        f"/outreach/{outreach_row['id']}",
        json={"status": "approved"},
        headers=AUTH_HEADERS,
    )
    assert approve.status_code == 200

    sleep_calls: list[float] = []

    def _fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(provider_resilience.time, "sleep", _fake_sleep)

    call_counter = {"count": 0}
    original_send = client.app.state.gmail_client.send_message

    def _counting_send(*, outreach_id: str, to_email: str | None, subject: str | None, message_content: str | None) -> dict:
        call_counter["count"] += 1
        return original_send(
            outreach_id=outreach_id,
            to_email=to_email,
            subject=subject,
            message_content=message_content,
        )

    monkeypatch.setattr(client.app.state.gmail_client, "send_message", _counting_send)

    client.app.state.outreach_service._provider_throttle_seconds = 0
    client.app.state.outreach_service._send_retry_attempts = 3
    client.app.state.outreach_service._send_retry_base_delay_seconds = 0.01
    client.app.state.outreach_service._send_retry_max_jitter_seconds = 0

    response = client.post(
        f"/runs/{run_id}/send-approved",
        json={"send_mode": "approved_only"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["sent_count"] == 0
    assert payload["failed_count"] == 1

    assert call_counter["count"] == 3
    assert sleep_calls == [0.01, 0.02]

    row = client.app.state.run_repository.get_outreach(outreach_id=outreach_row["id"])
    assert row is not None
    assert row["status"] == OUTREACH_STATUS_FAILED
    assert row["error_message"]


def test_generation_retry_backoff_for_transient_gemini_errors(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_id = _create_run(client, ["MESSAGE_429"])
    _wait_for_scrape_completion(client, run_id)
    _accept_all_pending_companies(client, run_id)

    sleep_calls: list[float] = []

    def _fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(provider_resilience.time, "sleep", _fake_sleep)

    call_counter = {"count": 0}
    original_generate = client.app.state.gemini_client.generate_outreach_draft

    def _counting_generate(*, company: dict, founder: dict, profile_snapshot: dict) -> dict:
        call_counter["count"] += 1
        return original_generate(
            company=company,
            founder=founder,
            profile_snapshot=profile_snapshot,
        )

    monkeypatch.setattr(client.app.state.gemini_client, "generate_outreach_draft", _counting_generate)

    client.app.state.outreach_generation_service._gemini_max_attempts = 3
    client.app.state.outreach_generation_service._gemini_base_delay_seconds = 0.01
    client.app.state.outreach_generation_service._gemini_max_jitter_seconds = 0
    client.app.state.outreach_generation_service._gemini_throttle_seconds = 0

    response = client.post(
        f"/runs/{run_id}/generate-messages",
        json={"founder_selection_strategy": "first_verified_email", "max_messages": 1},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["generated_count"] == 0
    assert payload["generation_failed_count"] == 1

    assert call_counter["count"] == 3
    assert sleep_calls == [0.01, 0.02]


def test_phase7_smoke_happy_path_manual_review_then_send(client: TestClient) -> None:
    run_id = _create_run(client, ["W25", "S24"])
    _wait_for_scrape_completion(client, run_id)
    _accept_all_pending_companies(client, run_id)
    _generate_messages(client, run_id, max_messages=2)

    draft_rows = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)
    assert len(draft_rows) == 2
    assert all(row["status"] == OUTREACH_STATUS_DRAFT for row in draft_rows)

    pre_review_send = client.post(
        f"/runs/{run_id}/send-approved",
        json={"send_mode": "approved_only"},
        headers=AUTH_HEADERS,
    )
    assert pre_review_send.status_code == 200
    assert pre_review_send.json()["data"]["sent_count"] == 0

    _approve_all_outreach_for_run(client, run_id)

    send_response = client.post(
        f"/runs/{run_id}/send-approved",
        json={"send_mode": "approved_only"},
        headers=AUTH_HEADERS,
    )
    assert send_response.status_code == 200
    payload = send_response.json()["data"]
    assert payload["sent_count"] == 2
    assert payload["failed_count"] == 0

    final_rows = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)
    assert all(row["status"] == OUTREACH_STATUS_SENT for row in final_rows)
    assert all(row["sent_at"] is not None for row in final_rows)


def test_regression_ownership_invariants_hold_for_outreach_endpoints(client: TestClient) -> None:
    repository = client.app.state.run_repository
    repository.ensure_user_exists(user_id="00000000-0000-0000-0000-000000000099", email="other@user.local")

    foreign_run = repository.create_run(
        user_id="00000000-0000-0000-0000-000000000099",
        selected_batches=["S24"],
        profile_snapshot={},
        status=RUN_STATUS_MESSAGES_GENERATED,
        progress=100,
    )
    repository.insert_company(
        payload={
            "run_id": foreign_run["id"],
            "name": "Foreign Company",
            "yc_url": "https://www.ycombinator.com/companies/foreign",
            "website_url": "https://foreign-company.test",
            "domain": "foreign-company.test",
            "batch": "S24",
            "founders": [{"name": "Foreign Founder", "email": "foreign@example.test"}],
            "raw_scraped_data": {},
            "website_content": {},
            "tags": [],
            "dossier": {},
            "status": "accepted",
            "fit_score": None,
        }
    )
    foreign_company = repository.get_companies_for_run(run_id=foreign_run["id"])[0]
    foreign_outreach = repository.insert_outreach(
        payload={
            "user_id": "00000000-0000-0000-0000-000000000099",
            "run_id": foreign_run["id"],
            "company_id": foreign_company["id"],
            "founder_name": "Foreign Founder",
            "founder_email": "foreign@example.test",
            "subject": "Foreign subject",
            "message_content": "Foreign message",
            "status": "approved",
            "review_notes": None,
            "error_message": None,
            "sent_at": None,
        }
    )

    assert client.get(f"/runs/{foreign_run['id']}/outreach", headers=AUTH_HEADERS).status_code == 404
    assert client.get(f"/outreach/{foreign_outreach['id']}", headers=AUTH_HEADERS).status_code == 404
    assert (
        client.patch(
            f"/outreach/{foreign_outreach['id']}",
            json={"status": "rejected"},
            headers=AUTH_HEADERS,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/outreach/{foreign_outreach['id']}/regenerate",
            json={"critique": "test", "message_preferences_override": {}},
            headers=AUTH_HEADERS,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/runs/{foreign_run['id']}/send-approved",
            json={"send_mode": "approved_only"},
            headers=AUTH_HEADERS,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/outreach/{foreign_outreach['id']}/send",
            json={"confirm_send": True},
            headers=AUTH_HEADERS,
        ).status_code
        == 404
    )
