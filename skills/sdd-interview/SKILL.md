---
name: sdd-interview
description: Conduct the initial discovery interview (in Brazilian Portuguese) and fill specs/00-product-brief.md with business needs, pains, users, pages and features. Run this first on a freshly scaffolded repo.
---

# /sdd-interview

Primeira interação do projeto. Conduza uma **entrevista de descoberta** com o usuário,
em **português**, para entender o negócio e as dores — **não** a tecnologia
(arquitetura já é fixa em `specs/constitution.md`).

## Como agir
1. Delegue ao subagente **`product-analyst`** (ou assuma o papel) e explique em 2-3
   linhas como este modelo funciona (SDD + agentes + arquitetura fixa).
2. Percorra as seções de `specs/00-product-brief.md` fazendo perguntas claras —
   preferencialmente **uma por vez** quando isso ajudar a pensar.
3. Cubra: dores, personas, jobs-to-be-done, páginas/telas, funcionalidades,
   regras de negócio, dados e **PII**, integrações, métricas de sucesso, compliance.
4. Resuma e **confirme** com o usuário antes de gravar.
5. Salve preenchendo `specs/00-product-brief.md`.

## Saída
- `specs/00-product-brief.md` preenchido e validado.
- Próximo passo sugerido ao usuário: **`/sdd-specify`**.
