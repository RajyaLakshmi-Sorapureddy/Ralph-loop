import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Request, RequestStatus


@pytest.fixture(autouse=True)
def _isolated_upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    return tmp_path


def _signup_and_login(client: TestClient, email: str = "requester@example.com") -> str:
    client.post(
        "/auth/signup",
        json={"name": "Requester", "email": email, "password": "hunter22"},
    )
    response = client.post("/auth/login", json={"email": email, "password": "hunter22"})
    return str(response.json()["access_token"])


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_request(client: TestClient, token: str) -> int:
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
    result: int = response.json()["id"]
    return result


def _mark_more_info_needed(db_session: Session, request_id: int) -> None:
    request = db_session.get(Request, request_id)
    assert request is not None
    request.status = RequestStatus.more_info_needed
    db_session.commit()


def test_resubmit_updates_description_and_reverts_to_pending(
    client: TestClient, db_session: Session
) -> None:
    token = _signup_and_login(client)
    request_id = _create_request(client, token)
    _mark_more_info_needed(db_session, request_id)

    response = client.post(
        f"/requests/{request_id}/resubmit",
        data={"description": "Taxi to client site, receipt attached"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["description"] == "Taxi to client site, receipt attached"
    assert body["status_history"][-1]["status"] == "pending"
    assert body["status_history"][-1]["reason"] == "Resubmitted by requester"


def test_resubmit_adds_documents(client: TestClient, db_session: Session) -> None:
    token = _signup_and_login(client)
    request_id = _create_request(client, token)
    _mark_more_info_needed(db_session, request_id)

    response = client.post(
        f"/requests/{request_id}/resubmit",
        files=[("files", ("receipt.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf"))],
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["documents"]) == 1
    assert body["documents"][0]["file_name"] == "receipt.pdf"


def test_resubmit_rejects_when_status_is_not_more_info_needed(client: TestClient) -> None:
    token = _signup_and_login(client)
    request_id = _create_request(client, token)

    response = client.post(
        f"/requests/{request_id}/resubmit",
        data={"description": "updated"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 400


def test_resubmit_rejects_non_owner(client: TestClient, db_session: Session) -> None:
    owner_token = _signup_and_login(client, email="owner@example.com")
    request_id = _create_request(client, owner_token)
    _mark_more_info_needed(db_session, request_id)
    other_token = _signup_and_login(client, email="other@example.com")

    response = client.post(
        f"/requests/{request_id}/resubmit",
        data={"description": "updated"},
        headers=_auth_headers(other_token),
    )

    assert response.status_code == 403


def test_resubmit_requires_authentication(client: TestClient) -> None:
    response = client.post("/requests/1/resubmit", data={"description": "updated"})

    assert response.status_code == 401


def test_resubmit_returns_404_for_unknown_request(client: TestClient) -> None:
    token = _signup_and_login(client)

    response = client.post(
        "/requests/999999/resubmit",
        data={"description": "updated"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 404
