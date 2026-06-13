"""Integration tests for the strikes-to-ban escalation (services.abuse)."""

from __future__ import annotations

from app.main import app
from app.models.ip_ban import IpBan
from app.services.abuse import FAILURE_THRESHOLD, register_failure
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

TEST_IP = "203.0.113.50"


async def _get_ban(session: AsyncSession, ip: str) -> IpBan | None:
    return (await session.scalars(select(IpBan).where(IpBan.ip_address == ip))).first()


async def test_failures_below_threshold_do_not_ban(owner_session: AsyncSession) -> None:
    for _ in range(FAILURE_THRESHOLD - 1):
        triggered = await register_failure(TEST_IP)
        assert triggered is False
    ban = await _get_ban(owner_session, TEST_IP)
    assert ban is not None
    assert ban.failed_attempts == FAILURE_THRESHOLD - 1
    assert ban.banned_until is None  # accumulating strikes, not yet banned


async def test_threshold_triggers_ban(owner_session: AsyncSession) -> None:
    triggered = [await register_failure(TEST_IP) for _ in range(FAILURE_THRESHOLD)]
    assert triggered[-1] is True
    ban = await _get_ban(owner_session, TEST_IP)
    assert ban is not None
    assert ban.violation_count == 1
    assert ban.banned_until is not None  # first ban on the ladder (5 min)
    assert ban.failed_attempts == 0  # window reset after the ban


async def test_failure_after_ban_restarts_window(owner_session: AsyncSession) -> None:
    # Crossing the threshold bans and clears window_start; the next failure must
    # start a fresh window rather than incrementing a stale counter.
    for _ in range(FAILURE_THRESHOLD):
        await register_failure(TEST_IP)
    triggered = await register_failure(TEST_IP)
    assert triggered is False
    ban = await _get_ban(owner_session, TEST_IP)
    assert ban is not None
    assert ban.failed_attempts == 1
    assert ban.window_start is not None


async def test_ban_from_strikes_blocks_requests() -> None:
    # 127.0.0.1 is what httpx ASGITransport reports as the client.
    for _ in range(FAILURE_THRESHOLD):
        await register_failure("127.0.0.1")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/live")
    assert response.status_code == 429
    assert "Retry-After" in response.headers
