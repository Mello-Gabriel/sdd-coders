"""Application settings loaded from environment variables (prefix ``APP_``)."""

from __future__ import annotations

import logging
import secrets
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Runtime configuration. Secrets must come from the environment."""

    model_config = SettingsConfigDict(
        # The canonical .env lives at the repository root, but backend commands
        # (alembic, app.scripts.*, pytest) are run from ``backend/``. Listing
        # both keeps a single .env working from either working directory; later
        # entries win, so a backend-local .env still overrides the root one.
        env_file=("../.env", ".env"),
        env_prefix="APP_",
        extra="ignore",
    )

    environment: str = "development"
    # App connects as the least-privilege role (no BYPASSRLS). Override via env.
    database_url: str = "postgresql+asyncpg://app_user:app_pass@localhost:5432/app"
    # Empty by default; the validator below requires it outside development.
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 15 * 60
    refresh_token_ttl_seconds: int = 7 * 24 * 60 * 60
    cors_origins: list[str] = Field(default_factory=list)

    # Networks allowed to set X-Forwarded-For (the reverse proxy / load balancer).
    # Defaults to localhost only; in prod add the Docker/ingress subnet via
    # APP_TRUSTED_PROXIES='["127.0.0.1/32","10.0.0.0/8"]'.
    trusted_proxies: list[str] = Field(default_factory=lambda: ["127.0.0.1/32", "::1/128"])

    # Rate limiting is on by default; the test suite disables it globally and
    # re-enables it for the dedicated rate-limit tests.
    rate_limit_enabled: bool = True

    # Redis (optional; if empty, in-memory fallback is used for rate limiting)
    redis_url: str = ""

    # Cloudflare Turnstile
    turnstile_secret_key: str = ""
    turnstile_enabled: bool = False

    # Email provider: "resend" | "smtp" | "memory"
    email_provider: str = "memory"
    resend_api_key: str = ""
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@example.com"

    # Base URL for verification/reset links sent in emails
    frontend_url: str = "http://localhost:3000"

    @model_validator(mode="after")
    def _require_secret_outside_dev(self) -> Settings:
        """Refuse to start without a JWT secret outside development.

        In development a missing secret is replaced with an ephemeral random one
        (logged loudly): convenient locally, and — crucially — it means a prod
        deploy that forgot ``APP_ENVIRONMENT`` never silently runs on an empty
        secret. Outside development a missing secret is a hard error.
        """
        if not self.jwt_secret:
            if self.environment != "development":
                msg = "APP_JWT_SECRET must be set outside development"
                raise ValueError(msg)
            object.__setattr__(self, "jwt_secret", secrets.token_hex(32))
            logger.warning(
                "APP_JWT_SECRET is unset; generated an ephemeral development secret. "
                "Tokens will not survive a restart. Set APP_JWT_SECRET for stability."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
