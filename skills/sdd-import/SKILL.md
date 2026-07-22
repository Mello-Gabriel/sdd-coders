---
name: sdd-import
description: Convert FUNCTIONAL specs that already exist in the repo (RFCs, design docs, prose specs under docs/) into EARS specs under specs/functional/. Functional only — architecture documents are never imported and this skill never writes to constitution.md. Inventory and approval first, conversion in waves. Run after /sdd-constitution in a repository adopted with `sdd-coders adopt`.
---

# /sdd-import

Traz documentação de requisitos **que já existe no repositório** para o formato
que o pipeline entende: `specs/functional/<feature>.md` em notação EARS.

## Por que existe

`/sdd-specify` produz specs a partir de um **brief** de descoberta. Num repo
adotado não há brief — há anos de RFCs, design docs e specs em prosa. Este skill
é a ponte. Sem ela, `/sdd-plan`, `/sdd-tasks` e `/sdd-analyze` não têm requisitos
com ID para rastrear.

## Escopo: só funcional

Este skill importa **exclusivamente specs funcionais** — o que o produto faz, para
quem, sob quais regras. Ele produz arquivos em `specs/functional/` e **nada mais**.

**Nunca** importa, converte ou deriva documentação de **arquitetura**: ADRs,
decisões de stack, padrões técnicos, diagramas de infraestrutura. Este skill
**não escreve em `specs/constitution.md`** em nenhuma circunstância, nem propõe
mudanças a ela.

Ao encontrar um documento arquitetural no diretório de origem, marque-o como
**fora de escopo** no manifesto e siga em frente. Ele fica exatamente onde está,
intocado. A constituição é preenchida pelo `/sdd-constitution`, que lê o
repositório por conta própria — não por importação de documento.

> Por que a separação é rígida: funcional e arquitetural têm regras de aprovação
> diferentes. Uma spec funcional entra como `draft` e você revisa. A constituição
> só muda via ADR deliberado. Deixar um importador em lote tocar na constituição
> transformaria um documento de governança em saída automática.

## Regra que não se quebra

> **Documento de origem não vira requisito por decreto.** Prosa quase nunca tem
> critério de aceite. Onde o original não disser, escreva `[LACUNA: ...]` — nunca
> invente comportamento, número, limite ou regra de negócio.

Uma spec importada com 8 lacunas marcadas é útil. Uma spec importada com 8
requisitos plausíveis e falsos é uma armadilha: `/sdd-implement` vai construir
em cima deles.

## Fase 1 — Inventário (antes de converter qualquer coisa)

1. Pergunte ao usuário **onde** estão os documentos, se ele ainda não disse
   (ex.: `docs/`, `rfcs/`, `adr/`). Não saia varrendo o repo inteiro.
2. Leia cada documento — **o suficiente para classificá-lo**, não para converter.
3. Escreva `specs/import-manifest.md`:

   | Documento de origem | Feature proposta | Ação | Motivo |
   | --- | --- | --- | --- |
   | `docs/rfcs/001-billing.md` | `billing` | converter | requisitos funcionais ativos |
   | `docs/rfcs/002-sso.md` | — | pular | superseded pela 007 |
   | `docs/legacy/perms.md` | `permissions` | mesclar em `007` | mesmo escopo |
   | `docs/adr/003-postgres.md` | — | fora de escopo | arquitetural, não funcional |

   Ações possíveis: **converter**, **mesclar** (dois docs → uma spec), **pular**
   (obsoleto/superseded), **fora de escopo** (é arquitetural — não é importado,
   fica onde está).

   Um documento misto (parte funcional, parte decisão técnica) é convertido
   **apenas na parte funcional**; a parte arquitetural não vai para lugar nenhum.
   Registre isso no motivo.
4. **Pare e apresente o manifesto.** Só siga depois que o usuário aprovar ou
   corrigir a classificação. É aqui que documentos mortos são cortados — muito
   mais barato do que descobrir depois de convertê-los.

## Fase 2 — Conversão em ondas

Converta em **ondas de no máximo 5 documentos**. Depois de cada onda, mostre o
resultado e confirme antes de seguir. Lote grande sem checkpoint degrada rápido.

Para cada documento aprovado, delegue ao **`product-analyst`** produzir
`specs/functional/<slug>.md` a partir de `specs/functional/_template.md`:

1. **Cabeçalho com procedência**, sempre:

   | Campo | Valor |
   | --- | --- |
   | Status | `draft` — **nunca** `approved`; ninguém revalidou isto ainda |
   | Origem | `docs/rfcs/001-billing.md` (commit `abc1234`) |

2. **Requisitos em EARS** derivados do texto original, cada um com ID. Onde o
   original for ambíguo (“o sistema deve ser rápido”), escreva o requisito **e**
   a lacuna: `REQ-3 (Ubíquo): O sistema deve responder em [LACUNA: qual p95?]`.
3. **Critérios de aceite** só onde o original permitir derivá-los. Caso
   contrário, `[LACUNA: critério de aceite não consta no documento de origem]`.
4. **Confronte com o código.** O documento pode estar desatualizado em relação ao
   que está implementado. Onde divergirem, registre na seção "Como se encaixa no
   que já existe": _"o doc descreve X; o código em `path.py:42` faz Y"_. Não
   silencie a divergência escolhendo um dos dois.
5. **Não apague o original.** Adicione no topo do documento de origem uma linha:
   `> Convertido para spec funcional: specs/functional/<slug>.md`.

## Fase 3 — Fechamento

1. Atualize `specs/import-manifest.md` com o resultado real de cada linha.
2. Liste ao usuário, agrupadas, **todas as `[LACUNA:]`** geradas. Essa lista é a
   pauta do próximo `/sdd-clarify` (ou de uma conversa direta).
3. Nenhuma spec importada vai para `status: approved` sem o usuário revisar as
   lacunas daquela spec.

## Saída

- `specs/import-manifest.md` — o mapa origem → spec, com o que foi pulado e por quê.
- `specs/functional/<slug>.md` para cada documento convertido, em `draft`.
- Uma lista consolidada de lacunas a resolver.
- Próximo passo: resolver as lacunas e então **`/sdd-plan`** para a feature que
  você for tocar primeiro.
