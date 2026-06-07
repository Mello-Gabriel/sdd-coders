"""Tests for password hashing and JWT helpers."""

from __future__ import annotations

from app.core.config import Settings
from app.core.security import (
    ACCESS_TOKEN,
    REFRESH_TOKEN,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)

settings = Settings()


def test_hash_and_verify_roundtrip() -> None:
    hashed = hash_password("s3cret-pw")
    assert hashed != "s3cret-pw"
    assert verify_password("s3cret-pw", hashed) is True


def test_verify_rejects_wrong_password() -> None:
    hashed = hash_password("right-pw")
    assert verify_password("wrong-pw", hashed) is False


def test_access_token_roundtrip() -> None:
    token = create_token("user-1", ACCESS_TOKEN, settings=settings)
    claims = decode_token(token, settings=settings)
    assert claims["sub"] == "user-1"
    assert claims["type"] == ACCESS_TOKEN
    assert claims["jti"]


def test_refresh_token_uses_custom_jti() -> None:
    token = create_token("user-1", REFRESH_TOKEN, settings=settings, jti="fixed-jti")
    claims = decode_token(token, settings=settings)
    assert claims["type"] == REFRESH_TOKEN
    assert claims["jti"] == "fixed-jti"
