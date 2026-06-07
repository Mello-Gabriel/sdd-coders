# Contributing to sdd-coders

## Layout

- `src/sdd_coders/` — the CLI engine (linted, typed, 100% covered).
- `src/sdd_coders/template/` — the replicated model. **Excluded** from the
  engine's ruff/mypy/coverage; it has its own quality gates (run from inside it).

## Engine

```bash
uv sync --dev
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest          # 100% coverage gate
```

## Template (the reference app)

The backend and frontend inside `template/` are real projects with their own
gates. To work on them, install their deps **outside** the template (so no
`.venv` / `node_modules` leak into the scaffold source):

```bash
# Backend (needs a Postgres for integration tests)
docker run -d --name pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=app -p 55432:5432 postgres:16-alpine
UV_PROJECT_ENVIRONMENT=/tmp/be uv run --project src/sdd_coders/template/backend pytest
```

> Never commit `.venv`, `node_modules`, `.next` or coverage output under
> `template/` — Copier cannot render a tree that contains them.

## Conventions

- **Conventional Commits** (feed the changelog).
- Specs first: changes to the architecture require an ADR (`docs/adr/`).
- Keep the root plugin (`agents/`, `skills/`) in sync with
  `template/.claude/` (same content, different distribution).

## Releasing

`uv build` produces the wheel; the bundled `template/` is included automatically
(VCS-ignored files are excluded). Verify with:

```bash
uvx --from ./dist/sdd_coders-*.whl sdd-coders init /tmp/smoke
```
