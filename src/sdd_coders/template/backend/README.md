# Backend

FastAPI + Pydantic v2 + SQLAlchemy 2.0 (async) + PostgreSQL with Row-Level Security.
Managed by **uv**. See `../specs/architecture/auth-rls.md` for the RLS pattern.

```bash
uv sync
uv run fastapi dev app/main.py      # dev server
uv run ruff check . && uv run mypy  # lint + types
uv run pytest                       # tests (100% coverage gate)
uv run alembic upgrade head         # migrations
```
