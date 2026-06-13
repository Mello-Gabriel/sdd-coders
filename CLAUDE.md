# CLAUDE.md — sdd_coders

## Project overview

`sdd_coders` is a **Spec-Driven Development (SDD) starter generator** for production-grade fullstack apps. It produces a complete repo (FastAPI + Next.js + Postgres RLS) via `uvx sdd-coders init <app>` (Copier-backed CLI). The template lives under `src/sdd_coders/template/`.

## Repository layout

```
sdd_coders/
├── src/sdd_coders/
│   ├── cli.py                    # Typer CLI: init, add-feature, doctor
│   ├── scaffold.py               # Copier + git init orchestration
│   └── template/                 # The generated repo template (Copier)
│       ├── backend/              # FastAPI app (uv, ruff, mypy, pytest)
│       ├── frontend/             # Next.js app (TypeScript strict, Biome, Vitest)
│       ├── infra/                # Docker, docker-compose
│       ├── specs/                # constitution.md + architecture specs
│       └── .claude/              # Agents, skills, hooks for generated repos
├── tests/                        # Engine CLI tests (cov 100)
└── .github/workflows/ci.yml
```

## Working on the backend template

All backend code lives in `src/sdd_coders/template/backend/`. Commands must be run from that directory:

```bash
cd src/sdd_coders/template/backend
uv run pytest                     # run all tests (100% coverage required)
uv run ruff check .               # lint
uv run mypy .                     # strict type checking
```

The test database is Docker Postgres at `localhost:55432`. The compose service is
named `db` (not `postgres`). Start it with:
```bash
docker compose -f src/sdd_coders/template/infra/docker-compose.yml up -d db
```

## Working on the frontend template

All frontend code lives in `src/sdd_coders/template/frontend/`. Commands:

```bash
cd src/sdd_coders/template/frontend
npm run test            # Vitest (100% coverage required)
npm run build           # Next.js production build
npx biome check .       # lint + format check
```

## Architecture decisions (non-negotiable)

- **Auth**: JWT access+refresh in httpOnly cookies, Argon2 password hashing, Postgres RLS for all user data. The app connects as `app_user` (no `BYPASSRLS`).
- **Coverage gate**: `fail_under = 100` in both backend and frontend. PRs must not drop coverage.
- **No mock DB in integration tests**: integration tests hit real Postgres (Docker). Mock sessions only for unit tests covering edge cases that require controlling `session.get()` return values.
- **IP bans**: stored in `ip_bans` table; escalation ladder `[5, 30, 240, 1440, None]` minutes; middleware gracefully degrades on DB errors (`except Exception: # pragma: no cover`).
- **Email provider**: abstracted via `EmailProvider` protocol. `MemoryProvider` for tests, `ResendProvider` for prod. Select via `APP_EMAIL_PROVIDER` env var.
- **Rate limiting**: `slowapi` + Redis in prod, in-memory in dev/test. `APP_REDIS_URL` controls the backend.
- **Turnstile**: disabled by default (`APP_TURNSTILE_ENABLED=false`). Enabled in prod for register + password-reset routes.

## Completed features (F0–F8)

| Feature | Status | Notes |
|---------|--------|-------|
| F0 — Engine foundations | done | uv, ruff, mypy, pytest, CI |
| F1 — Spec framework | done | constitution + architecture specs |
| F2 — Multi-agent toolkit | done | agents, skills, hooks, MCP |
| F3 — Backend starter | done | FastAPI, auth, RLS, audit, health |
| F4 — Frontend starter | done | Next.js, auth, admin, LGPD banner |
| F5 — Infra & CI | done | Docker, GH Actions, scans |
| F6 — CLI & replication | done | `uvx sdd-coders init` via Copier |
| F7 — Docs pipeline | done | MkDocs, OpenAPI client, ER diagram |
| F8 — Anti-abuse backend | done | Rate limit, IP ban, Turnstile, email verify |

## Pending features (v2)

- **F9** — Frontend: shadcn/ui dark mode, 4 standard screens, Turnstile widget, GA Consent Mode
- **F10** — Toolkit: design-engineer + platform-engineer agents, `/sdd-design` skill, Onlook integration
- **F11** — Infra IaC: Terraform (Hostinger + Cloudflare) + Ansible + Coolify + GitHub Environments
- **F12** — Retrospective: update constitution + specs with v2 lessons, `add-feature` stubs

## Key environment variables (backend)

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_DATABASE_URL` | — | asyncpg connection string |
| `APP_JWT_SECRET` | — | JWT signing secret |
| `APP_REDIS_URL` | `""` | Redis URI; empty = in-memory rate limit |
| `APP_TURNSTILE_ENABLED` | `false` | Enable Cloudflare Turnstile |
| `APP_TURNSTILE_SECRET_KEY` | `""` | Turnstile server-side secret |
| `APP_EMAIL_PROVIDER` | `memory` | `memory` \| `resend` \| `smtp` |
| `APP_RESEND_API_KEY` | `""` | Resend API key |
| `APP_FRONTEND_URL` | `http://localhost:3000` | Base URL for email links |

## Testing patterns

```python
# Unit test: mock session to cover None-return branches in verification service
session = MagicMock()
session.get = AsyncMock(return_value=None)

# Integration test: set email_verified before login
user = await owner_session.get(User, user_id)
user.email_verified = True
await owner_session.commit()

# Integration test: inject MemoryProvider to inspect sent emails
from app.services.email import get_email_provider, MemoryProvider
provider = get_email_provider()
assert isinstance(provider, MemoryProvider)
token_url = provider.outbox[0].text.split()[-1]
```

## Lessons learned (F8)

- **Detached SQLAlchemy instances**: always reload with `session.get(User, user.id)` before writing to an object loaded in a different session.
- **RLS sequence grants**: `autoincrement` columns need both `GRANT ... ON TABLE` AND `GRANT USAGE, SELECT ON SEQUENCE`.
- **ASGI test transport**: `httpx.ASGITransport` sets `request.client.host = "127.0.0.1"`, not `"testclient"`.
- **X-Forwarded-For**: only trust when the direct peer is a configured trusted proxy (CIDR list in `Settings.trusted_proxies`); walk the header right-to-left to the first untrusted hop (`app/core/client_ip.py`).
- **`lru_cache` in tests**: always call `get_settings.cache_clear()` and `get_email_provider.cache_clear()` before/after tests that monkeypatch env vars.

## Lessons learned (v3 remediation)

- **Migrations must be explicit.** Never use `Base.metadata.create_all()` in a migration — the live ORM schema drifts and the migration stops matching prior revisions. Use literal `op.create_table`. The CI `migrations` job runs `upgrade → downgrade → upgrade` on a virgin DB to catch this.
- **Coverage ≠ integration.** 100% unit coverage hid features that were never wired (rate limiting, IP-ban ladder). Test the production path: migrations on a fresh DB, the anti-abuse flow end-to-end.
- **The engine CI does not run the template's own gates.** Template backend/frontend `ruff/mypy/biome/tsc` only run in *generated* projects, so drift accumulates here unnoticed — run them manually when touching the template.
- **RLS + INSERT needs `WITH CHECK`.** A policy with only `USING` does not gate INSERT, so the insert is denied. Add `WITH CHECK` for any table users insert into (e.g. `consents`).
- **RLS + cross-session writes.** A write done in a request that then raises (e.g. 401) is rolled back. For durable side effects (strike counting, refresh-family revocation) open a dedicated committed session — and set the right RLS context, or the UPDATE matches zero rows.
- **`NEXT_PUBLIC_*` are build-time.** They're inlined into the client bundle, so they must be Docker `--build-arg`s, not runtime env.
- **Three signals.** Metrics→Prometheus, logs→Loki, traces→Tempo. Logs never go to Prometheus.
