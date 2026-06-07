"""Async database engine, session factory and per-request RLS context.

Every authenticated request runs inside a transaction that sets
``app.current_user_id`` and ``app.current_role`` via ``set_config(..., true)``
(LOCAL to the transaction), so Postgres RLS policies isolate data per user.
See ``specs/architecture/auth-rls.md``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)

#: RLS role used for unauthenticated flows (registration, login, readiness).
SERVICE_ROLE = "service"


@dataclass(frozen=True)
class RlsContext:
    """The identity injected into Postgres for a request's transaction."""

    user_id: str | None
    role: str


SERVICE_CONTEXT = RlsContext(user_id=None, role=SERVICE_ROLE)


async def _apply_context(session: AsyncSession, ctx: RlsContext) -> None:
    await session.execute(
        text("SELECT set_config('app.current_user_id', :uid, true)"),
        {"uid": ctx.user_id or ""},
    )
    await session.execute(
        text("SELECT set_config('app.current_role', :role, true)"),
        {"role": ctx.role},
    )


@asynccontextmanager
async def session_scope(ctx: RlsContext) -> AsyncIterator[AsyncSession]:
    """Open a transaction, apply the RLS context, and yield a session."""
    async with SessionFactory() as session, session.begin():
        await _apply_context(session, ctx)
        yield session
