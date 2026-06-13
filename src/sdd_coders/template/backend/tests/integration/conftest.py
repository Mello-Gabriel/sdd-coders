"""Integration-test fixtures: schema build (as owner), isolation, seeding, client.

The schema (tables + RLS policies + grants + app_user role) is built once per
session as the database owner. Tests then exercise the app's engine, which
connects as ``app_user`` (no BYPASSRLS), so RLS is genuinely enforced.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from app.core.db import engine
from app.db.rls import apply_rls, ensure_app_role, grant_app_privileges
from app.main import app
from app.models import Base, Project, User
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

OWNER_URL = os.environ.get(
    "TEST_OWNER_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:55432/app",
)


async def fetch_user_id(session: AsyncSession, email: str) -> str:
    """Look up a user's id by email.

    /auth/register returns a generic 202 (anti-enumeration), so tests resolve
    the freshly created user through the owner session instead of the response.
    """
    user = (await session.scalars(select(User).where(User.email == email))).one()
    return str(user.id)


async def _build_schema() -> None:
    owner = create_async_engine(OWNER_URL, poolclass=NullPool)
    try:
        async with owner.begin() as conn:
            await conn.run_sync(ensure_app_role)
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(apply_rls)
            await conn.run_sync(grant_app_privileges)
    finally:
        await owner.dispose()


@pytest.fixture(scope="session", autouse=True)
def _schema() -> None:
    asyncio.run(_build_schema())


@pytest_asyncio.fixture(autouse=True)
async def _isolate() -> AsyncIterator[None]:
    """Dispose the app engine and truncate all tables after each test."""
    yield
    await engine.dispose()
    owner = create_async_engine(OWNER_URL, poolclass=NullPool)
    try:
        async with owner.begin() as conn:
            await conn.execute(
                text(
                    "TRUNCATE users, projects, refresh_tokens, audit_log, ip_bans,"
                    " consents RESTART IDENTITY CASCADE"
                )
            )
    finally:
        await owner.dispose()


@pytest_asyncio.fixture
async def seed() -> dict[str, uuid.UUID]:
    """Insert two users (A, B) with projects, bypassing RLS as the owner role."""
    owner = create_async_engine(OWNER_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(owner, expire_on_commit=False)
    try:
        async with session_factory() as session, session.begin():
            user_a = User(email="a@example.com", hashed_password="x", role="user")
            user_b = User(email="b@example.com", hashed_password="x", role="user")
            session.add_all([user_a, user_b])
            await session.flush()
            session.add_all(
                [
                    Project(owner_id=user_a.id, name="A1"),
                    Project(owner_id=user_a.id, name="A2"),
                    Project(owner_id=user_b.id, name="B1"),
                ]
            )
        ids = {"a": user_a.id, "b": user_b.id}
    finally:
        await owner.dispose()
    return ids


@pytest_asyncio.fixture
async def owner_session() -> AsyncIterator[AsyncSession]:
    """A session as the database owner (bypasses RLS) for test mutations."""
    owner = create_async_engine(OWNER_URL, poolclass=NullPool)
    factory = async_sessionmaker(owner, expire_on_commit=False)
    try:
        async with factory() as session:
            yield session
    finally:
        await owner.dispose()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
