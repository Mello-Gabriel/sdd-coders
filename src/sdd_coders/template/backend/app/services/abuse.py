"""Abuse tracking: accumulate failed attempts per IP and escalate to a ban.

A single bad password should not ban anyone. We count failures inside a sliding
window and, once the threshold is crossed, hand off to the escalating IP-ban
ladder (``app.middleware.ip_ban``).

``register_failure`` opens its **own** transaction and commits immediately: the
auth routes call it right before raising an ``HTTPException``, and the request's
own transaction is rolled back on that exception — so the strike must be durable
independently of the request.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import engine
from app.middleware.ip_ban import record_ban_violation
from app.models.ip_ban import IpBan

#: Failures allowed within the window before a ban is issued.
FAILURE_THRESHOLD = 5
#: Length of the sliding window for counting failures.
WINDOW = dt.timedelta(minutes=15)


async def register_failure(ip: str, reason: str = "") -> bool:
    """Record one failed attempt from ``ip``. Returns True if it triggered a ban.

    Best-effort: any database error is swallowed so abuse tracking can never
    take down the auth flow itself.
    """
    try:
        async with AsyncSession(engine) as session, session.begin():
            return await _register_failure(session, ip, reason)
    except Exception:  # pragma: no cover - defensive; never break auth on tracking
        return False


async def _register_failure(session: AsyncSession, ip: str, reason: str) -> bool:
    now = dt.datetime.now(dt.UTC)
    ban = (await session.scalars(select(IpBan).where(IpBan.ip_address == ip))).first()

    if ban is None:
        session.add(IpBan(ip_address=ip, violation_count=0, failed_attempts=1, window_start=now))
        await session.flush()
        return False

    # Restart the window if it has elapsed (or was never started).
    if ban.window_start is None or now - ban.window_start > WINDOW:
        ban.window_start = now
        ban.failed_attempts = 1
        await session.flush()
        return False

    ban.failed_attempts += 1
    if ban.failed_attempts >= FAILURE_THRESHOLD:
        ban.failed_attempts = 0
        ban.window_start = None
        await record_ban_violation(session, ip, reason=reason or "failed attempts threshold")
        return True

    await session.flush()
    return False
