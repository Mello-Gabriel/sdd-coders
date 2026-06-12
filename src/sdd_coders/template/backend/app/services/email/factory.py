"""Email provider factory — selects implementation from config."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.email.base import EmailProvider
from app.services.email.memory import MemoryProvider
from app.services.email.resend import ResendProvider
from app.services.email.smtp import SmtpProvider


@lru_cache(maxsize=1)
def get_email_provider() -> EmailProvider:
    """Return the configured email provider (cached singleton)."""
    settings = get_settings()
    provider = settings.email_provider
    if provider == "resend":
        return ResendProvider()
    if provider == "smtp":
        return SmtpProvider()
    return MemoryProvider()
