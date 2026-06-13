"""Email verification and password reset token management."""

from __future__ import annotations

import datetime as dt
import hashlib
from typing import Any

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import decode_token, hash_password, verify_password
from app.models.user import User
from app.services.auth import get_user_by_email, revoke_all_refresh
from app.services.email import EmailMessage, get_email_provider

VERIFY_TOKEN = "email_verify"  # noqa: S105 - token type label
RESET_TOKEN = "password_reset"  # noqa: S105 - token type label

_VERIFY_TTL = 24 * 60 * 60
_RESET_TTL = 60 * 60


def _password_fingerprint(hashed_password: str) -> str:
    """A short digest of the password hash, embedded in reset tokens.

    Because it changes whenever the password changes, a reset token becomes
    single-use: once the password is set (or changed by any means) the embedded
    fingerprint no longer matches and the token is rejected.
    """
    return hashlib.sha256(hashed_password.encode()).hexdigest()[:16]


def _make_token(
    subject: str,
    token_type: str,
    ttl: int,
    settings: Settings,
    extra: dict[str, Any] | None = None,
) -> str:
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "exp": int((dt.datetime.now(dt.UTC) + dt.timedelta(seconds=ttl)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_claims(token: str, expected_type: str, settings: Settings) -> dict[str, Any] | None:
    """Decode a one-time token and return its claims, or None if invalid."""
    try:
        claims = decode_token(token, settings=settings)
    except jwt.PyJWTError:
        return None
    if claims.get("type") != expected_type:
        return None
    return claims


def _decode(token: str, expected_type: str, settings: Settings) -> str | None:
    """Decode a one-time token and return the subject, or None if invalid."""
    claims = _decode_claims(token, expected_type, settings)
    if claims is None:
        return None
    sub = claims.get("sub")
    return str(sub) if sub is not None else None


async def send_verification_email(user: User) -> None:
    """Generate a verify token and send the confirmation email."""
    settings = get_settings()
    token = _make_token(str(user.id), VERIFY_TOKEN, _VERIFY_TTL, settings)
    link = f"{settings.frontend_url}/auth/verify-email?token={token}"
    await get_email_provider().send(
        EmailMessage(
            to=user.email,
            subject="Confirme seu e-mail",
            html=f"<p>Confirme seu e-mail: <a href='{link}'>{link}</a></p>",
            text=f"Confirme seu e-mail: {link}",
        )
    )


async def verify_email_token(session: AsyncSession, token: str) -> User | None:
    """Validate a verify token and mark the user's email as verified."""
    sub = _decode(token, VERIFY_TOKEN, get_settings())
    if sub is None:
        return None
    user = await session.get(User, sub)
    if user is None:
        return None
    user.email_verified = True
    await session.flush()
    return user


async def send_password_reset_email(session: AsyncSession, email: str) -> None:
    """Generate a reset token and email it — silently no-ops if user not found."""
    user = await get_user_by_email(session, email)
    if user is None:
        return
    settings = get_settings()
    token = _make_token(
        str(user.id),
        RESET_TOKEN,
        _RESET_TTL,
        settings,
        extra={"pwd": _password_fingerprint(user.hashed_password)},
    )
    link = f"{settings.frontend_url}/auth/reset-password?token={token}"
    await get_email_provider().send(
        EmailMessage(
            to=user.email,
            subject="Redefinir senha",
            html=f"<p>Redefina sua senha: <a href='{link}'>{link}</a></p>",
            text=f"Redefina sua senha: {link}",
        )
    )


async def reset_password(session: AsyncSession, token: str, new_password: str) -> User | None:
    """Validate a reset token and update the user's password (single-use).

    The token carries a fingerprint of the password hash it was minted against;
    if the hash has since changed (token already used, or password changed by
    other means) the fingerprint no longer matches and the token is rejected.
    On success every existing session is revoked.
    """
    claims = _decode_claims(token, RESET_TOKEN, get_settings())
    if claims is None or claims.get("sub") is None:
        return None
    user = await session.get(User, str(claims["sub"]))
    if user is None:
        return None
    if claims.get("pwd") != _password_fingerprint(user.hashed_password):
        return None
    user.hashed_password = hash_password(new_password)
    await revoke_all_refresh(session, user.id)
    await session.flush()
    return user


async def change_password(
    session: AsyncSession, user: User, current_password: str, new_password: str
) -> bool:
    """Verify the current password and update to the new one. Returns False if wrong."""
    # Reload the user in this session to avoid detached-instance writes.
    db_user = await session.get(User, user.id)
    if db_user is None:
        return False
    if not verify_password(current_password, db_user.hashed_password):
        return False
    db_user.hashed_password = hash_password(new_password)
    await revoke_all_refresh(session, db_user.id)
    await session.flush()
    return True
