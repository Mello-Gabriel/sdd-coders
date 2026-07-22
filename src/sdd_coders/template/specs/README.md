# `specs/` — Especificações do projeto

Esta pasta é a **fonte da verdade** do produto. Os agentes leem daqui para
construir o sistema; o código existe para satisfazer estas specs.

## Estrutura

| Caminho | O que é | Quem edita |
| --- | --- | --- |
| `constitution.md` | Arquitetura e princípios **fixos** | Raramente — `/sdd-constitution` + ADR |
| `00-product-brief.md` | Visão, dores, usuários, páginas, escopo | **Você**, na entrevista |
| `functional/*.md` | Specs funcionais por feature (notação **EARS**) | `/sdd-specify` + você |
| `architecture/*.md` | Specs técnicas (decorrem da constituição) | Fixas por default |
| `tasks/*.md` | Planos de tarefas gerados por feature | `/sdd-tasks` |

## Fluxo (Spec-Driven Development)

```
/sdd-interview   → preenche 00-product-brief.md (em PT-BR)
/sdd-specify     → cria functional/<feature>.md (EARS) a partir do brief
/sdd-plan        → deriva o design (constituição + funcional)
/sdd-tasks       → quebra em tasks/<feature>.md (ondas paralelizáveis)
/sdd-implement   → orquestrador delega a subagentes especializados
/sdd-verify      → lint + types + testes (cov 100) + Playwright E2E
/sdd-docs        → regenera documentação (OpenAPI→TS, ER, referência, changelog)
```

## Regra de ouro

**Nenhuma feature sem spec funcional aprovada.** Specs primeiro, código depois.
Separe sempre **funcional** (o quê/por quê — aqui e em `functional/`) de
**arquitetural** (como — fixo na `constitution.md` e em `architecture/`).
