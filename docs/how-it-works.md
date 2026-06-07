# How the model works

`sdd-coders` has three parts that work together.

## 1. The engine (this repo)

A small Python CLI (`src/sdd_coders/`) that scaffolds the model into a new repo,
the way `uv init` scaffolds a Python project. It is built on **Copier**: only
`*.jinja` files are templated (so JSX `}}` and GitHub `${{ }}` survive verbatim),
and build artifacts (`.venv`, `node_modules`) are excluded from the render.

```bash
uvx sdd-coders init my-app          # scaffold
sdd-coders add-feature billing      # new functional spec (inside a project)
sdd-coders doctor                   # check the toolchain
```

## 2. The specs (`template/specs/`)

The **constitution** fixes the architecture and the non-negotiable principles.
Per-project work lives in:

- `00-product-brief.md` — filled by the **interview** (business, not tech).
- `functional/*.md` — feature specs in **EARS** notation (testable requirements).
- `architecture/*.md` — the fixed technical specs (auth/RLS, security, LGPD,
  admin, observability, audit, Docker).

The split is deliberate: you only ever decide the **what/why**; the **how** is
the constitution.

## 3. The multi-agent toolkit (`template/.claude/`)

Every generated repo ships with:

- **Agents** — an orchestrator plus nine specialists, each scoped to one concern.
- **Skills** — the `/sdd-*` pipeline (interview → specify → plan → tasks →
  implement → verify → docs).
- **Hooks** — a pre-commit gate that blocks commits when lint/types fail.
- **MCP servers** (`.mcp.json`) — Postgres, Playwright, GitHub.

The same toolkit is also distributable as a Claude Code **plugin**
(`.claude-plugin/`) for use in any repository.

## The reference app

The template is not just specs — it includes a **working** fullstack app
(`backend/`, `frontend/`, `infra/`): auth + RLS, projects CRUD, admin, LGPD
banner, hardened Docker, full CI, 100% test coverage. New features extend this
foundation rather than starting from a blank page.

## Documentation is a build artifact

`/sdd-docs` (and CI) regenerate the OpenAPI schema, the typed TS client, the API
reference (mkdocstrings) and the ER diagram from the code. CI fails if the
committed artifacts are stale — docs can't drift.
