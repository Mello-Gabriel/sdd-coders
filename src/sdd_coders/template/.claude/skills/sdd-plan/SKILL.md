---
name: sdd-plan
description: Derive the technical design for an approved functional spec from the fixed constitution + architecture specs. Produces a concise design note; does not re-decide architecture. Run after /sdd-specify.
---

# /sdd-plan

Deriva o **design técnico** de uma feature aprovada. A arquitetura **não é
re-decidida** — ela vem da `constitution.md` e de `specs/architecture/*`.

## Como agir
1. Leia a spec funcional alvo + `constitution.md` + `architecture/*`.
2. Produza um design enxuto em `specs/functional/<feature>.md` (seção de design) ou
   nota anexa, cobrindo:
   - Entidades/tabelas e **migrations + policies RLS** necessárias.
   - Endpoints/contratos (entrada/saída Pydantic) e regras/serviços.
   - Telas/componentes e estados no frontend.
   - Pontos de **auditoria**, **observabilidade** e **LGPD**.
   - Impacto em testes (unit/integração/E2E) e em docs.
3. Reuse o que já existe no repo; aponte arquivos concretos a tocar.

## Saída
- Design derivado, alinhado à constituição. Próximo passo: **`/sdd-tasks`**.
