"""IP ban middleware and escalation tests."""

from __future__ import annotations

import datetime as dt

from app.main import app
from app.middleware.ip_ban import ban_duration_for_count, record_ban_violation
from app.models.ip_ban import IpBan
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# --- unit: ban_duration_for_count -----------------------------------------


def test_ban_duration_first_violation() -> None:
    assert ban_duration_for_count(1) == 5


def test_ban_duration_second_violation() -> None:
    assert ban_duration_for_count(2) == 30


def test_ban_duration_third_violation() -> None:
    assert ban_duration_for_count(3) == 4 * 60


def test_ban_duration_fourth_violation() -> None:
    assert ban_duration_for_count(4) == 24 * 60


def test_ban_duration_fifth_and_beyond_is_permanent() -> None:
    assert ban_duration_for_count(5) is None
    assert ban_duration_for_count(10) is None


# --- unit: record_ban_violation -------------------------------------------


async def test_record_creates_first_ban(owner_session: AsyncSession) -> None:
    ban = await record_ban_violation(owner_session, "1.2.3.4", reason="test")
    await owner_session.commit()
    assert ban.ip_address == "1.2.3.4"
    assert ban.violation_count == 1
    assert ban.is_permanent is False
    assert ban.banned_until is not None


async def test_record_escalates_existing_ban(owner_session: AsyncSession) -> None:
    await record_ban_violation(owner_session, "1.2.3.4")
    await record_ban_violation(owner_session, "1.2.3.4")
    await owner_session.commit()
    ban = (await owner_session.scalars(select(IpBan).where(IpBan.ip_address == "1.2.3.4"))).first()
    assert ban is not None
    assert ban.violation_count == 2
    assert ban_duration_for_count(2) == 30


async def test_record_fifth_violation_is_permanent(owner_session: AsyncSession) -> None:
    for _ in range(5):
        await record_ban_violation(owner_session, "9.9.9.9")
    await owner_session.commit()
    ban = (await owner_session.scalars(select(IpBan).where(IpBan.ip_address == "9.9.9.9"))).first()
    assert ban is not None
    assert ban.is_permanent is True
    assert ban.banned_until is None


# --- integration: middleware blocks banned IPs ----------------------------


async def test_middleware_blocks_active_ban(owner_session: AsyncSession) -> None:
    # httpx ASGITransport reports the client as 127.0.0.1.
    ban = IpBan(
        ip_address="127.0.0.1",
        violation_count=1,
        is_permanent=False,
        banned_until=dt.datetime.now(dt.UTC) + dt.timedelta(hours=1),
    )
    owner_session.add(ban)
    await owner_session.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/live")
    assert response.status_code == 429
    assert "Retry-After" in response.headers


async def test_middleware_blocks_permanent_ban(owner_session: AsyncSession) -> None:
    ban = IpBan(
        ip_address="127.0.0.1",
        violation_count=5,
        is_permanent=True,
        banned_until=None,
    )
    owner_session.add(ban)
    await owner_session.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/live")
    assert response.status_code == 403


async def test_middleware_allows_expired_ban(owner_session: AsyncSession) -> None:
    ban = IpBan(
        ip_address="127.0.0.1",
        violation_count=1,
        is_permanent=False,
        banned_until=dt.datetime.now(dt.UTC) - dt.timedelta(minutes=1),
    )
    owner_session.add(ban)
    await owner_session.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/live")
    assert response.status_code == 200


async def test_middleware_allows_unbanned_ip(client: AsyncClient) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200
