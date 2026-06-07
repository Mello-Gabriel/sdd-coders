"""Row-Level Security isolation, enforced by Postgres (not the app code)."""

from __future__ import annotations

import uuid

from app.core.db import SERVICE_CONTEXT, RlsContext, session_scope
from app.models import Project, User
from sqlalchemy import select


async def test_user_sees_only_own_projects(seed: dict[str, uuid.UUID]) -> None:
    async with session_scope(RlsContext(user_id=str(seed["a"]), role="user")) as session:
        names = {p.name for p in (await session.scalars(select(Project))).all()}
    assert names == {"A1", "A2"}


async def test_other_user_is_isolated(seed: dict[str, uuid.UUID]) -> None:
    async with session_scope(RlsContext(user_id=str(seed["b"]), role="user")) as session:
        names = {p.name for p in (await session.scalars(select(Project))).all()}
    assert names == {"B1"}


async def test_admin_sees_all_projects(seed: dict[str, uuid.UUID]) -> None:
    async with session_scope(RlsContext(user_id=str(seed["a"]), role="admin")) as session:
        projects = (await session.scalars(select(Project))).all()
    assert len(projects) == 3


async def test_user_sees_only_own_user_row(seed: dict[str, uuid.UUID]) -> None:
    async with session_scope(RlsContext(user_id=str(seed["a"]), role="user")) as session:
        ids = {u.id for u in (await session.scalars(select(User))).all()}
    assert ids == {seed["a"]}


async def test_service_context_reads_all_users_for_auth(seed: dict[str, uuid.UUID]) -> None:
    async with session_scope(SERVICE_CONTEXT) as session:
        emails = {u.email for u in (await session.scalars(select(User))).all()}
    assert emails == {"a@example.com", "b@example.com"}
