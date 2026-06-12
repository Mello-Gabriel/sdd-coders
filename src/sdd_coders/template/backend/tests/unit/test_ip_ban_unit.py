"""Unit tests for ip_ban helper functions."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.middleware.ip_ban import _get_client_ip


def _make_request(
    forwarded_for: str | None = None,
    client_host: str = "1.2.3.4",
) -> MagicMock:
    request = MagicMock()
    request.headers.get.return_value = forwarded_for
    request.client = MagicMock()
    request.client.host = client_host
    return request


def test_get_client_ip_direct_connection() -> None:
    request = _make_request(client_host="5.6.7.8")
    assert _get_client_ip(request) == "5.6.7.8"


def test_get_client_ip_trusted_proxy_uses_forwarded_for() -> None:
    """When request comes from localhost and X-Forwarded-For is set, use the header."""
    request = _make_request(forwarded_for="203.0.113.1, 10.0.0.1", client_host="127.0.0.1")
    assert _get_client_ip(request) == "203.0.113.1"


def test_get_client_ip_untrusted_proxy_ignores_forwarded_for() -> None:
    """X-Forwarded-For is ignored when the direct client is not localhost."""
    request = _make_request(forwarded_for="1.1.1.1", client_host="5.6.7.8")
    assert _get_client_ip(request) == "5.6.7.8"


def test_get_client_ip_no_client_returns_unknown() -> None:
    request = MagicMock()
    request.headers.get.return_value = None
    request.client = None
    assert _get_client_ip(request) == "unknown"
