---
name: sdd-specify
description: Turn the product brief into approved functional specs using EARS notation, one file per feature under specs/functional/. Run after /sdd-interview.
---

# /sdd-specify

Transforma o `specs/00-product-brief.md` em **specs funcionais** testáveis.

## Como agir
1. Leia `00-product-brief.md` e a lista priorizada de funcionalidades.
2. Para cada funcionalidade, delegue ao **`product-analyst`** criar
   `specs/functional/<feature>.md` a partir de `functional/_template.md`.
3. Requisitos em **EARS** (Quando/Enquanto/Se/Onde + "o sistema deve…"), cada um
   com **critérios de aceite** (Dado/Quando/Então).
4. Em cada spec, deixe explícito: atores e **RLS**, dados/**PII**, auditoria,
   casos de borda, plano de testes.
5. Apresente as specs ao usuário; só marque `status: approved` após aprovação.

## Saída
- `specs/functional/<feature>.md` para cada funcionalidade priorizada.
- Próximo passo: **`/sdd-plan`**.
