from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.services.email import (
    send_email,
    send_new_request_notification,
    send_status_change_notification,
)


def _signup_and_login(client: TestClient, email: str = "requester@example.com") -> str:
    client.post(
        "/auth/signup",
        json={"name": "Requester", "email": email, "password": "hunter22"},
    )
    response = client.post("/auth/login", json={"email": email, "password": "hunter22"})
    return str(response.json()["access_token"])


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_send_email_sends_via_smtp() -> None:
    with patch("app.services.email.smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        send_email("someone@example.com", "Subject", "Body")

        mock_server.send_message.assert_called_once()


def test_send_new_request_notification_swallows_smtp_errors() -> None:
    with patch("app.services.email.send_email", side_effect=Exception("smtp down")):
        send_new_request_notification(
            requester_name="Jane Doe",
            amount="125.50",
            currency="USD",
            category="Travel",
            request_id=1,
        )


def test_create_request_sends_notification_email(client: TestClient) -> None:
    token = _signup_and_login(client)

    with patch("app.routers.requests.send_new_request_notification") as mock_notify:
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
    mock_notify.assert_called_once()
    _, kwargs = mock_notify.call_args
    assert kwargs["requester_name"] == "Requester"
    assert kwargs["category"] == "Travel"


def test_send_status_change_notification_swallows_smtp_errors() -> None:
    with patch("app.services.email.send_email", side_effect=Exception("smtp down")):
        send_status_change_notification(
            requester_email="jane@example.com",
            request_id=1,
            new_status="approved",
            reason=None,
        )


def test_create_request_succeeds_even_if_email_send_fails(client: TestClient) -> None:
    token = _signup_and_login(client)

    with patch("app.services.email.smtplib.SMTP", side_effect=Exception("smtp down")):
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
