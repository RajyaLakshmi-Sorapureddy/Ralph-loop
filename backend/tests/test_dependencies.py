import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, require_finance_user
from app.models import User, UserRole
from app.security import create_access_token, hash_password


def _make_user(db_session: Session, role: UserRole = UserRole.requester) -> User:
    user = User(
        name="Test User",
        email=f"{role.value}-{id(db_session)}@example.com",
        password_hash=hash_password("hunter22"),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _bearer(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_get_current_user_returns_user_for_valid_token(db_session: Session) -> None:
    user = _make_user(db_session)
    token = create_access_token(subject=str(user.id))

    result = get_current_user(credentials=_bearer(token), db=db_session)

    assert result.id == user.id


def test_get_current_user_raises_401_when_credentials_missing(db_session: Session) -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=None, db=db_session)

    assert exc_info.value.status_code == 401


def test_get_current_user_raises_401_for_invalid_token(db_session: Session) -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=_bearer("not-a-valid-token"), db=db_session)

    assert exc_info.value.status_code == 401


def test_get_current_user_raises_401_for_unknown_user_id(db_session: Session) -> None:
    token = create_access_token(subject="999999")

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=_bearer(token), db=db_session)

    assert exc_info.value.status_code == 401


def test_require_finance_user_allows_finance_role(db_session: Session) -> None:
    user = _make_user(db_session, role=UserRole.finance)

    result = require_finance_user(current_user=user)

    assert result.id == user.id


def test_require_finance_user_rejects_requester_role(db_session: Session) -> None:
    user = _make_user(db_session, role=UserRole.requester)

    with pytest.raises(HTTPException) as exc_info:
        require_finance_user(current_user=user)

    assert exc_info.value.status_code == 403
