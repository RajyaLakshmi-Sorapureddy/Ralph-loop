from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Request, RequestStatus, User, UserRole
from app.security import create_access_token, hash_password


def _signup_and_login(client: TestClient, email: str, name: str = "Requester") -> str:
    client.post(
        "/auth/signup",
        json={"name": name, "email": email, "password": "hunter22"},
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


def test_list_pending_requests_includes_pending_and_more_info_needed(
    client: TestClient, db_session: Session
) -> None:
    token = _signup_and_login(client, email="pending-req@example.com", name="Alice Requester")
    pending_id = _create_request(client, token, category="Travel", description="Taxi")
    more_info_id = _create_request(client, token, category="Meals", description="Lunch")

    more_info_request = db_session.get(Request, more_info_id)
    assert more_info_request is not None
    more_info_request.status = RequestStatus.more_info_needed
    db_session.commit()

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.get("/requests/pending", headers=_auth_headers(finance_token))

    assert response.status_code == 200
    body = response.json()
    ids = {item["id"] for item in body}
    assert {pending_id, more_info_id} <= ids

    pending_item = next(item for item in body if item["id"] == pending_id)
    assert pending_item["requester_name"] == "Alice Requester"
    assert pending_item["requester_email"] == "pending-req@example.com"
    assert pending_item["amount"] == "125.50"
    assert pending_item["category"] == "Travel"
    assert pending_item["description"] == "Taxi"
    assert pending_item["expense_date"] == "2026-07-01"
    assert pending_item["status"] == "pending"
    assert "created_at" in pending_item


def test_list_pending_requests_excludes_approved_and_rejected(
    client: TestClient, db_session: Session
) -> None:
    token = _signup_and_login(client, email="approved-req@example.com")
    approved_id = _create_request(client, token)
    rejected_id = _create_request(client, token)

    approved_request = db_session.get(Request, approved_id)
    assert approved_request is not None
    approved_request.status = RequestStatus.approved

    rejected_request = db_session.get(Request, rejected_id)
    assert rejected_request is not None
    rejected_request.status = RequestStatus.rejected
    db_session.commit()

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.get("/requests/pending", headers=_auth_headers(finance_token))

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert approved_id not in ids
    assert rejected_id not in ids


def test_list_pending_requests_rejects_non_finance_user(client: TestClient) -> None:
    token = _signup_and_login(client, email="non-finance@example.com")

    response = client.get("/requests/pending", headers=_auth_headers(token))

    assert response.status_code == 403


def test_list_pending_requests_requires_authentication(client: TestClient) -> None:
    response = client.get("/requests/pending")

    assert response.status_code == 401
