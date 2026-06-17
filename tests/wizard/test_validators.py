"""Tests for the pure input validators."""

from __future__ import annotations

import pytest

from sdd_coders.wizard import validators


@pytest.mark.parametrize("value", ["my-app", "a1", "app-2-x"])
def test_validate_slug_accepts(value: str) -> None:
    assert validators.validate_slug(value) == value


@pytest.mark.parametrize("value", ["../evil", "App", "1abc", "a", "x" * 70, "a_b"])
def test_validate_slug_rejects(value: str) -> None:
    with pytest.raises(ValueError, match="lowercase"):
        validators.validate_slug(value)


def test_validate_domain_normalizes() -> None:
    assert validators.validate_domain("  Example.COM. ") == "example.com"


@pytest.mark.parametrize("value", ["nope", "http://example.com", "example", "a..b.com"])
def test_validate_domain_rejects(value: str) -> None:
    with pytest.raises(ValueError, match="bare domain"):
        validators.validate_domain(value)


def test_validate_url_strips_trailing_slash() -> None:
    assert validators.validate_url("https://coolify.example.com/") == "https://coolify.example.com"


def test_validate_url_rejects_without_scheme() -> None:
    with pytest.raises(ValueError, match="full URL"):
        validators.validate_url("coolify.example.com")


def test_validate_ip_accepts_v4_and_v6() -> None:
    assert validators.validate_ip(" 203.0.113.5 ") == "203.0.113.5"
    assert validators.validate_ip("::1") == "::1"


def test_validate_ip_rejects() -> None:
    with pytest.raises(ValueError, match="valid IP"):
        validators.validate_ip("999.1.1.1")


def test_validate_ga_id() -> None:
    assert validators.validate_ga_id("g-abc123") == "G-ABC123"
    with pytest.raises(ValueError, match="GA4"):
        validators.validate_ga_id("UA-123")


def test_validate_nonempty() -> None:
    assert validators.validate_nonempty("  token ") == "token"
    with pytest.raises(ValueError, match="required"):
        validators.validate_nonempty("   ")
