"""Abstract email provider protocol and message dataclass."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class EmailMessage:
    """A simple transactional email."""

    to: str
    subject: str
    html: str
    text: str = ""


class EmailProvider(Protocol):
    """Abstraction over email delivery backends."""

    async def send(self, message: EmailMessage) -> None:
        """Send an email message."""
        ...
