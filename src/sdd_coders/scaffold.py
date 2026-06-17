"""Render the bundled template into a new project directory using Copier."""

from __future__ import annotations

import secrets
import textwrap
from pathlib import Path

import copier

#: The template that ships inside the package (rendered by Copier).
TEMPLATE_DIR = Path(__file__).resolve().parent / "template"


def scaffold_project(destination: Path, project_name: str, ui_theme: str = "blue") -> None:
    """Copy and render the template into ``destination`` for ``project_name``.

    ``ui_theme`` selects the shadcn primary palette baked into ``globals.css``.
    """
    copier.run_copy(
        str(TEMPLATE_DIR),
        str(destination),
        data={"project_name": project_name, "ui_theme": ui_theme},
        defaults=True,
        quiet=True,
    )


def write_dev_env(path: Path) -> None:
    """Write a working local-dev ``.env`` with a freshly generated JWT secret.

    Only throwaway, local-only values — production secrets never live here (the
    wizard pushes those straight to Coolify / GitHub).
    """
    env_path = path / ".env"
    if env_path.exists():
        return
    jwt_secret = secrets.token_hex(32)
    env_path.write_text(
        textwrap.dedent(f"""\
            # Local development defaults (matches infra/docker-compose.yml).
            # Production secrets live in Coolify / GitHub Secrets — never here.
            APP_ENVIRONMENT=development
            POSTGRES_USER=postgres
            POSTGRES_PASSWORD=postgres
            POSTGRES_DB=app
            APP_DATABASE_URL=postgresql+asyncpg://app_user:app_pass@localhost:55432/app
            ALEMBIC_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:55432/app
            REDIS_PASSWORD=redis
            APP_REDIS_URL=redis://:redis@localhost:6379/0
            APP_JWT_SECRET={jwt_secret}
            APP_EMAIL_PROVIDER=memory
            APP_TURNSTILE_ENABLED=false
            APP_FRONTEND_URL=http://localhost:3000
            NEXT_PUBLIC_API_URL=http://localhost:8000
        """),
        encoding="utf-8",
    )
