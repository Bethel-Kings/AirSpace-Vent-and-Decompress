from fastapi import status


def test_create_and_get_check_ins(client, auth_headers):
    # Create session
    create_resp = client.post(
        "/api/v1/sessions",
        headers=auth_headers,
        json={"content": "Trying out check-in feature."},
    )
    session_id = create_resp.json()["id"]

    # Add before check-in (FR-040)
    pre_resp = client.post(
        f"/api/v1/sessions/{session_id}/check-ins",
        headers=auth_headers,
        json={"stage": "before", "value": "Very Anxious (1/5)"},
    )
    assert pre_resp.status_code == status.HTTP_201_CREATED
    assert pre_resp.json()["stage"] == "before"
    assert pre_resp.json()["value"] == "Very Anxious (1/5)"

    # Add after check-in (FR-041)
    post_resp = client.post(
        f"/api/v1/sessions/{session_id}/check-ins",
        headers=auth_headers,
        json={"stage": "after", "value": "Much Calmer (4/5)"},
    )
    assert post_resp.status_code == status.HTTP_201_CREATED
    assert post_resp.json()["stage"] == "after"
    assert post_resp.json()["value"] == "Much Calmer (4/5)"

    # Review check-ins (FR-043)
    list_resp = client.get(
        f"/api/v1/sessions/{session_id}/check-ins",
        headers=auth_headers,
    )
    assert list_resp.status_code == status.HTTP_200_OK
    check_ins = list_resp.json()
    assert len(check_ins) == 2
    stages = [c["stage"] for c in check_ins]
    assert "before" in stages
    assert "after" in stages


def test_check_in_history_and_followups(client, auth_headers, db_session):
    create_resp = client.post(
        "/api/v1/sessions",
        headers=auth_headers,
        json={"content": "Need a later reset check-in.", "initial_mood": "Heavy (2/5)"},
    )
    session_id = create_resp.json()["id"]
    client.post(
        f"/api/v1/sessions/{session_id}/check-ins",
        headers=auth_headers,
        json={"stage": "after", "value": "Much Calmer (4/5)"},
    )
    client.post(
        f"/api/v1/sessions/{session_id}/check-ins",
        headers=auth_headers,
        json={"stage": "reset_3d", "value": "Steadier (4/5)"},
    )

    history = client.get("/api/v1/check-ins", headers=auth_headers)
    assert history.status_code == status.HTTP_200_OK
    assert history.json()["total"] >= 3
    stages = {item["stage"] for item in history.json()["check_ins"]}
    assert {"before", "after", "reset_3d"} <= stages

    followups = client.get("/api/v1/reset-followups", headers=auth_headers)
    assert followups.status_code == status.HTTP_200_OK
    assert "pending" in followups.json()
    assert "completed" in followups.json()


def test_cross_user_check_in_blocked(client, auth_headers, second_auth_headers):
    # User 1 creates session
    create_resp = client.post(
        "/api/v1/sessions",
        headers=auth_headers,
        json={"content": "Session for check-in isolation test."},
    )
    session_id = create_resp.json()["id"]

    # User 2 tries to add check-in to User 1's session (FR-050, FR-051)
    hack_resp = client.post(
        f"/api/v1/sessions/{session_id}/check-ins",
        headers=second_auth_headers,
        json={"stage": "before", "value": "Sneaky Checkin"},
    )
    assert hack_resp.status_code == status.HTTP_404_NOT_FOUND

    history = client.get("/api/v1/check-ins", headers=second_auth_headers)
    assert history.status_code == status.HTTP_200_OK
    assert history.json()["total"] == 0
