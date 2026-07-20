from fastapi.testclient import TestClient


def test_signup_creates_requester_user(client: TestClient) -> None:
    response = client.post(
        "/auth/signup",
        json={"name": "Alice", "email": "alice@example.com", "password": "hunter22"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["name"] == "Alice"
    assert body["role"] == "requester"
    assert "password" not in body
    assert "password_hash" not in body


def test_signup_rejects_duplicate_email(client: TestClient) -> None:
    payload = {"name": "Alice", "email": "alice@example.com", "password": "hunter22"}
    first = client.post("/auth/signup", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/signup", json=payload)
    assert second.status_code == 409


def test_login_returns_token_on_valid_credentials(client: TestClient) -> None:
    client.post(
        "/auth/signup",
        json={"name": "Bob", "email": "bob@example.com", "password": "correct-horse"},
    )

    response = client.post(
        "/auth/login",
        json={"email": "bob@example.com", "password": "correct-horse"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]


def test_login_rejects_wrong_password(client: TestClient) -> None:
    client.post(
        "/auth/signup",
        json={"name": "Bob", "email": "bob@example.com", "password": "correct-horse"},
    )

    response = client.post(
        "/auth/login",
        json={"email": "bob@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_rejects_unknown_email_with_generic_error(client: TestClient) -> None:
    known_user_response = client.post(
        "/auth/login",
        json={"email": "unknown@example.com", "password": "whatever"},
    )

    client.post(
        "/auth/signup",
        json={"name": "Bob", "email": "bob@example.com", "password": "correct-horse"},
    )
    wrong_password_response = client.post(
        "/auth/login",
        json={"email": "bob@example.com", "password": "wrong-password"},
    )

    assert known_user_response.status_code == wrong_password_response.status_code == 401
    assert known_user_response.json()["detail"] == wrong_password_response.json()["detail"]
