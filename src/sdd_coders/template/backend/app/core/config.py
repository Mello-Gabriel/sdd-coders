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
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    # Empty by default; the validator below requires it outside development.
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 15 * 60
    refresh_token_ttl_seconds: int = 7 * 24 * 60 * 60
    cors_origins: list[str] = Field(default_factory=list)

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
