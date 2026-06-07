---
name: sdd-implement
description: Execute the task plan by delegating each task to the right specialist subagent, integrating results, and iterating until the feature's acceptance criteria pass. Run after /sdd-tasks.
---

# /sdd-implement

Constrói a feature executando `specs/tasks/<feature>.md`. Use o subagente
**`orchestrator`** (ou assuma o papel de lead).

## Como agir
1. Para cada onda, **delegue** cada tarefa ao subagente dono, passando contexto
   suficiente (arquivos, trechos, critérios de aceite) — eles não veem sua conversa.
2. Rode ondas independentes em paralelo quando possível; respeite dependências.
3. Após cada onda, **integre** e rode os checks relevantes. Não avance com algo quebrado.
4. Ao final, rode **`/sdd-verify`**. Só conclua com tudo verde.
5. Atualize `status` da spec para `implemented` e dispare **`/sdd-docs`**.

## Princípios
- Spec-first, deny-by-default, RLS sempre, 100% de cobertura, simplicidade.
- Prefira reuso ao já existente; cada mudança nasce coberta por testes.
