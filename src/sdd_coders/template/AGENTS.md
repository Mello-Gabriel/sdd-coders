# AGENTS.md — {{ project_name }}

Contexto para agentes de IA neste repositório (convenção **agents.md**). A guidance
acumula descendo a árvore: `backend/AGENTS.md` e `frontend/AGENTS.md` complementam este.

## Stack

`frontend/` Next.js (App Router) + TypeScript · `backend/` FastAPI + Pydantic v2 +
SQLAlchemy async (gerenciado por **uv**) · PostgreSQL + **RLS** · Docker.
Detalhes em `specs/architecture/stack.md`.

## Comandos

**Backend** (`cd backend`):
`uv sync` · `uv run fastapi dev` · `uv run ruff check .` · `uv run mypy` ·
`uv run pytest` · `uv run alembic upgrade head`

**Frontend** (`cd frontend`):
`npm ci` · `npm run dev` · `npm run lint` · `npm run typecheck` · `npm run test` ·
`npm run e2e`

## Convenções

- **uv** sempre no backend; **npm** no frontend. Nada de pip/poetry direto.
- Tipagem estrita; **100% de cobertura** (gate de CI). **Conventional Commits**.
- Código/identificadores/API em **inglês**; specs e textos de negócio em **PT-BR**.
- Prefira **reuso** ao que já existe antes de criar algo novo.

## Segurança (inegociável)

- **Deny-by-default** nas rotas; **RLS** em toda tabela de usuário
  (`specs/architecture/auth-rls.md`).
- Segredos só via env (`.env` é git-ignored). Validar **toda** entrada.
- **PII fora dos logs**; LGPD com banner que **funciona** (`specs/architecture/lgpd.md`).

## Antes de abrir PR

Rode **`/sdd-verify`** (lint + types + testes 100% + E2E) — é exatamente o que o CI exige.
