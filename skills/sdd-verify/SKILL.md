---
name: sdd-verify
description: Run the full quality gate — backend and frontend lint, format, type-check, unit tests with 100% coverage, integration (incl. RLS isolation) and Playwright E2E. Reports failures; blocks "done" until green.
---

# /sdd-verify

Portão de qualidade. Replica o que o CI exige; nada é "feito" sem isto **verde**.

## Backend
```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest            # gate --cov-fail-under=100, inclui integração + RLS
```

## Frontend
```bash
npm run lint             # biome
npm run typecheck        # tsc --noEmit
npm run test             # vitest, cobertura 100%
npm run e2e              # playwright (login, LGPD, admin negado a user)
```

## Como agir
1. Rode os blocos acima (delegue ao `test-engineer`/`devops-engineer` se útil).
2. Para cada falha, conserte na origem (não relaxe o gate de cobertura).
3. Confirme que os **critérios de aceite** da spec funcional passam.
4. Reporte um resumo: o que passou, o que falhou, o que foi corrigido.

## Saída
- Tudo verde → siga para **`/sdd-docs`**. Caso contrário, lista de pendências.
