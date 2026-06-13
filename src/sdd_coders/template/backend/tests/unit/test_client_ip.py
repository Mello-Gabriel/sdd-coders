"""Unit tests for proxy-aware client IP resolution."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from app.core import client_ip as client_ip_module
from app.core.client_ip import _trusted_networks, get_client_ip
from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _reset_caches() -> Iterator[None]:
    get_settings.cache_clear()
    _trusted_networks.cache_clear()
    yield
    get_settings.cache_clear()
    _trusted_networks.cache_clear()


def _request(forwarded_for: str | None = None, client_host: str | None = "1.2.3.4") -> MagicMock:
    request = MagicMock()
    request.headers.get.return_value = forwarded_for
    if client_host is None:
        request.client = None
    else:
        request.client = MagicMock()
        request.client.host = client_host
    return request


def test_direct_untrusted_connection_returns_peer() -> None:
    assert get_client_ip(_request(client_host="5.6.7.8")) == "5.6.7.8"


def test_untrusted_peer_ignores_forwarded_for() -> None:
    # An attacker connecting directly cannot spoof their IP via the header.
    assert get_client_ip(_request(forwarded_for="9.9.9.9", client_host="5.6.7.8")) == "5.6.7.8"


def test_trusted_proxy_uses_rightmost_untrusted_hop() -> None:
    request = _request(forwarded_for="203.0.113.1, 198.51.100.2", client_host="127.0.0.1")
    assert get_client_ip(request) == "198.51.100.2"


def test_trusted_proxy_skips_trusted_hops_in_chain() -> None:
    request = _request(forwarded_for="203.0.113.1, 127.0.0.1", client_host="127.0.0.1")
    assert get_client_ip(request) == "203.0.113.1"


def test_trusted_proxy_without_header_returns_peer() -> None:
    assert get_client_ip(_request(client_host="127.0.0.1")) == "127.0.0.1"


def test_all_hops_trusted_falls_back_to_first() -> None:
    request = _request(forwarded_for="127.0.0.1, ::1", client_host="127.0.0.1")
    assert get_client_ip(request) == "127.0.0.1"


def test_no_client_returns_unknown() -> None:
    assert get_client_ip(_request(client_host=None)) == "unknown"


def test_custom_trusted_proxy_cidr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_TRUSTED_PROXIES", '["10.0.0.0/8"]')
    get_settings.cache_clear()
    _trusted_networks.cache_clear()
    request = _request(forwarded_for="203.0.113.5", client_host="10.1.2.3")
    assert get_client_ip(request) == "203.0.113.5"


def test_malformed_cidr_is_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_TRUSTED_PROXIES", '["not-a-cidr", "127.0.0.1/32"]')
    get_settings.cache_clear()
    _trusted_networks.cache_clear()
    nets = client_ip_module._trusted_networks()
    assert len(nets) == 1


def test_non_ip_forwarded_hop_is_not_trusted() -> None:
    # A garbage XFF token must not be treated as a trusted hop.
    request = _request(forwarded_for="garbage", client_host="127.0.0.1")
    assert get_client_ip(request) == "garbage"
