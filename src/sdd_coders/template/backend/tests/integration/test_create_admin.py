"""Tests for the create-admin operational script."""

from __future__ import annotations

import pytest
from app.models import User
from app.scripts import create_admin
from app.scripts.create_admin import _run, main, promote_or_create_admin
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _get(session: AsyncSession, email: str) -> User | None:
    return (await session.scalars(select(User).where(User.email == email))).first()


async def test_creates_new_admin(owner_session: AsyncSession) -> None:
    user = await promote_or_create_admin(owner_session, "new@example.com", "supersecret123")
    await owner_session.commit()
    assert user.role == "admin"
    assert user.email_verified is True


async def test_promotes_existing_user(owner_session: AsyncSession) -> None:
    owner_session.add(
        User(email="existing@example.com", hashed_password="x", role="user", email_verified=False)
    )
    await owner_session.commit()
    user = await promote_or_create_admin(owner_session, "existing@example.com", "ignored123")
    await owner_session.commit()
    assert user.role == "admin"
    assert user.email_verified is True


async def test_run_creates_admin(owner_session: AsyncSession) -> None:
    await _run("run@example.com", "supersecret123")
    user = await _get(owner_session, "run@example.com")
    assert user is not None
    assert user.role == "admin"


def test_main_wrong_args() -> None:
    assert main([]) == 1


def test_main_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    async def fake_run(email: str, password: str) -> None:
        calls.append((email, password))

    # main() drives the real asyncio.run over our stub — no DB, no event-loop clash.
    monkeypatch.setattr(create_admin, "_run", fake_run)
    assert main(["a@example.com", "pw12345678"]) == 0
    assert calls == [("a@example.com", "pw12345678")]
