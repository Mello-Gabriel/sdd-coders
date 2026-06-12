"""Email provider backed by SMTP (aiosmtplib)."""

from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import get_settings
from app.services.email.base import EmailMessage


class SmtpProvider:
    """Sends transactional email via SMTP using aiosmtplib."""

    async def send(self, message: EmailMessage) -> None:
        settings = get_settings()
        msg = MIMEMultipart("alternative")
        msg["Subject"] = message.subject
        msg["From"] = settings.email_from
        msg["To"] = message.to
        if message.text:
            msg.attach(MIMEText(message.text, "plain"))
        msg.attach(MIMEText(message.html, "html"))
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username or None,
            password=settings.smtp_password or None,
        )
