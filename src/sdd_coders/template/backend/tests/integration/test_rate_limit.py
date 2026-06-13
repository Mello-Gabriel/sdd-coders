"""Integration test proving rate limiting is actually wired in.

The rest of the suite disables the limiter (it would make tests flaky); here we
turn it on for one route and confirm the limit is enforced. This is the test the
shipped template lacked — limits were declared but never exercised.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from app.core.limiter import limiter
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def rate_limited_client() -> AsyncIterator[AsyncClient]:
    limiter.enabled = True
    limiter.reset()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            yield http_client
    finally:
        limiter.reset()
        limiter.enabled = False


async def test_request_verification_is_rate_limited(rate_limited_client: AsyncClient) -> None:
    # /auth/request-verification is limited to 3/hour and always returns 204 for
    # an unknown email (no IP-ban strikes), so it isolates rate limiting cleanly.
    payload = {"email": "ghost@example.com"}
    statuses = [
        (await rate_limited_client.post("/auth/request-verification", json=payload)).status_code
        for _ in range(4)
    ]
    assert statuses[:3] == [204, 204, 204]
    assert statuses[3] == 429
