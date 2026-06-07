---
name: sdd-tasks
description: Break an approved design into ordered, parallelizable task waves in specs/tasks/<feature>.md, each task assigned to a specialist subagent. Run after /sdd-plan.
---

# /sdd-tasks

Quebra o design em **tarefas executáveis** organizadas em **ondas**.

## Como agir
1. A partir do design, gere `specs/tasks/<feature>.md` com tarefas pequenas e
   verificáveis. Tarefas independentes vão na mesma onda (paralelizáveis); dependentes
   em ondas seguintes.
2. Cada tarefa tem: **dono** (subagente), entradas, saída esperada e **critério de
   verificação** (teste/comando).
3. Sugestão de sequência típica:
   - Onda 1: `database-engineer` (schema/migrations/RLS).
   - Onda 2: `backend-engineer` (API/serviços) ‖ `frontend-engineer` (telas).
   - Onda 3: `test-engineer` (integração/E2E) → `security-auditor` (revisão).
   - Onda 4: `devops-engineer` (infra/CI) ‖ `docs-writer` (docs).

## Saída
- `specs/tasks/<feature>.md` com ondas e donos. Próximo passo: **`/sdd-implement`**.
