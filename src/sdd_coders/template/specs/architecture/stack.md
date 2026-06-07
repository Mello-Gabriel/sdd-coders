# Arquitetura — Stack

> Decorre da `constitution.md` §2. Aqui ficam versões, layout e comandos concretos.

## Componentes

```
frontend/  Next.js (App Router) + TypeScript strict + Tailwind + shadcn/ui
backend/   FastAPI + Pydantic v2 + SQLAlchemy 2.0 async + Alembic   (uv)
db         PostgreSQL 16 + RLS
infra/     Dockerfiles endurecidos + docker-compose
docs/      MkDocs Material (+ mkdocstrings)
```

## Layout do backend

```
backend/app/
  main.py            # cria o app FastAPI, middlewares, routers, lifespan
  core/
    config.py        # Settings (pydantic-settings), lê env
    db.py            # engine/sessionmaker async + contexto RLS por request
    security.py      # hashing Argon2, JWT encode/decode
    logging.py       # structlog + OpenTelemetry
  models/            # SQLAlchemy 2.0 (Mapped[...] tipado)
  schemas/           # Pydantic v2 (entrada/saída da API)
  api/
    deps.py          # dependências (current_user, db session com RLS)
    routes/          # auth, users, admin, health
  audit/             # serviço de audit log
  services/          # regras de negócio
backend/alembic/     # migrations (inclui policies RLS)
backend/tests/       # unit + integração (cov 100)
```

## Layout do frontend

```
frontend/
  app/               # rotas (App Router): (auth)/login, (app)/dashboard, admin/...
  components/         # UI (shadcn/ui) e componentes de domínio
  lib/
    api/             # cliente TS gerado do OpenAPI (não editar à mão)
    auth/            # helpers de sessão
    consent/         # LGPD: estado de consentimento + gating de scripts
  tests/             # vitest (unit) + playwright (e2e)
```

## Comandos canônicos

| Ação | Backend | Frontend |
| --- | --- | --- |
| Instalar | `uv sync` | `npm ci` |
| Rodar (dev) | `uv run fastapi dev` | `npm run dev` |
| Lint | `uv run ruff check .` | `npm run lint` (biome) |
| Tipos | `uv run mypy` | `npm run typecheck` |
| Testes | `uv run pytest` | `npm run test` / `npm run e2e` |
| Migração | `uv run alembic upgrade head` | — |

## Configuração (12-factor)

Tudo por variáveis de ambiente via `pydantic-settings`. `.env.example` documenta
todas as chaves; segredos nunca no repositório.
