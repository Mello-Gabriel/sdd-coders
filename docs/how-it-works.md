# How the model works

`sdd-coders` has three parts that work together.

## 1. The engine (this repo)

A small Python CLI (`src/sdd_coders/`) that scaffolds the model into a new repo,
the way `uv init` scaffolds a Python project. It is built on **Copier**: only
`*.jinja` files are templated (so JSX `}}` and GitHub `${{ }}` survive verbatim),
and build artifacts (`.venv`, `node_modules`) are excluded from the render.

```bash
uvx sdd-coders new my-app           # wizard: scaffold + provision + launch Claude
uvx sdd-coders init my-app          # scaffold only (+ generates a local-dev .env)
sdd-coders configure my-app         # reopen the wizard to rotate/update secrets
sdd-coders add-feature billing      # EARS spec + code stubs (router, page, test)
sdd-coders doctor                   # check the toolchain
```

`init` also writes a `.copier-answers.yml`, so a generated project can later run
`copier update` to pull in fixes from a newer template version.

### The wizard and the secret boundary

`new` opens a native (Tkinter) window — no browser, so no browser-AI surface ever
sees the form. The guarantee that **no AI can read production secrets is
architectural**, not a matter of model behavior:

- The wizard is a *privileged* process that holds secrets in memory and the OS
  keychain, and pushes them straight to their remote homes — GitHub
  secrets/variables (over stdin, never argv), Coolify env (API), Terraform
  (`TF_VAR_*`), Ansible (a transient inventory). Terraform **state** and the
  inventory live under `~/.local/state/sdd-coders/<project>/`, never in the repo.
- Claude Code is launched as an *unprivileged* child: its working dir (the repo)
  holds only throwaway local-dev values, and its environment is **scrubbed** of
  every secret-shaped variable before launch.
- Every generated repo ships defense-in-depth: `.claude/settings.json` deny-rules
  plus a `secret-guard` hook that block the agent from reading `.env`/`*.tfvars`/
  state/inventory or dumping the environment.

This works because the template needs **zero** production secrets for local dev
(memory email provider, in-memory rate limiting, Turnstile off, ephemeral JWT).

### Picking a look

At creation you choose a **UI theme** — a curated shadcn/Tailwind primary palette
(`blue`, `neutral`, `violet`, `emerald`, `rose`). It only swaps the design tokens in
`globals.css` (same screens, different accent), so it costs nothing against the
frontend's 100% test gate. The wizard shows colour swatches; headless it's
`sdd-coders init --theme violet`.

## 2. The specs (`template/specs/`)

The **constitution** fixes the architecture and the non-negotiable principles.
Per-project work lives in:

- `00-product-brief.md` — filled by the **interview** (business, not tech).
- `functional/*.md` — feature specs in **EARS** notation (testable requirements).
- `architecture/*.md` — the fixed technical specs (auth/RLS, security,
  anti-abuse, LGPD, admin, observability, audit, Docker, deploy).

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
(`backend/`, `frontend/`, `infra/`): auth + RLS with single-use reset tokens and
refresh-reuse detection, anti-abuse (per-route rate limits + escalating IP bans +
Turnstile + email verification), projects CRUD, admin, LGPD banner **plus
self-service data export / deletion / consent**, structured logging and a
Prometheus `/metrics` endpoint, hardened Docker, full CI (including a virgin-DB
migration check), 100% test coverage. New features extend this foundation rather
than starting from a blank page.

## Deploy & observability

`infra/` ships infrastructure-as-code: Terraform (Cloudflare DNS + edge rate
limiting, Coolify environments) and an Ansible hardening playbook, plus dev/prod
deploy workflows gated by GitHub Environments. A separate
`infra/monitoring/` compose brings up Prometheus + Grafana + Loki + Promtail +
Node Exporter — or point the app at Grafana Cloud. See
[`template/docs/guides/setup.md`](../src/sdd_coders/template/docs/guides/setup.md)
for the full one-time setup.

## Documentation is a build artifact

`/sdd-docs` (and CI) regenerate the OpenAPI schema, the typed TS client, the API
reference (mkdocstrings) and the ER diagram from the code. CI fails if the
committed artifacts are stale — docs can't drift.
