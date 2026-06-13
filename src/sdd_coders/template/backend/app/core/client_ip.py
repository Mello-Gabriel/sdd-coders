"""Resolve the real client IP, trusting ``X-Forwarded-For`` only from proxies.

A naive ``X-Forwarded-For`` read lets any client spoof its IP (and thus dodge
rate limits and IP bans). We only believe the header when the *direct* peer is a
configured trusted proxy, and we walk the header right-to-left, skipping trusted
hops, to find the first address the infrastructure actually observed.
"""

from __future__ import annotations

import ipaddress
from functools import lru_cache

from fastapi import Request

from app.core.config import get_settings

_UNKNOWN = "unknown"


@lru_cache(maxsize=1)
def _trusted_networks() -> tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]:
    nets: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for cidr in get_settings().trusted_proxies:
        try:
            nets.append(ipaddress.ip_network(cidr, strict=False))
        except ValueError:  # pragma: no cover - guarded by config, defensive only
            continue
    return tuple(nets)


def _is_trusted(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in net for net in _trusted_networks())


def get_client_ip(request: Request) -> str:
    """Return the best-effort real client IP for rate limiting and IP bans."""
    if request.client is None:
        return _UNKNOWN
    direct = request.client.host

    # Only honour X-Forwarded-For when the connection itself came from a proxy
    # we trust; otherwise the header is attacker-controlled.
    if not _is_trusted(direct):
        return direct

    forwarded = request.headers.get("X-Forwarded-For")
    if not forwarded:
        return direct

    hops = [hop.strip() for hop in forwarded.split(",") if hop.strip()]
    # Walk right-to-left: the rightmost untrusted hop is the real client.
    for hop in reversed(hops):
        if not _is_trusted(hop):
            return hop
    # All hops were trusted proxies — fall back to the leftmost (original) hop.
    return hops[0] if hops else direct
