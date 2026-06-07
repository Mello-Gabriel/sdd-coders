"""Liveness probe. Readiness (with DB check) is added alongside the database layer."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    """Liveness probe: the process is up and serving."""
    return {"status": "ok"}
