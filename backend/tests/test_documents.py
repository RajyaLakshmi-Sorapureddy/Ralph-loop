import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User, UserRole
from app.security import create_access_token, hash_password


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
            "description": "Taxi to client site",
        },
        headers=_auth_headers(token),
    )
    result: int = response.json()["id"]
    return result


def test_upload_document_succeeds_for_owner(client: TestClient, tmp_path: Path) -> None:
    token = _signup_and_login(client)
    request_id = _create_request(client, token)

    response = client.post(
        f"/requests/{request_id}/documents",
        files=[("files", ("receipt.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf"))],
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body) == 1
    assert body[0]["file_name"] == "receipt.pdf"
    assert body[0]["file_size"] == len(b"%PDF-1.4 fake")
    assert (tmp_path / str(request_id) / "receipt.pdf").exists()


def test_upload_document_accepts_multiple_files(client: TestClient) -> None:
    token = _signup_and_login(client)
    request_id = _create_request(client, token)

    response = client.post(
        f"/requests/{request_id}/documents",
        files=[
            ("files", ("receipt.pdf", io.BytesIO(b"pdf-bytes"), "application/pdf")),
            ("files", ("photo.jpg", io.BytesIO(b"jpg-bytes"), "image/jpeg")),
        ],
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    assert len(response.json()) == 2


def test_upload_document_rejects_disallowed_file_type(client: TestClient) -> None:
    token = _signup_and_login(client)
    request_id = _create_request(client, token)

    response = client.post(
        f"/requests/{request_id}/documents",
        files=[("files", ("malware.exe", io.BytesIO(b"binary"), "application/octet-stream"))],
        headers=_auth_headers(token),
    )

    assert response.status_code == 400


def test_upload_document_rejects_file_exceeding_size_limit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "max_file_size_mb", 0)
    token = _signup_and_login(client)
    request_id = _create_request(client, token)

    response = client.post(
        f"/requests/{request_id}/documents",
        files=[("files", ("receipt.pdf", io.BytesIO(b"more than zero bytes"), "application/pdf"))],
        headers=_auth_headers(token),
    )

    assert response.status_code == 400


def test_upload_document_rejects_exceeding_file_count_limit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "max_files_per_request", 1)
    token = _signup_and_login(client)
    request_id = _create_request(client, token)

    response = client.post(
        f"/requests/{request_id}/documents",
        files=[
            ("files", ("receipt1.pdf", io.BytesIO(b"a"), "application/pdf")),
            ("files", ("receipt2.pdf", io.BytesIO(b"b"), "application/pdf")),
        ],
        headers=_auth_headers(token),
    )

    assert response.status_code == 400


def test_upload_document_rejects_non_owner(client: TestClient) -> None:
    owner_token = _signup_and_login(client, email="owner@example.com")
    request_id = _create_request(client, owner_token)
    other_token = _signup_and_login(client, email="other@example.com")

    response = client.post(
        f"/requests/{request_id}/documents",
        files=[("files", ("receipt.pdf", io.BytesIO(b"pdf-bytes"), "application/pdf"))],
        headers=_auth_headers(other_token),
    )

    assert response.status_code == 403


def test_download_document_succeeds_for_owner(client: TestClient) -> None:
    token = _signup_and_login(client)
    request_id = _create_request(client, token)
    upload_response = client.post(
        f"/requests/{request_id}/documents",
        files=[("files", ("receipt.pdf", io.BytesIO(b"pdf-bytes"), "application/pdf"))],
        headers=_auth_headers(token),
    )
    doc_id = upload_response.json()[0]["id"]

    response = client.get(
        f"/requests/{request_id}/documents/{doc_id}",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.content == b"pdf-bytes"


def test_download_document_succeeds_for_finance_user(
    client: TestClient, db_session: Session
) -> None:
    token = _signup_and_login(client)
    request_id = _create_request(client, token)
    upload_response = client.post(
        f"/requests/{request_id}/documents",
        files=[("files", ("receipt.pdf", io.BytesIO(b"pdf-bytes"), "application/pdf"))],
        headers=_auth_headers(token),
    )
    doc_id = upload_response.json()[0]["id"]

    finance_user = _make_finance_user(db_session)
    finance_token = create_access_token(subject=str(finance_user.id))

    response = client.get(
        f"/requests/{request_id}/documents/{doc_id}",
        headers=_auth_headers(finance_token),
    )

    assert response.status_code == 200


def test_download_document_rejects_non_owner_non_finance(client: TestClient) -> None:
    owner_token = _signup_and_login(client, email="owner2@example.com")
    request_id = _create_request(client, owner_token)
    upload_response = client.post(
        f"/requests/{request_id}/documents",
        files=[("files", ("receipt.pdf", io.BytesIO(b"pdf-bytes"), "application/pdf"))],
        headers=_auth_headers(owner_token),
    )
    doc_id = upload_response.json()[0]["id"]

    other_token = _signup_and_login(client, email="other2@example.com")

    response = client.get(
        f"/requests/{request_id}/documents/{doc_id}",
        headers=_auth_headers(other_token),
    )

    assert response.status_code == 403


def test_download_document_returns_404_for_unknown_document(client: TestClient) -> None:
    token = _signup_and_login(client)
    request_id = _create_request(client, token)

    response = client.get(
        f"/requests/{request_id}/documents/999999",
        headers=_auth_headers(token),
    )

    assert response.status_code == 404
