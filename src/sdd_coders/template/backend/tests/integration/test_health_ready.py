"""Readiness probe hits the database through the app engine (app_user)."""

from __future__ import annotations

from httpx import AsyncClient


async def test_ready_returns_ready(client: AsyncClient) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
