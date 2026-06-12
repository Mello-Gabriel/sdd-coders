"""Email provider backed by the Resend API."""

from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.services.email.base import EmailMessage

_RESEND_URL = "https://api.resend.com/emails"


class ResendProvider:
    """Sends transactional email via Resend (httpx async client)."""

    async def send(self, message: EmailMessage) -> None:
        settings = get_settings()
        payload: dict[str, object] = {
            "from": settings.email_from,
            "to": [message.to],
            "subject": message.subject,
            "html": message.html,
        }
        if message.text:
            payload["text"] = message.text
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _RESEND_URL,
                json=payload,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            )
            resp.raise_for_status()
