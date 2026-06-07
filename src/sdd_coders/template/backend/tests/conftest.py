"""Shared test configuration."""

from __future__ import annotations

import os

# Configure the environment before any Settings()/engine is built.
# Secret >= 32 bytes to satisfy HS256; DB points at the local test container and
# connects as the least-privilege app_user so RLS is actually enforced.
os.environ.setdefault("APP_JWT_SECRET", "test-secret-not-for-production-0123456789")
os.environ.setdefault(
    "APP_DATABASE_URL",
    "postgresql+asyncpg://app_user:app_pass@localhost:55432/app",
)
