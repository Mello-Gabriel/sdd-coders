"""Unit tests for rate limiter storage URI selection."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from app.core.config import get_settings
from app.core.limiter import _get_storage_uri


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_storage_uri_defaults_to_memory() -> None:
    assert _get_storage_uri() == "memory://"


def test_storage_uri_returns_redis_url_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_REDIS_URL", "redis://localhost:6379/0")
    get_settings.cache_clear()
    assert _get_storage_uri() == "redis://localhost:6379/0"
