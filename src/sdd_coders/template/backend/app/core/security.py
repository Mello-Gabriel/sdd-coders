"""Password hashing (Argon2id) and JWT token helpers."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error

from app.core.config import Settings

_hasher = PasswordHasher()

ACCESS_TOKEN = "access"  # noqa: S105 - token *type* label, not a secret
REFRESH_TOKEN = "refresh"  # noqa: S105 - token *type* label, not a secret


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Return ``True`` if the password matches the hash, ``False`` otherwise."""
    try:
        return _hasher.verify(hashed, password)
    except Argon2Error:
        return False


def create_token(
    subject: str,
    token_type: str,
    *,
    settings: Settings,
    jti: str | None = None,
    extra: dict[str, str] | None = None,
) -> str:
    """Create a signed JWT. ``token_type`` is ``access`` or ``refresh``.

    ``extra`` adds non-reserved claims (e.g. the user's ``role`` on access tokens).
    """
    ttl = (
        settings.access_token_ttl_seconds
        if token_type == ACCESS_TOKEN
        else settings.refresh_token_ttl_seconds
    )
    now = dt.datetime.now(tz=dt.UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": jti or str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(seconds=ttl)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, *, settings: Settings) -> dict[str, Any]:
    """Decode and verify a JWT, returning its claims (raises on invalid token)."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
