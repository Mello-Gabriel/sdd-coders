"""Email service: protocol + provider implementations."""

from app.services.email.base import EmailMessage, EmailProvider
from app.services.email.factory import get_email_provider
from app.services.email.memory import MemoryProvider

__all__ = ["EmailMessage", "EmailProvider", "MemoryProvider", "get_email_provider"]
