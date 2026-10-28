from fastapi import status


def test_health_endpoints(client):
    for path in ("/health", "/healthz", "/ready"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["status"] in {"healthy", "ready"}


def test_unauthenticated_session_access_rejected(client):
    response = client.get("/api/v1/sessions")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_session(client, auth_headers):
    response = client.post(
        "/api/v1/sessions",
        headers=auth_headers,
        json={"content": "I feel completely overwhelmed by everything happening this week."},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["content"] == "I feel completely overwhelmed by everything happening this week."
    assert "id" in data
    assert "created_at" in data
    assert data["check_ins"] == []
    assert data["reflection"] is None


def test_create_session_with_initial_mood(client, auth_headers):
    response = client.post(
        "/api/v1/sessions",
        headers=auth_headers,
        json={
            "content": "Work deadlines are piling up and I cannot catch a break.",
            "initial_mood": "Stressed (4/5)",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert len(data["check_ins"]) == 1
    assert data["check_ins"][0]["stage"] == "before"
    assert data["check_ins"][0]["value"] == "Stressed (4/5)"


def test_list_sessions_isolation(client, auth_headers, second_auth_headers):
    # User 1 creates session
    client.post(
        "/api/v1/sessions",
        headers=auth_headers,
        json={"content": "User 1 private journal entry."},
    )
    # User 2 creates session
    client.post(
        "/api/v1/sessions",
        headers=second_auth_headers,
        json={"content": "User 2 completely separate entry."},
    )

    # User 1 lists sessions
    resp1 = client.get("/api/v1/sessions", headers=auth_headers)
    assert resp1.status_code == status.HTTP_200_OK
    sessions1 = resp1.json()["sessions"]
    assert len(sessions1) == 1
    assert sessions1[0]["content"] == "User 1 private journal entry."

    # User 2 lists sessions
    resp2 = client.get("/api/v1/sessions", headers=second_auth_headers)
    assert resp2.status_code == status.HTTP_200_OK
    sessions2 = resp2.json()["sessions"]
    assert len(sessions2) == 1
    assert sessions2[0]["content"] == "User 2 completely separate entry."


def test_cross_user_access_blocked(client, auth_headers, second_auth_headers):
    # User 1 creates a session
    create_resp = client.post(
        "/api/v1/sessions",
        headers=auth_headers,
        json={"content": "Confidential user 1 thoughts."},
    )
    session_id = create_resp.json()["id"]

    # User 2 tries to read User 1's session (FR-050, FR-051, AC-11)
    get_resp = client.get(f"/api/v1/sessions/{session_id}", headers=second_auth_headers)
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND

    # User 2 tries to modify User 1's session
    patch_resp = client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=second_auth_headers,
        json={"content": "Malicious edit attempt"},
    )
    assert patch_resp.status_code == status.HTTP_404_NOT_FOUND

    # User 2 tries to delete User 1's session
    del_resp = client.delete(f"/api/v1/sessions/{session_id}", headers=second_auth_headers)
    assert del_resp.status_code == status.HTTP_404_NOT_FOUND


def test_delete_own_session(client, auth_headers):
    create_resp = client.post(
        "/api/v1/sessions",
        headers=auth_headers,
        json={"content": "To be deleted."},
    )
    session_id = create_resp.json()["id"]

    # Delete session (FR-025, AC-10)
    del_resp = client.delete(f"/api/v1/sessions/{session_id}", headers=auth_headers)
    assert del_resp.status_code == status.HTTP_200_OK

    # Verify session is gone
    get_resp = client.get(f"/api/v1/sessions/{session_id}", headers=auth_headers)
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND
