"""Cloudflare Turnstile captcha verification."""

from __future__ import annotations

import httpx

from app.core.config import get_settings

_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile(token: str) -> bool:
    """Return True if the Turnstile token is valid.

    When Turnstile is disabled (settings.turnstile_enabled = False), always returns True.
    """
    settings = get_settings()
    if not settings.turnstile_enabled:
        return True
    if not token:
        return False
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _VERIFY_URL,
            data={"secret": settings.turnstile_secret_key, "response": token},
        )
        data = resp.json()
        return bool(data.get("success", False))
