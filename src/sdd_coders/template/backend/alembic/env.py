"""Alembic environment (async). Migrations run as the database owner role."""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from app.core.config import get_settings
from app.models import Base
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _owner_url_from_dotenv() -> str | None:
    """Read ALEMBIC_DATABASE_URL from the repo-root (or backend-local) .env.

    Migrations create tables, RLS policies and grants, so they must connect as
    the owner role — never as the least-privilege app role. That URL is not an
    ``APP_``-prefixed setting, so ``Settings`` does not pick it up; without this
    a developer running ``alembic`` from ``backend/`` would silently fall back
    to the app role and fail on the first CREATE TABLE.
    """
    for candidate in (Path("../.env"), Path(".env")):
        if not candidate.is_file():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() == "ALEMBIC_DATABASE_URL":
                return value.strip().strip("\"'") or None
    return None


def _database_url() -> str:
    # Prefer an explicit owner URL for migrations; fall back to the app URL.
    return (
        os.environ.get("ALEMBIC_DATABASE_URL")
        or _owner_url_from_dotenv()
        or get_settings().database_url
    )


def _run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def _run_async_migrations() -> None:
    engine = create_async_engine(_database_url(), pool_pre_ping=True)
    async with engine.connect() as connection:
        await connection.run_sync(_run_migrations)
        await connection.commit()
    await engine.dispose()


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(_run_async_migrations())
