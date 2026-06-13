"""Authentication services: registration, credential checks and token issuance."""

from __future__ import annotations

import datetime as dt
import uuid

import jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import SERVICE_CONTEXT, session_scope
from app.core.security import (
    ACCESS_TOKEN,
    REFRESH_TOKEN,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import RefreshToken, User

# A fixed valid Argon2 hash used to equalize timing when the email is unknown,
# so an attacker cannot distinguish "no such user" from "wrong password".
_DUMMY_HASH = hash_password("timing-equalization-placeholder")


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Return the user with this email, or ``None``."""
    return (await session.scalars(select(User).where(User.email == email))).first()


async def register_user(session: AsyncSession, email: str, password: str) -> User:
    """Create and flush a new user (password hashed with Argon2)."""
    user = User(email=email, hashed_password=hash_password(password), role="user")
    session.add(user)
    await session.flush()
    return user


async def authenticate(session: AsyncSession, email: str, password: str) -> User | None:
    """Return the user if email + password are valid and the account is active.

    Always runs a password verification (against a dummy hash when the email is
    unknown) so response timing does not reveal whether an account exists.
    """
    user = await get_user_by_email(session, email)
    password_ok = verify_password(password, user.hashed_password if user else _DUMMY_HASH)
    if user is None or not password_ok or not user.is_active:
        return None
    return user


async def issue_tokens(session: AsyncSession, user: User) -> tuple[str, str]:
    """Mint an access + refresh token pair and persist the refresh token."""
    settings = get_settings()
    jti = str(uuid.uuid4())
    access = create_token(str(user.id), ACCESS_TOKEN, settings=settings, extra={"role": user.role})
    refresh = create_token(str(user.id), REFRESH_TOKEN, settings=settings, jti=jti)
    expires_at = dt.datetime.now(tz=dt.UTC) + dt.timedelta(
        seconds=settings.refresh_token_ttl_seconds
    )
    session.add(RefreshToken(jti=jti, user_id=user.id, expires_at=expires_at))
    return access, refresh


async def _refresh_row(session: AsyncSession, jti: str) -> RefreshToken | None:
    return (await session.scalars(select(RefreshToken).where(RefreshToken.jti == jti))).first()


def _decode_refresh(token: str) -> dict[str, object] | None:
    try:
        claims = decode_token(token, settings=get_settings())
    except jwt.PyJWTError:
        return None
    if claims.get("type") != REFRESH_TOKEN:
        return None
    return claims


async def revoke_all_refresh(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Revoke every refresh token for a user (password change / theft response)."""
    await session.execute(
        update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True)
    )


async def _revoke_all_refresh_committed(user_id: uuid.UUID) -> None:
    """Revoke a user's tokens in a dedicated, immediately-committed transaction.

    The reuse-detection path returns None and the caller then responds 401, which
    rolls back the request's own transaction — so the revocation must commit on
    its own to actually stick. Runs in the service RLS context: refresh_tokens has
    RLS enabled, so without a context the UPDATE would match zero rows.
    """
    async with session_scope(SERVICE_CONTEXT) as session:
        await revoke_all_refresh(session, user_id)


async def rotate_tokens(session: AsyncSession, token: str) -> tuple[User, str, str] | None:
    """Validate a refresh token, revoke it, and issue a fresh pair (rotation)."""
    claims = _decode_refresh(token)
    row = await _refresh_row(session, str(claims.get("jti", ""))) if claims else None
    if row is None:
        return None
    if row.revoked:
        # A revoked token being presented again means the rotation chain was
        # replayed — presume the token was stolen and burn the whole family.
        await _revoke_all_refresh_committed(row.user_id)
        return None
    if row.expires_at < dt.datetime.now(tz=dt.UTC):
        return None
    row.revoked = True
    user = await session.get(User, row.user_id)
    if user is None:  # pragma: no cover - FK guarantees the token's user exists
        return None
    if not user.is_active:
        return None
    access, refresh = await issue_tokens(session, user)
    return user, access, refresh


async def revoke_refresh(session: AsyncSession, token: str) -> None:
    """Best-effort revocation of a refresh token (used on logout)."""
    claims = _decode_refresh(token)
    if claims is None:
        return
    row = await _refresh_row(session, str(claims.get("jti", "")))
    if row is not None:
        row.revoked = True
