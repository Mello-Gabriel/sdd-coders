"""Structured logging (structlog → JSON on stdout).

Logs are JSON so the platform's log collector (Promtail → Loki, or Coolify's
built-in collector) can parse them. ``request_id`` is bound per request via
contextvars in the app middleware, so every line of a request is correlated.
Metrics live elsewhere (Prometheus ``/metrics``); logs are a separate signal.
"""

from __future__ import annotations

import logging
from typing import cast

import structlog


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog to emit JSON lines to stdout."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelNamesMapping()[level]),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "app") -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return cast("structlog.stdlib.BoundLogger", structlog.get_logger(name))
