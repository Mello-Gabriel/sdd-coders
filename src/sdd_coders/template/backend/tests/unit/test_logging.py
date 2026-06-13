"""Tests for structured logging configuration."""

from __future__ import annotations

import json

import pytest
from app.core.logging import configure_logging, get_logger


def test_configure_logging_emits_json(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging()
    log = get_logger("test")
    log.info("hello", answer=42)
    out = capsys.readouterr().out.strip()
    record = json.loads(out)
    assert record["event"] == "hello"
    assert record["answer"] == 42
    assert record["level"] == "info"


def test_get_logger_returns_bound_logger() -> None:
    configure_logging()
    assert get_logger("x") is not None
