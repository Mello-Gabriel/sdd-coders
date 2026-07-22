---
name: sdd-specify
description: Turn the product brief into approved functional specs using EARS notation, one file per feature under specs/functional/. Run after /sdd-interview.
---

# /sdd-specify

Transforma o `specs/00-product-brief.md` em **specs funcionais** testáveis.

## Fonte de entrada

- **Projeto novo:** `specs/00-product-brief.md`, produzido por `/sdd-interview`.
- **Repo adotado** (`sdd-coders adopt`): não existe brief. Se o usuário indicar um
  documento de origem (uma RFC, um design doc), trabalhe a partir dele; se forem
  vários documentos já existentes no repo, use **`/sdd-import`**, que faz
  inventário e conversão em lote. Se não houver documento nenhum, colete o
  escopo direto com o usuário — não invente a partir do código.

Se o brief não existir e o usuário não apontar uma origem, **pergunte** em vez de
seguir com um arquivo vazio.

## Como agir
1. Leia a fonte de entrada acima e a lista priorizada de funcionalidades.
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
