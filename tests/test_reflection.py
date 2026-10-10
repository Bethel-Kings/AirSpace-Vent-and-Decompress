from unittest.mock import patch
from fastapi import status
from app.services.ai import AIServiceError


def test_reflect_session_success(client, auth_headers):
    # 1. Create a session
    create_resp = client.post(
        "/api/v1/sessions",
        headers=auth_headers,
        json={"content": "I have so many tasks at work and not enough hours. I feel stressed."},
    )
    session_id = create_resp.json()["id"]

    # 2. Trigger Decompress & Reframe (FR-030)
    reflect_resp = client.post(
        f"/api/v1/sessions/{session_id}/reflect",
        headers=auth_headers,
        json={"focus": "workload"},
    )
    assert reflect_resp.status_code == status.HTTP_200_OK
    reflection_data = reflect_resp.json()
    assert "content" in reflection_data
    assert reflection_data["session_id"] == session_id

    # 3. Verify user's original content is unchanged and untouched (FR-032, FR-033, AC-07)
    session_check = client.get(f"/api/v1/sessions/{session_id}", headers=auth_headers).json()
    assert session_check["content"] == "I have so many tasks at work and not enough hours. I feel stressed."
    assert session_check["reflection"] is not None
    assert session_check["reflection"]["content"] == reflection_data["content"]


def test_reflect_session_ai_failure_preserves_content(client, auth_headers):
    # 1. Create a session
    original_text = "Critical venting entry that must never be lost."
    create_resp = client.post(
        "/api/v1/sessions",
        headers=auth_headers,
        json={"content": original_text},
    )
    session_id = create_resp.json()["id"]

    # 2. Simulate AI provider failure (FR-034, AC-13)
    with patch(
        "app.services.ai.AIReflectionService.generate_reflection",
        side_effect=AIServiceError("Provider connection timed out"),
    ):
        reflect_resp = client.post(
            f"/api/v1/sessions/{session_id}/reflect",
            headers=auth_headers,
            json={},
        )
        assert reflect_resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    # 3. Assert the saved session was NOT destroyed or corrupted
    session_check = client.get(f"/api/v1/sessions/{session_id}", headers=auth_headers).json()
    assert session_check["content"] == original_text
    assert session_check["reflection"] is None


def test_reflection_retention_control(client, auth_headers):
    create_resp = client.post(
        "/api/v1/sessions",
        headers=auth_headers,
        json={"content": "A session used to test keep-or-discard reflection control."},
    )
    session_id = create_resp.json()["id"]
    original = create_resp.json()["content"]

    draft = client.post(
        f"/api/v1/sessions/{session_id}/reflect",
        headers=auth_headers,
        json={"save_immediately": False},
    )
    assert draft.status_code == status.HTTP_200_OK
    assert draft.json()["is_saved"] is False

    kept = client.patch(
        f"/api/v1/sessions/{session_id}/reflection",
        headers=auth_headers,
        json={"is_saved": True},
    )
    assert kept.status_code == status.HTTP_200_OK
    assert kept.json()["is_saved"] is True

    discarded = client.delete(f"/api/v1/sessions/{session_id}/reflection", headers=auth_headers)
    assert discarded.status_code == status.HTTP_200_OK

    session_check = client.get(f"/api/v1/sessions/{session_id}", headers=auth_headers).json()
    assert session_check["content"] == original
    assert session_check["reflection"] is None
