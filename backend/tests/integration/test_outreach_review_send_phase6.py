from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.statuses import (
    COMPANY_STATUS_ACCEPTED,
    OUTREACH_STATUS_APPROVED,
    OUTREACH_STATUS_DRAFT,
    OUTREACH_STATUS_FAILED,
    OUTREACH_STATUS_SENT,
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


def _accept_companies(client: TestClient, run_id: str) -> list[dict]:
    queue_response = client.get(f"/runs/{run_id}/companies?status=pending_review", headers=AUTH_HEADERS)
    assert queue_response.status_code == 200
    companies = queue_response.json()["data"]["companies"]

    for company in companies:
        patch_response = client.patch(
            f"/companies/{company['id']}",
            json={"status": "accepted"},
            headers=AUTH_HEADERS,
        )
        assert patch_response.status_code == 200

    return companies


def _generate_messages(client: TestClient, run_id: str, *, max_messages: int) -> None:
    response = client.post(
        f"/runs/{run_id}/generate-messages",
        json={"founder_selection_strategy": "first_verified_email", "max_messages": max_messages},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == RUN_STATUS_MESSAGES_GENERATED


def test_patch_outreach_allows_permitted_states(client: TestClient) -> None:
    run_id = _create_run(client, ["W25"])
    _wait_for_scrape_completion(client, run_id)
    _accept_companies(client, run_id)
    _generate_messages(client, run_id, max_messages=1)

    outreach_row = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)[0]

    patch_response = client.patch(
        f"/outreach/{outreach_row['id']}",
        json={
            "subject": "Updated subject line",
            "message_content": "Updated message body.",
            "status": "approved",
            "review_notes": "Looks good after edits.",
        },
        headers=AUTH_HEADERS,
    )
    assert patch_response.status_code == 200
    payload = patch_response.json()["data"]
    assert payload["status"] == OUTREACH_STATUS_APPROVED

    detail_response = client.get(f"/outreach/{outreach_row['id']}", headers=AUTH_HEADERS)
    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    assert detail["subject"] == "Updated subject line"
    assert detail["message_content"] == "Updated message body."
    assert detail["review_notes"] == "Looks good after edits."
    assert detail["status"] == OUTREACH_STATUS_APPROVED

    invalid_status_response = client.patch(
        f"/outreach/{outreach_row['id']}",
        json={"status": "sent"},
        headers=AUTH_HEADERS,
    )
    assert invalid_status_response.status_code == 422


def test_regenerate_success_and_failure_preserve_prior_draft(client: TestClient) -> None:
    run_id = _create_run(client, ["W25"])
    _wait_for_scrape_completion(client, run_id)
    _accept_companies(client, run_id)
    _generate_messages(client, run_id, max_messages=1)

    outreach_row = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)[0]

    regenerate_response = client.post(
        f"/outreach/{outreach_row['id']}/regenerate",
        json={
            "critique": "Make it shorter and less formal.",
            "message_preferences_override": {"tone": "casual"},
        },
        headers=AUTH_HEADERS,
    )
    assert regenerate_response.status_code == 200
    regenerated = regenerate_response.json()["data"]
    assert regenerated["status"] == OUTREACH_STATUS_DRAFT

    detail_after_success = client.get(f"/outreach/{outreach_row['id']}", headers=AUTH_HEADERS).json()["data"]

    failed_regenerate_response = client.post(
        f"/outreach/{outreach_row['id']}/regenerate",
        json={
            "critique": "fail-regen please",
            "message_preferences_override": {"tone": "casual"},
        },
        headers=AUTH_HEADERS,
    )
    assert failed_regenerate_response.status_code == 502
    assert failed_regenerate_response.json()["error"]["code"] == "GEMINI_FAILED"

    detail_after_failure = client.get(f"/outreach/{outreach_row['id']}", headers=AUTH_HEADERS).json()["data"]
    assert detail_after_failure["subject"] == detail_after_success["subject"]
    assert detail_after_failure["message_content"] == detail_after_success["message_content"]
    assert detail_after_failure["status"] == OUTREACH_STATUS_DRAFT
    assert detail_after_failure["error_message"]


def test_send_approved_enforces_ownership_quota_and_approved_only(client: TestClient) -> None:
    run_id = _create_run(client, ["W25", "S24"])
    _wait_for_scrape_completion(client, run_id)
    _accept_companies(client, run_id)
    _generate_messages(client, run_id, max_messages=2)

    rows = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)
    assert len(rows) == 2

    approve_first = client.patch(
        f"/outreach/{rows[0]['id']}",
        json={"status": "approved"},
        headers=AUTH_HEADERS,
    )
    assert approve_first.status_code == 200

    send_response = client.post(
        f"/runs/{run_id}/send-approved",
        json={"send_mode": "approved_only"},
        headers=AUTH_HEADERS,
    )
    assert send_response.status_code == 200
    payload = send_response.json()["data"]
    assert payload["sent_count"] == 1
    assert payload["failed_count"] == 0

    after_rows = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)
    statuses_by_id = {row["id"]: row["status"] for row in after_rows}
    assert statuses_by_id[rows[0]["id"]] == OUTREACH_STATUS_SENT
    assert statuses_by_id[rows[1]["id"]] == OUTREACH_STATUS_DRAFT

    review_summary_response = client.get(f"/runs/{run_id}/outreach/review-summary", headers=AUTH_HEADERS)
    assert review_summary_response.status_code == 200
    counts = review_summary_response.json()["data"]["counts"]
    assert counts[OUTREACH_STATUS_SENT] == 1
    assert counts[OUTREACH_STATUS_DRAFT] == 1

    client.app.state.outreach_service._sends_per_day_limit = 0

    quota_response = client.post(
        f"/runs/{run_id}/send-approved",
        json={"send_mode": "approved_only"},
        headers=AUTH_HEADERS,
    )
    assert quota_response.status_code == 429
    assert quota_response.json()["error"]["code"] == "QUOTA_EXCEEDED"

    repository = client.app.state.run_repository
    repository.ensure_user_exists(user_id="00000000-0000-0000-0000-000000000099", email="other@user.local")
    foreign_run = repository.create_run(
        user_id="00000000-0000-0000-0000-000000000099",
        selected_batches=["S24"],
        profile_snapshot={},
        status=RUN_STATUS_MESSAGES_GENERATED,
        progress=100,
    )

    forbidden_response = client.post(
        f"/runs/{foreign_run['id']}/send-approved",
        json={"send_mode": "approved_only"},
        headers=AUTH_HEADERS,
    )
    assert forbidden_response.status_code == 404
    assert forbidden_response.json()["error"]["code"] == "NOT_FOUND"


def test_send_approved_marks_gmail_failures_without_crashing_batch(client: TestClient) -> None:
    run_id = _create_run(client, ["W25", "S24"])
    _wait_for_scrape_completion(client, run_id)
    _accept_companies(client, run_id)
    _generate_messages(client, run_id, max_messages=2)

    rows = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)
    assert len(rows) == 2

    for row in rows:
        approve_response = client.patch(
            f"/outreach/{row['id']}",
            json={"status": "approved"},
            headers=AUTH_HEADERS,
        )
        assert approve_response.status_code == 200

    client.app.state.run_repository.update_outreach(
        outreach_id=rows[1]["id"],
        fields={"founder_email": "founder@gmail-fail.test"},
    )

    send_response = client.post(
        f"/runs/{run_id}/send-approved",
        json={"send_mode": "approved_only"},
        headers=AUTH_HEADERS,
    )
    assert send_response.status_code == 200
    payload = send_response.json()["data"]
    assert payload["sent_count"] == 1
    assert payload["failed_count"] == 1

    final_rows = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)
    status_by_id = {row["id"]: row for row in final_rows}

    assert status_by_id[rows[0]["id"]]["status"] in {OUTREACH_STATUS_SENT, OUTREACH_STATUS_FAILED}
    assert status_by_id[rows[1]["id"]]["status"] in {OUTREACH_STATUS_SENT, OUTREACH_STATUS_FAILED}

    failed_rows = [row for row in final_rows if row["status"] == OUTREACH_STATUS_FAILED]
    sent_rows = [row for row in final_rows if row["status"] == OUTREACH_STATUS_SENT]
    assert len(failed_rows) == 1
    assert len(sent_rows) == 1
    assert failed_rows[0]["error_message"]
    assert sent_rows[0]["sent_at"] is not None


def test_send_single_requires_approved_and_confirm_send(client: TestClient) -> None:
    run_id = _create_run(client, ["W25"])
    _wait_for_scrape_completion(client, run_id)
    _accept_companies(client, run_id)
    _generate_messages(client, run_id, max_messages=1)

    outreach_row = client.app.state.run_repository.get_outreach_for_run(run_id=run_id)[0]

    missing_confirm = client.post(
        f"/outreach/{outreach_row['id']}/send",
        json={"confirm_send": False},
        headers=AUTH_HEADERS,
    )
    assert missing_confirm.status_code == 400
    assert missing_confirm.json()["error"]["code"] == "VALIDATION_ERROR"

    not_approved = client.post(
        f"/outreach/{outreach_row['id']}/send",
        json={"confirm_send": True},
        headers=AUTH_HEADERS,
    )
    assert not_approved.status_code == 409
    assert not_approved.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"

    approve = client.patch(
        f"/outreach/{outreach_row['id']}",
        json={"status": "approved"},
        headers=AUTH_HEADERS,
    )
    assert approve.status_code == 200

    send_response = client.post(
        f"/outreach/{outreach_row['id']}/send",
        json={"confirm_send": True},
        headers=AUTH_HEADERS,
    )
    assert send_response.status_code == 200
    payload = send_response.json()["data"]
    assert payload["status"] == OUTREACH_STATUS_SENT
    assert payload["sent_at"]
