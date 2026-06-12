"""In-memory email provider — captures sent messages for test inspection."""

from __future__ import annotations

from app.services.email.base import EmailMessage


class MemoryProvider:
    """Stores sent messages in a list; never makes network calls."""

    def __init__(self) -> None:
        self.outbox: list[EmailMessage] = []

    async def send(self, message: EmailMessage) -> None:
        self.outbox.append(message)

    def clear(self) -> None:
        self.outbox.clear()
