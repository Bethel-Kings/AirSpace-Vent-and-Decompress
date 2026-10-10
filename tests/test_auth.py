from fastapi import status


def test_register_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "password": "SecurePassword123!"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(client, test_user):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": test_user.email, "password": "SecurePassword123!"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]


def test_login_success(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "Password123!"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # Check cookie
    assert "access_token" in response.cookies


def test_login_wrong_password(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_me_authenticated(client, auth_headers):
    response = client.get("/api/v1/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == "testuser@example.com"


def test_get_me_unauthenticated(client):
    response = client.get("/api/v1/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_invalidates_token(client, auth_headers):
    me = client.get("/api/v1/me", headers=auth_headers)
    assert me.status_code == status.HTTP_200_OK

    logout = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert logout.status_code == status.HTTP_200_OK

    after = client.get("/api/v1/me", headers=auth_headers)
    assert after.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_account(client, auth_headers):
    response = client.delete("/api/v1/account", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Verify account is gone
    me_resp = client.get("/api/v1/me", headers=auth_headers)
    assert me_resp.status_code == status.HTTP_401_UNAUTHORIZED
