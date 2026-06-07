"""Liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import ServiceSession

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    """Liveness probe: the process is up and serving."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(session: ServiceSession) -> dict[str, str]:
    """Readiness probe: the database connection is usable."""
    await session.execute(text("SELECT 1"))
    return {"status": "ready"}
