from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Request, RequestStatusHistory, User, UserRole
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


def _create_request(client: TestClient, token: str) -> int:
    response = client.post(
        "/requests",
        json={
            "amount": "125.50",
            "currency": "USD",
            "category": "Travel",
            "expense_date": "2026-07-01",
            "description": "Taxi",
        },
        headers=_auth_headers(token),
    )
    result: int = response.json()["id"]
    return result


def test_approve_request_updates_status_and_history(
    client: TestClient, db_session: Session
) -> None:
    token = _signup_and_login(client, email="approve-req@example.com")
    request_id = _create_request(client, token)

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.post(
        f"/requests/{request_id}/review",
        json={"action": "approve"},
        headers=_auth_headers(finance_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert len(body["status_history"]) == 1
    assert body["status_history"][0]["status"] == "approved"
    assert body["status_history"][0]["reason"] is None
    assert body["status_history"][0]["changed_by_user_id"] == finance_user.id

    db_session.expire_all()
    request = db_session.get(Request, request_id)
    assert request is not None
    assert request.status.value == "approved"


def test_reject_request_requires_reason(client: TestClient, db_session: Session) -> None:
    token = _signup_and_login(client, email="reject-req@example.com")
    request_id = _create_request(client, token)

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.post(
        f"/requests/{request_id}/review",
        json={"action": "reject"},
        headers=_auth_headers(finance_token),
    )

    assert response.status_code == 400


def test_reject_request_with_reason_succeeds(client: TestClient, db_session: Session) -> None:
    token = _signup_and_login(client, email="reject-reason@example.com")
    request_id = _create_request(client, token)

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.post(
        f"/requests/{request_id}/review",
        json={"action": "reject", "reason": "Missing receipt"},
        headers=_auth_headers(finance_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "rejected"
    assert body["status_history"][0]["reason"] == "Missing receipt"

    history_rows = (
        db_session.query(RequestStatusHistory)
        .filter(RequestStatusHistory.request_id == request_id)
        .all()
    )
    assert len(history_rows) == 1
    assert history_rows[0].reason == "Missing receipt"
    assert history_rows[0].changed_by_user_id == finance_user.id


def test_more_info_request_requires_reason(client: TestClient, db_session: Session) -> None:
    token = _signup_and_login(client, email="more-info-req@example.com")
    request_id = _create_request(client, token)

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.post(
        f"/requests/{request_id}/review",
        json={"action": "more_info"},
        headers=_auth_headers(finance_token),
    )

    assert response.status_code == 400


def test_more_info_request_with_reason_succeeds(client: TestClient, db_session: Session) -> None:
    token = _signup_and_login(client, email="more-info-reason@example.com")
    request_id = _create_request(client, token)

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.post(
        f"/requests/{request_id}/review",
        json={"action": "more_info", "reason": "Need itemized receipt"},
        headers=_auth_headers(finance_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "more_info_needed"
    assert body["status_history"][0]["reason"] == "Need itemized receipt"


def test_review_rejects_non_finance_user(client: TestClient) -> None:
    token = _signup_and_login(client, email="non-finance-review@example.com")
    request_id = _create_request(client, token)

    response = client.post(
        f"/requests/{request_id}/review",
        json={"action": "approve"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 403


def test_review_requires_authentication(client: TestClient, db_session: Session) -> None:
    token = _signup_and_login(client, email="review-unauth@example.com")
    request_id = _create_request(client, token)

    response = client.post(f"/requests/{request_id}/review", json={"action": "approve"})

    assert response.status_code == 401


def test_review_unknown_request_returns_404(client: TestClient, db_session: Session) -> None:
    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.post(
        "/requests/999999/review",
        json={"action": "approve"},
        headers=_auth_headers(finance_token),
    )

    assert response.status_code == 404


def test_review_sends_status_change_notification(client: TestClient, db_session: Session) -> None:
    token = _signup_and_login(client, email="notify-review@example.com")
    request_id = _create_request(client, token)

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    with patch("app.routers.requests.send_status_change_notification") as mock_notify:
        response = client.post(
            f"/requests/{request_id}/review",
            json={"action": "reject", "reason": "Missing receipt"},
            headers=_auth_headers(finance_token),
        )

    assert response.status_code == 200
    mock_notify.assert_called_once()
    _, kwargs = mock_notify.call_args
    assert kwargs["requester_email"] == "notify-review@example.com"
    assert kwargs["new_status"] == "rejected"
    assert kwargs["reason"] == "Missing receipt"


def test_review_succeeds_even_if_email_send_fails(client: TestClient, db_session: Session) -> None:
    token = _signup_and_login(client, email="review-email-fails@example.com")
    request_id = _create_request(client, token)

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    with patch("app.services.email.smtplib.SMTP", side_effect=Exception("smtp down")):
        response = client.post(
            f"/requests/{request_id}/review",
            json={"action": "approve"},
            headers=_auth_headers(finance_token),
        )

    assert response.status_code == 200
