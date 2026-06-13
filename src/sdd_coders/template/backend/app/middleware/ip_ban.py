"""Middleware that blocks requests from banned IP addresses."""

from __future__ import annotations

import datetime as dt
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.client_ip import get_client_ip
from app.core.db import engine
from app.models.ip_ban import IpBan

# Escalation ladder: violation_count → ban duration in minutes (0 = permanent)
_BAN_LADDER: list[int | None] = [5, 30, 4 * 60, 24 * 60, None]

# Non-permanent ban rows are pruned once they are this old (LGPD data minimisation
# for IP addresses, which are personal data).
_RETENTION_DAYS = 30


def ban_duration_for_count(violation_count: int) -> int | None:
    """Return ban duration in minutes for a given violation count (None = permanent)."""
    idx = min(violation_count - 1, len(_BAN_LADDER) - 1)
    return _BAN_LADDER[idx]


async def _get_ban(session: AsyncSession, ip: str) -> IpBan | None:
    return (await session.scalars(select(IpBan).where(IpBan.ip_address == ip))).first()


async def _prune_expired(session: AsyncSession) -> None:
    """Delete old non-permanent ban rows (LGPD minimisation of IP data)."""
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=_RETENTION_DAYS)
    await session.execute(
        delete(IpBan).where(IpBan.is_permanent.is_(False), IpBan.updated_at < cutoff)
    )


async def record_ban_violation(session: AsyncSession, ip: str, reason: str = "") -> IpBan:
    """Create or escalate an IP ban entry. Returns the updated record."""
    await _prune_expired(session)
    ban = await _get_ban(session, ip)
    if ban is None:
        ban = IpBan(ip_address=ip, violation_count=1, reason=reason)
        session.add(ban)
    else:
        ban.violation_count += 1
        ban.reason = reason

    duration = ban_duration_for_count(ban.violation_count)
    if duration is None:
        ban.is_permanent = True
        ban.banned_until = None
    else:
        ban.is_permanent = False
        ban.banned_until = dt.datetime.now(dt.UTC) + dt.timedelta(minutes=duration)

    ban.updated_at = dt.datetime.now(dt.UTC)
    await session.flush()
    return ban


async def ip_ban_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Block requests from IPs that are actively banned."""
    ip = get_client_ip(request)

    try:
        async with AsyncSession(engine) as session:
            ban = await _get_ban(session, ip)
    except Exception:  # pragma: no cover
        return await call_next(request)

    if ban is not None:
        if ban.is_permanent:
            return JSONResponse(
                status_code=403,
                content={"detail": "Your IP has been permanently banned."},
            )
        if ban.banned_until and ban.banned_until > dt.datetime.now(dt.UTC):
            retry_after = int((ban.banned_until - dt.datetime.now(dt.UTC)).total_seconds())
            return JSONResponse(
                status_code=429,
                content={"detail": "Your IP is temporarily banned. Try again later."},
                headers={"Retry-After": str(retry_after)},
            )

    return await call_next(request)
