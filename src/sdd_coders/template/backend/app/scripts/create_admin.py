"""Create or promote an admin user.

Usage::

    uv run python -m app.scripts.create_admin <email> <password>

Idempotent: if the email already exists the account is promoted to ``admin`` and
marked verified; otherwise a new verified admin is created. Runs in the service
RLS context so it works with the least-privilege ``app_user`` role.
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SERVICE_CONTEXT, session_scope
from app.core.security import hash_password
from app.models import User
from app.services.auth import get_user_by_email

_EXPECTED_ARGS = 2  # email + password


async def promote_or_create_admin(session: AsyncSession, email: str, password: str) -> User:
    """Create a verified admin, or promote an existing user to admin."""
    user = await get_user_by_email(session, email)
    if user is None:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            role="admin",
            email_verified=True,
        )
        session.add(user)
        await session.flush()
        return user
    user.role = "admin"
    user.email_verified = True
    await session.flush()
    return user


async def _run(email: str, password: str) -> None:
    async with session_scope(SERVICE_CONTEXT) as session:
        user = await promote_or_create_admin(session, email, password)
        print(f"Admin ready: {user.email} ({user.id})")


def main(argv: list[str]) -> int:
    """CLI entry point. Returns a process exit code."""
    if len(argv) != _EXPECTED_ARGS:
        print("Usage: python -m app.scripts.create_admin <email> <password>", file=sys.stderr)
        return 1
    asyncio.run(_run(argv[0], argv[1]))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via the module CLI
    raise SystemExit(main(sys.argv[1:]))
