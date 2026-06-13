"""Turnstile captcha verification unit tests (respx mocks)."""

from __future__ import annotations

from collections.abc import Generator

import httpx
import pytest
import respx
from app.core.config import get_settings
from app.services.turnstile import _VERIFY_URL, verify_turnstile


@pytest.fixture(autouse=True)
def _reset_settings(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def test_verify_disabled_always_true() -> None:
    result = await verify_turnstile("any-token")
    assert result is True


async def test_verify_empty_token_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_TURNSTILE_ENABLED", "true")
    monkeypatch.setenv("APP_TURNSTILE_SECRET_KEY", "secret")
    get_settings.cache_clear()
    result = await verify_turnstile("")
    assert result is False


@respx.mock
async def test_verify_valid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_TURNSTILE_ENABLED", "true")
    monkeypatch.setenv("APP_TURNSTILE_SECRET_KEY", "secret")
    get_settings.cache_clear()
    respx.post(_VERIFY_URL).mock(return_value=httpx.Response(200, json={"success": True}))
    result = await verify_turnstile("valid-token")
    assert result is True


@respx.mock
async def test_verify_invalid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_TURNSTILE_ENABLED", "true")
    monkeypatch.setenv("APP_TURNSTILE_SECRET_KEY", "secret")
    get_settings.cache_clear()
    respx.post(_VERIFY_URL).mock(
        return_value=httpx.Response(
            200, json={"success": False, "error-codes": ["invalid-input-response"]}
        )
    )
    result = await verify_turnstile("bad-token")
    assert result is False
