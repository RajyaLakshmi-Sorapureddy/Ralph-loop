from fastapi.testclient import TestClient


def _signup_and_login(client: TestClient, email: str = "requester@example.com") -> str:
    client.post(
        "/auth/signup",
        json={"name": "Requester", "email": email, "password": "hunter22"},
    )
    response = client.post("/auth/login", json={"email": email, "password": "hunter22"})
    return str(response.json()["access_token"])


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_create_request_succeeds_for_authenticated_requester(client: TestClient) -> None:
    token = _signup_and_login(client)

    response = client.post(
        "/requests",
        json={
            "amount": "125.50",
            "currency": "USD",
            "category": "Travel",
            "expense_date": "2026-07-01",
            "description": "Taxi to client site",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert body["status"] == "pending"
    assert body["amount"] == "125.50"
    assert body["category"] == "Travel"


def test_create_request_rejects_missing_required_field(client: TestClient) -> None:
    token = _signup_and_login(client)

    response = client.post(
        "/requests",
        json={
            "amount": "125.50",
            "currency": "USD",
            "category": "Travel",
            # expense_date missing
            "description": "Taxi to client site",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


def test_create_request_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/requests",
        json={
            "amount": "125.50",
            "currency": "USD",
            "category": "Travel",
            "expense_date": "2026-07-01",
            "description": "Taxi to client site",
        },
    )

    assert response.status_code == 401
