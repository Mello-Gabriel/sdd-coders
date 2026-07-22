# sdd-coders

**A replicable, spec-driven base model for production-grade fullstack apps —
built by orchestrated AI agents.**

`sdd-coders` is the `uv init` for serious fullstack systems. One command scaffolds
a complete, opinionated repository where the **architecture is already decided**
and only the **product** is yours to define. From there, a team of specialized
Claude Code agents builds the app from your specs.

```bash
uvx sdd-coders new my-app   # wizard: collect secrets, provision, launch Claude
# — or the headless path —
uvx sdd-coders init my-app
cd my-app
# open in Claude Code and run /sdd-interview
```

Already have a project? Bring the workflow to it instead of starting over:

```bash
cd my-existing-repo
uvx sdd-coders adopt          # agents, /sdd-* skills, hooks, stack-agnostic specs/
# open in Claude Code and run /sdd-constitution
```

`adopt` never overwrites your files (pass `--force` if you want it to), and its
`specs/constitution.md` ships empty on purpose — `/sdd-constitution` reads your
actual stack and fills it in with you.

> **The wizard (`new`) keeps production secrets away from every AI.** It collects
> your tokens in a native window, pushes them straight to GitHub / Coolify /
> Cloudflare (running Terraform/Ansible with state kept *outside* the repo), then
> launches Claude Code with a scrubbed environment. By construction the repo the AI
> works in holds only throwaway local-dev values — reinforced by deny-rules and a
> secret-guard hook in every generated repo.

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
| Frontend | Next.js (App Router) + TypeScript + Tailwind + shadcn/ui, dark mode, **Biome** |
| Backend | Python 3.13 + FastAPI + Pydantic v2 + SQLAlchemy async, **uv** |
| Database | PostgreSQL with **Row-Level Security everywhere** |
| Auth | Self-hosted (Argon2 + JWT), RLS context per request, single-use reset + refresh-reuse detection |
| Anti-abuse | Per-route rate limiting + escalating IP bans, Cloudflare Turnstile, mandatory email verification |
| Tests | pytest / Vitest (100%), integration (incl. RLS isolation) + Playwright E2E |
| Quality | ruff + mypy `--strict`, Biome + `tsc --strict` |
| Container | Multi-stage, slim, **non-root** images; migrations run on start |
| CI/CD | GitHub Actions: lint, types, tests, virgin-DB migrations, build, scans, docs |
| Deploy | Coolify + Hostinger VPS + Cloudflare, **IaC** (Terraform + Ansible), dev/prod GitHub Environments |
| Observability | structlog JSON + Prometheus `/metrics`; optional Grafana + Loki stack |
| Docs | OpenAPI → typed TS client, MkDocs + mkdocstrings, ER diagram |
| Compliance | **LGPD** cookie consent that actually gates + self-service export/delete/consent, audit log, admin |

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


