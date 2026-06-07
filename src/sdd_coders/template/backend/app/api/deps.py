"""Reusable FastAPI dependencies."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import SERVICE_CONTEXT, RlsContext, session_scope
from app.core.security import ACCESS_TOKEN, decode_token
from app.models import User

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


async def get_service_session() -> AsyncIterator[AsyncSession]:
    """Yield a session in the ``service`` RLS context (auth and health flows)."""
    async with session_scope(SERVICE_CONTEXT) as session:
        yield session


ServiceSession = Annotated[AsyncSession, Depends(get_service_session)]


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(request: Request) -> User:
    """Resolve the authenticated user from the access-token cookie."""
    token = request.cookies.get(ACCESS_COOKIE)
    if token is None:
        raise _credentials_exception()
    try:
        claims = decode_token(token, settings=get_settings())
    except jwt.PyJWTError as exc:
        raise _credentials_exception() from exc
    if claims.get("type") != ACCESS_TOKEN:
        raise _credentials_exception()
    user_id = str(claims.get("sub", ""))
    role = str(claims.get("role", "user"))
    async with session_scope(RlsContext(user_id=user_id, role=role)) as session:
        user = await session.get(User, uuid.UUID(user_id))
        if user is None:
            raise _credentials_exception()
        if not user.is_active:
            raise _credentials_exception()
        return user


CurrentUser = Annotated[User, Depends(get_current_user)]
