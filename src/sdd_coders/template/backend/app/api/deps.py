"""Reusable FastAPI dependencies."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SERVICE_CONTEXT, session_scope


async def get_service_session() -> AsyncIterator[AsyncSession]:
    """Yield a session in the ``service`` RLS context (auth and health flows)."""
    async with session_scope(SERVICE_CONTEXT) as session:
        yield session


ServiceSession = Annotated[AsyncSession, Depends(get_service_session)]
