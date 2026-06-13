# syntax=docker/dockerfile:1
# Build context: ../backend

FROM python:3.13-slim AS build
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini README.md ./
RUN uv sync --frozen --no-dev

FROM python:3.13-slim AS runtime
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
# Non-root, no shell login, minimal footprint.
RUN groupadd --system app && useradd --system --gid app --no-create-home app
WORKDIR /app
COPY --from=build --chown=app:app /app /app
# Entrypoint applies pending migrations, then execs the command (uvicorn by
# default). ALEMBIC_DATABASE_URL must point at an owner role that can run DDL;
# see infra/docker-compose.yml and docs/guides/setup.md. Single-replica starter
# — for multiple replicas, run migrations as a separate release step instead.
COPY <<'EOF' /usr/local/bin/docker-entrypoint.sh
#!/bin/sh
set -e
alembic upgrade head
exec "$@"
EOF
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"]
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
