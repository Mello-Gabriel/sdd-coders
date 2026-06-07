# sdd-coders

**A replicable, spec-driven base model for production-grade fullstack apps —
built by orchestrated AI agents.**

`sdd-coders` is the `uv init` for serious fullstack systems. One command scaffolds
a complete, opinionated repository where the **architecture is already decided**
and only the **product** is yours to define. From there, a team of specialized
Claude Code agents builds the app from your specs.

```bash
uvx sdd-coders init my-app
cd my-app
# open in Claude Code and run /sdd-interview
```

## Why

Most "starters" give you code. This gives you a **method**: fixed architecture +
a spec-driven workflow + a multi-agent toolkit, so every project you spin up is
secure, tested, observable and standardized **by default** — not by discipline.

- **Architecture is a constant.** React/Next.js + FastAPI + PostgreSQL, RLS,
  auth, Docker, CI — decided once, in [`constitution.md`](src/sdd_coders/template/specs/constitution.md).
- **Only the product varies.** A guided interview turns business pains into
  functional specs (EARS notation); agents implement them.
- **Quality is enforced, not hoped for.** 100% unit coverage (front + back),
  integration + E2E, strict typing/linting, hardened Docker, security scans,
  and auto-generated docs — all gated in CI.

## The default stack

| Layer | Choice |
| --- | --- |
| Frontend | Next.js (App Router) + TypeScript + Tailwind, **Biome** |
| Backend | Python 3.13 + FastAPI + Pydantic v2 + SQLAlchemy async, **uv** |
| Database | PostgreSQL with **Row-Level Security everywhere** |
| Auth | Self-hosted (Argon2 + JWT), RLS context per request |
| Tests | pytest / Vitest (100%), integration + Playwright E2E |
| Quality | ruff + mypy `--strict`, Biome + `tsc --strict` |
| Container | Multi-stage, slim, **non-root** images |
| CI/CD | GitHub Actions: lint, types, tests, build, scans, docs |
| Docs | OpenAPI → typed TS client, MkDocs + mkdocstrings, ER diagram |
| Compliance | **LGPD** cookie consent that actually gates, audit log, admin |

## The workflow

The first time you open a generated repo in Claude Code:

```
/sdd-interview  → discovery interview (PT-BR) → specs/00-product-brief.md
/sdd-specify    → functional specs (EARS) per feature
/sdd-plan       → derive the design from the constitution
/sdd-tasks      → break into parallelizable task waves
/sdd-implement  → orchestrator delegates to specialist agents
/sdd-verify     → lint + types + 100% tests + E2E
/sdd-docs       → regenerate OpenAPI client, API reference, ER diagram, changelog
```

A **lead/orchestrator** agent coordinates nine specialists (backend, frontend,
database, test, security, devops, docs, product-analyst). MCP servers (Postgres,
Playwright, GitHub) are the tool layer; hooks enforce quality gates.

## What's in this repository

```
src/sdd_coders/
  cli.py  scaffold.py          # the `sdd-coders` CLI (Copier-based)
  template/                    # the model that gets replicated:
    specs/                     #   constitution + architecture + EARS templates
    .claude/                   #   agents, skills, hooks, settings
    backend/  frontend/  infra/#   working reference app + Docker + CI
```

See [`docs/how-it-works.md`](docs/how-it-works.md) and
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT
