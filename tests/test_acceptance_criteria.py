from fastapi import status


def test_pitch_acceptance_criteria_end_to_end_journey(client):
    """
    Validates the end-to-end user journey fulfilling Pitch-Critical Acceptance Criteria
    AC-02 through AC-11 and AC-13.
    """
    # AC-02: A new user can register and log in.
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": "pitchdemo@example.com", "password": "AirSpacePitch2026!"},
    )
    assert reg_res.status_code == status.HTTP_201_CREATED

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "pitchdemo@example.com", "password": "AirSpacePitch2026!"},
    )
    assert login_res.status_code == status.HTTP_200_OK
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # AC-03: The user reaches the AirSpace dashboard / identity after authentication.
    me_res = client.get("/api/v1/me", headers=headers)
    assert me_res.status_code == status.HTTP_200_OK
    assert me_res.json()["email"] == "pitchdemo@example.com"

    # AC-04 & AC-08 (Part 1): Record before-session state & write Air It Out entry.
    session_text = (
        "I feel like I am letting everyone down. The project presentation is approaching "
        "and I have been stuck on this bug for 6 hours. I can't think straight."
    )
    create_res = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={"content": session_text, "initial_mood": "Overwhelmed (1/5)"},
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    session_id = create_res.json()["id"]

    # AC-05: The entry persists after retrieval (simulating browser refresh / reloading).
    refresh_res = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
    assert refresh_res.status_code == status.HTTP_200_OK
    assert refresh_res.json()["content"] == session_text

    # AC-06 & AC-07: Request Decompress & Reframe; AI output is separate from original entry.
    reflect_res = client.post(f"/api/v1/sessions/{session_id}/reflect", headers=headers)
    assert reflect_res.status_code == status.HTTP_200_OK
    reflection_text = reflect_res.json()["content"]
    assert reflection_text is not None

    # Verify session entry still has original content untouched
    verified_session = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert verified_session["content"] == session_text
    assert verified_session["reflection"]["content"] == reflection_text

    # AC-08 (Part 2): Record after-session emotional state.
    post_checkin_res = client.post(
        f"/api/v1/sessions/{session_id}/check-ins",
        headers=headers,
        json={"stage": "after", "value": "Relieved & Clear (4/5)"},
    )
    assert post_checkin_res.status_code == status.HTTP_201_CREATED

    # AC-09: The user can view previous sessions.
    history_res = client.get("/api/v1/sessions", headers=headers)
    assert history_res.status_code == status.HTTP_200_OK
    assert history_res.json()["total"] >= 1
    assert any(s["id"] == session_id for s in history_res.json()["sessions"])

    # AC-11: Another user cannot access the first user's data.
    # Register an unauthorized user
    client.post(
        "/api/v1/auth/register",
        json={"email": "attacker@example.com", "password": "AttackerPass123!"},
    )
    attacker_login = client.post(
        "/api/v1/auth/login",
        json={"email": "attacker@example.com", "password": "AttackerPass123!"},
    )
    attacker_headers = {"Authorization": f"Bearer {attacker_login.json()['access_token']}"}

    attacker_attempt = client.get(f"/api/v1/sessions/{session_id}", headers=attacker_headers)
    assert attacker_attempt.status_code == status.HTTP_404_NOT_FOUND

    followup = client.post(
        f"/api/v1/sessions/{session_id}/check-ins",
        headers=headers,
        json={"stage": "reset_7d", "value": "Clearer (5/5)"},
    )
    assert followup.status_code == status.HTTP_201_CREATED
    history = client.get("/api/v1/check-ins", headers=headers)
    assert history.status_code == status.HTTP_200_OK
    assert any(item["stage"] == "reset_7d" for item in history.json()["check_ins"])

    # AC-10: The user can delete their session.
    delete_res = client.delete(f"/api/v1/sessions/{session_id}", headers=headers)
    assert delete_res.status_code == status.HTTP_200_OK

    # Verify deleted
    deleted_check = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
    assert deleted_check.status_code == status.HTTP_404_NOT_FOUND
