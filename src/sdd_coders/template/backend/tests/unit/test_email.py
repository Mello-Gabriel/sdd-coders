"""Email provider unit tests."""

from __future__ import annotations

import httpx
import pytest
import respx
from app.core.config import get_settings
from app.services.email.base import EmailMessage
from app.services.email.factory import get_email_provider
from app.services.email.memory import MemoryProvider
from app.services.email.resend import _RESEND_URL, ResendProvider
from app.services.email.smtp import SmtpProvider

_MSG = EmailMessage(to="a@b.com", subject="Hello", html="<p>Hi</p>", text="Hi")
_MSG_NO_TEXT = EmailMessage(to="a@b.com", subject="Hello", html="<p>Hi</p>", text="")


async def test_memory_provider_stores_message() -> None:
    provider = MemoryProvider()
    await provider.send(_MSG)
    assert len(provider.outbox) == 1
    assert provider.outbox[0].to == "a@b.com"


async def test_memory_provider_clear() -> None:
    provider = MemoryProvider()
    await provider.send(_MSG)
    provider.clear()
    assert len(provider.outbox) == 0


async def test_memory_provider_multiple_messages() -> None:
    provider = MemoryProvider()
    await provider.send(_MSG)
    await provider.send(_MSG)
    assert len(provider.outbox) == 2


@respx.mock
async def test_resend_provider_sends_request(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("APP_EMAIL_FROM", "noreply@app.com")
    get_settings.cache_clear()
    route = respx.post(_RESEND_URL).mock(return_value=httpx.Response(200, json={"id": "abc"}))
    provider = ResendProvider()
    await provider.send(_MSG)
    assert route.called
    get_settings.cache_clear()


@respx.mock
async def test_resend_provider_raises_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("APP_EMAIL_FROM", "noreply@app.com")
    get_settings.cache_clear()
    respx.post(_RESEND_URL).mock(
        return_value=httpx.Response(422, json={"name": "validation_error"})
    )
    provider = ResendProvider()
    with pytest.raises(httpx.HTTPStatusError):
        await provider.send(_MSG)
    get_settings.cache_clear()


@respx.mock
async def test_resend_provider_no_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("APP_EMAIL_FROM", "noreply@app.com")
    get_settings.cache_clear()
    route = respx.post(_RESEND_URL).mock(return_value=httpx.Response(200, json={"id": "abc"}))
    provider = ResendProvider()
    await provider.send(_MSG_NO_TEXT)
    assert route.called
    assert "text" not in route.calls.last.request.content.decode()
    get_settings.cache_clear()


async def test_smtp_provider_sends(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("APP_EMAIL_FROM", "noreply@app.com")
    get_settings.cache_clear()
    sent: list[object] = []

    async def _fake_send(msg: object, **kwargs: object) -> None:
        sent.append(msg)

    monkeypatch.setattr("aiosmtplib.send", _fake_send)
    provider = SmtpProvider()
    await provider.send(_MSG)
    assert len(sent) == 1
    get_settings.cache_clear()


async def test_smtp_provider_no_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("APP_EMAIL_FROM", "noreply@app.com")
    get_settings.cache_clear()

    async def _fake_send(msg: object, **kwargs: object) -> None:
        pass

    monkeypatch.setattr("aiosmtplib.send", _fake_send)
    provider = SmtpProvider()
    await provider.send(_MSG_NO_TEXT)
    get_settings.cache_clear()


def test_factory_returns_memory_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    get_email_provider.cache_clear()
    get_settings.cache_clear()
    provider = get_email_provider()
    assert isinstance(provider, MemoryProvider)
    get_email_provider.cache_clear()
    get_settings.cache_clear()


def test_factory_returns_resend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_EMAIL_PROVIDER", "resend")
    get_email_provider.cache_clear()
    get_settings.cache_clear()
    provider = get_email_provider()
    assert isinstance(provider, ResendProvider)
    get_email_provider.cache_clear()
    get_settings.cache_clear()


def test_factory_returns_smtp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_EMAIL_PROVIDER", "smtp")
    get_email_provider.cache_clear()
    get_settings.cache_clear()
    provider = get_email_provider()
    assert isinstance(provider, SmtpProvider)
    get_email_provider.cache_clear()
    get_settings.cache_clear()
