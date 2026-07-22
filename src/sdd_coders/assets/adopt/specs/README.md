# `specs/` — Especificações do projeto

Esta pasta é a **fonte da verdade** do produto. Os agentes leem daqui para
construir o sistema; o código existe para satisfazer estas specs.

Este esqueleto foi criado por `sdd-coders adopt` num repositório que **já tinha
código**. Diferente de um projeto novo, aqui a constituição descreve o stack que
já existe — comece preenchendo-a.

## Estrutura

| Caminho | O que é | Quem edita |
| --- | --- | --- |
| `constitution.md` | Arquitetura e princípios **fixos** | `/sdd-constitution`, depois raramente (via ADR) |
| `import-manifest.md` | Mapa dos documentos legados → specs (o que virou o quê, e o que foi pulado) | `/sdd-import` |
| `functional/*.md` | Specs funcionais por feature (notação **EARS**) | `/sdd-import`, `/sdd-specify` + você |
| `tasks/*.md` | Planos de tarefas gerados por feature | `/sdd-tasks` |

## Fluxo (Spec-Driven Development)

```
/sdd-constitution → descreve o stack e os princípios reais do repo  ← comece aqui
/sdd-import       → converte specs que já existem (docs/, rfcs/) para EARS
/sdd-specify      → cria functional/<feature>.md (EARS) para o que ainda não tem spec
/sdd-plan         → deriva o design (constituição + funcional)
/sdd-tasks        → quebra em tasks/<feature>.md (ondas paralelizáveis)
/sdd-implement    → orquestrador delega a subagentes especializados
/sdd-verify       → roda o quality gate declarado na constituição
/sdd-docs         → regenera a documentação
```

`/sdd-interview` (entrevista de descoberta) é para produtos **novos**. Num repo
adotado o produto já existe, então ela é opcional — use só se quiser registrar
visão, dores e usuários que nunca foram escritos.

## Regra de ouro

**Nenhuma feature sem spec funcional aprovada.** Specs primeiro, código depois.
Separe sempre **funcional** (o quê/por quê — em `functional/`) de
**arquitetural** (como — fixo na `constitution.md`).
