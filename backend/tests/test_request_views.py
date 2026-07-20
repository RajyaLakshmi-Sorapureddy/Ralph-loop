from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Request, User, UserRole
from app.security import create_access_token, hash_password


def _signup_and_login(client: TestClient, email: str = "requester@example.com") -> str:
    client.post(
        "/auth/signup",
        json={"name": "Requester", "email": email, "password": "hunter22"},
    )
    response = client.post("/auth/login", json={"email": email, "password": "hunter22"})
    return str(response.json()["access_token"])


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _make_finance_user(db_session: Session) -> User:
    user = User(
        name="Finance Person",
        email=f"finance-{id(db_session)}@example.com",
        password_hash=hash_password("hunter22"),
        role=UserRole.finance,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_request(
    client: TestClient, token: str, category: str = "Travel", description: str = "Taxi"
) -> int:
    response = client.post(
        "/requests",
        json={
            "amount": "125.50",
            "currency": "USD",
            "category": category,
            "expense_date": "2026-07-01",
            "description": description,
        },
        headers=_auth_headers(token),
    )
    result: int = response.json()["id"]
    return result


def test_list_my_requests_returns_only_own_requests(client: TestClient) -> None:
    token = _signup_and_login(client, email="mine@example.com")
    request_id = _create_request(client, token)
    other_token = _signup_and_login(client, email="other-mine@example.com")
    _create_request(client, other_token)

    response = client.get("/requests/mine", headers=_auth_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == request_id


def test_list_my_requests_sorted_by_most_recently_updated(
    client: TestClient, db_session: Session
) -> None:
    token = _signup_and_login(client, email="sorted@example.com")
    first_id = _create_request(client, token, description="First")
    second_id = _create_request(client, token, description="Second")

    # Requests created back-to-back in the same DB transaction can share an
    # identical `now()`-derived updated_at, so force a deterministic ordering.
    first_request = db_session.get(Request, first_id)
    assert first_request is not None
    first_request.updated_at = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()

    response = client.get("/requests/mine", headers=_auth_headers(token))

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert ids.index(second_id) < ids.index(first_id)


def test_list_my_requests_requires_authentication(client: TestClient) -> None:
    response = client.get("/requests/mine")

    assert response.status_code == 401


def test_get_request_detail_succeeds_for_owner(client: TestClient) -> None:
    token = _signup_and_login(client, email="detail-owner@example.com")
    request_id = _create_request(client, token)

    response = client.get(f"/requests/{request_id}", headers=_auth_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == request_id
    assert body["documents"] == []
    assert body["status_history"] == []


def test_get_request_detail_succeeds_for_finance_user(
    client: TestClient, db_session: Session
) -> None:
    token = _signup_and_login(client, email="detail-finance@example.com")
    request_id = _create_request(client, token)

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.get(f"/requests/{request_id}", headers=_auth_headers(finance_token))

    assert response.status_code == 200
    assert response.json()["id"] == request_id


def test_get_request_detail_rejects_non_owner_non_finance(client: TestClient) -> None:
    owner_token = _signup_and_login(client, email="detail-owner2@example.com")
    request_id = _create_request(client, owner_token)
    other_token = _signup_and_login(client, email="detail-other@example.com")

    response = client.get(f"/requests/{request_id}", headers=_auth_headers(other_token))

    assert response.status_code == 403


def test_get_request_detail_returns_404_for_unknown_request(client: TestClient) -> None:
    token = _signup_and_login(client, email="detail-404@example.com")

    response = client.get("/requests/999999", headers=_auth_headers(token))

    assert response.status_code == 404
