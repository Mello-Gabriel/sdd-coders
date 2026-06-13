"""Rate limiter backed by Redis (prod) or in-memory (dev/test).

Keyed by the real client IP (proxy-aware, see ``app.core.client_ip``) so that a
client behind a trusted reverse proxy cannot bypass limits by spoofing headers.
"""

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter

from app.core.client_ip import get_client_ip
from app.core.config import get_settings


def _get_storage_uri() -> str:
    settings = get_settings()
    if settings.redis_url:
        return settings.redis_url
    return "memory://"


def _rate_limit_key(request: Request) -> str:
    return get_client_ip(request)


limiter = Limiter(
    key_func=_rate_limit_key,
    storage_uri=_get_storage_uri(),
    enabled=get_settings().rate_limit_enabled,
)
