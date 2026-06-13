"""Application settings loaded from environment variables (prefix ``APP_``)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Secrets must come from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
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
        """Refuse to start without a JWT secret in non-development environments."""
        if self.environment != "development" and not self.jwt_secret:
            msg = "APP_JWT_SECRET must be set outside development"
            raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
