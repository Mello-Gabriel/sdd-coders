"""Unit tests for edge cases in verification service."""

from __future__ import annotations

import datetime as dt
import uuid
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from app.core.config import get_settings
from app.core.security import hash_password
from app.services.verification import (
    RESET_TOKEN,
    VERIFY_TOKEN,
    _decode,
    _make_token,
    change_password,
    reset_password,
    verify_email_token,
)


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _token(subject: str, token_type: str, ttl: int = 3600) -> str:
    return _make_token(subject, token_type, ttl, get_settings())


def _mock_session(get_return: object = None) -> MagicMock:
    session = MagicMock()
    session.get = AsyncMock(return_value=get_return)
    session.flush = AsyncMock()
    return session


def test_decode_wrong_type_returns_none() -> None:
    """A verify token should be rejected when expected type is reset."""
    token = _token("sub-id", VERIFY_TOKEN)
    result = _decode(token, RESET_TOKEN, get_settings())
    assert result is None


def test_decode_expired_token_returns_none() -> None:
    """An expired token should return None."""
    settings = get_settings()
    payload = {
        "sub": "user-id",
        "type": VERIFY_TOKEN,
        "exp": int((dt.datetime.now(dt.UTC) - dt.timedelta(seconds=1)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    result = _decode(token, VERIFY_TOKEN, settings)
    assert result is None


def test_decode_valid_token_returns_subject() -> None:
    subject = str(uuid.uuid4())
    token = _token(subject, VERIFY_TOKEN)
    result = _decode(token, VERIFY_TOKEN, get_settings())
    assert result == subject


async def test_verify_email_token_user_not_found_returns_none() -> None:
    token = _token(str(uuid.uuid4()), VERIFY_TOKEN)
    session = _mock_session(get_return=None)
    result = await verify_email_token(session, token)
    assert result is None


async def test_reset_password_user_not_found_returns_none() -> None:
    token = _token(str(uuid.uuid4()), RESET_TOKEN)
    session = _mock_session(get_return=None)
    result = await reset_password(session, token, "newpass123")
    assert result is None


async def test_change_password_user_not_found_returns_false() -> None:
    user = MagicMock()
    user.id = uuid.uuid4()
    session = _mock_session(get_return=None)
    result = await change_password(session, user, "current", "new")
    assert result is False


async def test_change_password_wrong_current_returns_false() -> None:
    user_stub = MagicMock()
    user_stub.id = uuid.uuid4()
    db_user = MagicMock()
    db_user.hashed_password = hash_password("correct-password")
    session = _mock_session(get_return=db_user)
    result = await change_password(session, user_stub, "wrong-password", "new")
    assert result is False
