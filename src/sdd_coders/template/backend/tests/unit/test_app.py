"""Tests for the application factory, middleware and health route."""

from __future__ import annotations

import pytest
from app.core.config import Settings
from app.main import app, create_app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_live_ok() -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "X-Request-ID" in response.headers


def test_security_headers_present() -> None:
    response = client.get("/health/live")
    assert (
        response.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"
    )
    assert "Permissions-Policy" in response.headers
    # HSTS must NOT be sent in development (would pin localhost to HTTPS).
    assert "Strict-Transport-Security" not in response.headers


def test_request_id_is_propagated() -> None:
    response = client.get("/health/live", headers={"X-Request-ID": "abc-123"})
    assert response.headers["X-Request-ID"] == "abc-123"


def test_hsts_sent_outside_development(monkeypatch: pytest.MonkeyPatch) -> None:
    prod_settings = Settings(environment="production", jwt_secret="x" * 32)
    monkeypatch.setattr("app.main.get_settings", lambda: prod_settings)
    prod_client = TestClient(create_app())
    response = prod_client.get("/health/live")
    assert response.headers["Strict-Transport-Security"].startswith("max-age=")
