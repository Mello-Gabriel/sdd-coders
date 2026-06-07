"""Authentication services: registration, credential checks and token issuance."""

from __future__ import annotations

import datetime as dt
import uuid

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    ACCESS_TOKEN,
    REFRESH_TOKEN,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import RefreshToken, User


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
    """Return the user if email + password are valid and the account is active."""
    user = await get_user_by_email(session, email)
    if user is None:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
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


async def rotate_tokens(session: AsyncSession, token: str) -> tuple[User, str, str] | None:
    """Validate a refresh token, revoke it, and issue a fresh pair (rotation)."""
    claims = _decode_refresh(token)
    if claims is None:
        return None
    row = await _refresh_row(session, str(claims.get("jti", "")))
    if row is None or row.revoked:
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
