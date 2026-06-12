"""Rate limiter backed by Redis (prod) or in-memory (dev/test)."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings


def _get_storage_uri() -> str:
    settings = get_settings()
    if settings.redis_url:
        return settings.redis_url
    return "memory://"


limiter = Limiter(key_func=get_remote_address, storage_uri=_get_storage_uri())
