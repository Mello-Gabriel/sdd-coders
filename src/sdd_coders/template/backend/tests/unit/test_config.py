"""Tests for application settings."""

from __future__ import annotations

import pytest
from app.core.config import Settings, get_settings
from pydantic import ValidationError


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.environment == "development"
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_ttl_seconds == 900
    assert settings.refresh_token_ttl_seconds == 604800
    assert settings.cors_origins == []


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    first = get_settings()
    assert get_settings() is first


def test_secret_required_outside_development() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="")


def test_secret_present_outside_development_is_ok() -> None:
    settings = Settings(environment="production", jwt_secret="prod-secret")
    assert settings.environment == "production"
