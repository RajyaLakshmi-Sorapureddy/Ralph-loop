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
    client: TestClient,
    token: str,
    category: str = "Travel",
    description: str = "Taxi",
    expense_date: str = "2026-07-01",
) -> int:
    response = client.post(
        "/requests",
        json={
            "amount": "125.50",
            "currency": "USD",
            "category": category,
            "expense_date": expense_date,
            "description": description,
        },
        headers=_auth_headers(token),
    )
    result: int = response.json()["id"]
    return result


def test_list_all_requests_returns_every_status(client: TestClient, db_session: Session) -> None:
    token = _signup_and_login(client, email="all-req@example.com", name="Alice Requester")
    pending_id = _create_request(client, token)
    approved_id = _create_request(client, token, category="Meals")
    approved_request = db_session.get(Request, approved_id)
    assert approved_request is not None
    approved_request.status = RequestStatus.approved
    db_session.commit()

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.get("/requests", headers=_auth_headers(finance_token))

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert {pending_id, approved_id} <= ids


def test_list_all_requests_filters_by_status(client: TestClient, db_session: Session) -> None:
    token = _signup_and_login(client, email="filter-status@example.com")
    pending_id = _create_request(client, token)
    approved_id = _create_request(client, token)
    approved_request = db_session.get(Request, approved_id)
    assert approved_request is not None
    approved_request.status = RequestStatus.approved
    db_session.commit()

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.get(
        "/requests", params={"status": "approved"}, headers=_auth_headers(finance_token)
    )

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert approved_id in ids
    assert pending_id not in ids


def test_list_all_requests_filters_by_category(client: TestClient, db_session: Session) -> None:
    token = _signup_and_login(client, email="filter-category@example.com")
    travel_id = _create_request(client, token, category="Travel")
    meals_id = _create_request(client, token, category="Meals")

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.get(
        "/requests", params={"category": "Meals"}, headers=_auth_headers(finance_token)
    )

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert meals_id in ids
    assert travel_id not in ids


def test_list_all_requests_filters_by_requester_id(client: TestClient, db_session: Session) -> None:
    token_a = _signup_and_login(client, email="requester-a@example.com", name="Requester A")
    token_b = _signup_and_login(client, email="requester-b@example.com", name="Requester B")
    request_a_id = _create_request(client, token_a)
    request_b_id = _create_request(client, token_b)

    request_a = db_session.get(Request, request_a_id)
    assert request_a is not None
    requester_a_id = request_a.requester_id

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.get(
        "/requests",
        params={"requester_id": requester_a_id},
        headers=_auth_headers(finance_token),
    )

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert request_a_id in ids
    assert request_b_id not in ids


def test_list_all_requests_filters_by_date_range(client: TestClient, db_session: Session) -> None:
    token = _signup_and_login(client, email="filter-date@example.com")
    early_id = _create_request(client, token, expense_date="2026-01-01")
    late_id = _create_request(client, token, expense_date="2026-12-01")

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.get(
        "/requests",
        params={"date_from": "2026-06-01", "date_to": "2026-12-31"},
        headers=_auth_headers(finance_token),
    )

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert late_id in ids
    assert early_id not in ids


def test_list_all_requests_rejects_non_finance_user(client: TestClient) -> None:
    token = _signup_and_login(client, email="non-finance-all@example.com")

    response = client.get("/requests", headers=_auth_headers(token))

    assert response.status_code == 403


def test_list_all_requests_requires_authentication(client: TestClient) -> None:
    response = client.get("/requests")

    assert response.status_code == 401
