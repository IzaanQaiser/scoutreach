from __future__ import annotations

from fastapi.testclient import TestClient


AUTH_HEADERS = {"Authorization": "Bearer local-dev-token"}


def test_me_returns_extended_user_payload(client: TestClient) -> None:
    response = client.get("/me", headers=AUTH_HEADERS)
    assert response.status_code == 200

    payload = response.json()["data"]
    user = payload["user"]
    assert user["id"] == "00000000-0000-0000-0000-000000000001"
    assert user["email"] == "dev@scoutreach.local"
    assert user["onboarding_status"] == "not_started"
    assert user["onboarding_step"] == "auth"
    assert payload["has_candidate_profile"] is False
    assert payload["onboarding_complete"] is False


def test_name_profile_settings_progress_onboarding_state(client: TestClient) -> None:
    patch_me = client.patch(
        "/me",
        json={"first_name": "Izaan", "last_name": "K"},
        headers=AUTH_HEADERS,
    )
    assert patch_me.status_code == 200
    assert patch_me.json()["data"]["onboarding_step"] == "profile_sources"

    put_profile = client.put(
        "/candidate-profile",
        json={
            "resume": "Resume text",
            "github_url": "https://github.com/example",
            "portfolio_url": "https://example.com",
            "target_roles": ["Software Engineer"],
            "job_preferences": {"industries": ["AI"]},
        },
        headers=AUTH_HEADERS,
    )
    assert put_profile.status_code == 200

    profile = client.get("/candidate-profile", headers=AUTH_HEADERS)
    assert profile.status_code == 200
    profile_data = profile.json()["data"]
    assert profile_data["resume"] == "Resume text"
    assert profile_data["target_roles"] == ["Software Engineer"]

    patch_settings = client.patch(
        "/settings",
        json={
            "message_preferences": {
                "tone": "casual",
                "length": "short",
            }
        },
        headers=AUTH_HEADERS,
    )
    assert patch_settings.status_code == 200

    onboarding_state = client.get("/onboarding/state", headers=AUTH_HEADERS)
    assert onboarding_state.status_code == 200
    state_data = onboarding_state.json()["data"]
    assert state_data["status"] == "in_progress"
    assert state_data["step"] == "calibration"


def test_onboarding_example_generation_and_feedback_loop(client: TestClient) -> None:
    client.patch(
        "/me",
        json={"first_name": "Izaan", "last_name": "K"},
        headers=AUTH_HEADERS,
    )

    generated = client.post(
        "/onboarding/example-messages",
        json={"loop_index": 0},
        headers=AUTH_HEADERS,
    )
    assert generated.status_code == 200
    data = generated.json()["data"]
    assert data["loop_index"] == 0
    assert data["max_loops"] == 3
    assert len(data["examples"]) == 5
    assert data["examples"][0]["subject"]

    refreshed = client.post(
        "/onboarding/example-feedback",
        json={
            "loop_index": 0,
            "rejected_examples": [
                {
                    "example_id": "loop-1-example-1",
                    "position_industry_feedback": "less generic",
                    "subject_feedback": "more direct",
                    "body_feedback": "shorter",
                }
            ],
        },
        headers=AUTH_HEADERS,
    )
    assert refreshed.status_code == 200
    refreshed_data = refreshed.json()["data"]
    assert refreshed_data["loop_index"] == 1
    assert len(refreshed_data["examples"]) == 5


def test_onboarding_feedback_empty_completes_flow(client: TestClient) -> None:
    client.post(
        "/onboarding/example-messages",
        json={"loop_index": 0},
        headers=AUTH_HEADERS,
    )

    completed = client.post(
        "/onboarding/example-feedback",
        json={"loop_index": 0, "rejected_examples": []},
        headers=AUTH_HEADERS,
    )
    assert completed.status_code == 200
    completion = completed.json()["data"]
    assert completion["onboarding_complete"] is True
    assert completion["step"] == "done"
    assert completion["status"] == "completed"


def test_onboarding_loop_cap_and_skip_paths(client: TestClient) -> None:
    client.post(
        "/onboarding/example-messages",
        json={"loop_index": 2},
        headers=AUTH_HEADERS,
    )

    cap_exit = client.post(
        "/onboarding/example-feedback",
        json={
            "loop_index": 2,
            "rejected_examples": [{"body_feedback": "not my style"}],
        },
        headers=AUTH_HEADERS,
    )
    assert cap_exit.status_code == 200
    cap_data = cap_exit.json()["data"]
    assert cap_data["status"] == "completed_after_cap"
    assert cap_data["onboarding_complete"] is True

    reset_client = client
    skipped = reset_client.post(
        "/onboarding/complete",
        json={"completion_mode": "skipped_calibration"},
        headers=AUTH_HEADERS,
    )
    assert skipped.status_code == 200
    assert skipped.json()["data"]["status"] == "skipped_calibration"
