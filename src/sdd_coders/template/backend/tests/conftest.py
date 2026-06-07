"""Shared test configuration."""

from __future__ import annotations

import os

# Provide a JWT secret for the test session before any Settings() is built.
os.environ.setdefault("APP_JWT_SECRET", "test-secret-not-for-production")
