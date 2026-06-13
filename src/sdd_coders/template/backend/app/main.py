"""Application factory and ASGI entrypoint."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CollectorRegistry
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import admin, auth, health, me, projects
from app.core.config import get_settings
from app.core.limiter import limiter
from app.core.logging import configure_logging, get_logger
from app.middleware.ip_ban import ip_ban_middleware

# The API serves JSON only; a tight CSP plus framing/sniffing defenses suffice.
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}
# Only sent outside development (HSTS over plain HTTP would be a footgun locally).
_HSTS = "max-age=63072000; includeSubDomains; preload"


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    configure_logging()
    log = get_logger()
    app = FastAPI(title="app", version="0.1.0")
    settings = get_settings()

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Prometheus metrics at /metrics (request count, latency, in-progress, ...).
    # A per-app registry keeps create_app() idempotent (tests build several apps).
    Instrumentator(registry=CollectorRegistry()).instrument(app).expose(
        app, include_in_schema=False
    )

    @app.middleware("http")
    async def ip_ban_gate(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        return await ip_ban_middleware(request, call_next)

    @app.middleware("http")
    async def add_request_context(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        # Bind the id for this request so every structlog line is correlated.
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        for header, value in _SECURITY_HEADERS.items():
            response.headers[header] = value
        if settings.environment != "development":
            response.headers["Strict-Transport-Security"] = _HSTS
        log.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
        )
        structlog.contextvars.clear_contextvars()
        return response

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(projects.router)
    app.include_router(admin.router)
    app.include_router(me.router)
    return app


app = create_app()
