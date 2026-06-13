"""Middleware that blocks requests from banned IP addresses."""

from __future__ import annotations

import datetime as dt
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import engine
from app.models.ip_ban import IpBan

# Escalation ladder: violation_count → ban duration in minutes (0 = permanent)
_BAN_LADDER: list[int | None] = [5, 30, 4 * 60, 24 * 60, None]


def _get_client_ip(request: Request) -> str:
    """Return the real client IP, trusting X-Forwarded-For only from localhost."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for and request.client and request.client.host in ("127.0.0.1", "::1"):
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def ban_duration_for_count(violation_count: int) -> int | None:
    """Return ban duration in minutes for a given violation count (None = permanent)."""
    idx = min(violation_count - 1, len(_BAN_LADDER) - 1)
    return _BAN_LADDER[idx]


async def _get_ban(session: AsyncSession, ip: str) -> IpBan | None:
    return (await session.scalars(select(IpBan).where(IpBan.ip_address == ip))).first()


async def record_ban_violation(session: AsyncSession, ip: str, reason: str = "") -> IpBan:
    """Create or escalate an IP ban entry. Returns the updated record."""
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
    ip = _get_client_ip(request)

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
