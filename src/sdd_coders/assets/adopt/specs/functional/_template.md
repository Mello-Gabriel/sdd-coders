# Spec Funcional — <NOME_DA_FEATURE>

| Campo | Valor |
| --- | --- |
| ID | `FEAT-NNN` |
| Status | `draft` \| `approved` \| `implemented` |
| Prioridade | `must` \| `should` \| `could` |
| Depende de | `FEAT-...` (ou nenhuma) |

> **Regra:** esta spec descreve **comportamento** (o quê/por quê), não
> implementação. As decisões técnicas vêm da `constitution.md`.

## 1. Contexto & objetivo

_Que dor resolve? Qual valor entrega? (1–3 frases.)_

## 2. Atores & permissões

_Quem usa esta feature e com qual papel? Que dados cada ator pode ver/alterar?_

| Ator | Pode | Não pode |
| --- | --- | --- |
| … | … | … |

## 3. Como se encaixa no que já existe

_Num repositório adotado, a maior parte das features toca código existente.
Aponte os módulos, rotas, tabelas ou telas afetados e o que **não** pode
quebrar (contratos públicos, formatos persistidos, integrações)._

## 4. Requisitos (notação EARS)

> Use os padrões EARS. Cada requisito é testável e tem um ID.

- **REQ-1 (Evento):** _Quando_ `<gatilho>`, o sistema **deve** `<comportamento>`.
- **REQ-2 (Estado):** _Enquanto_ `<estado>`, o sistema **deve** `<comportamento>`.
- **REQ-3 (Ubíquo):** O sistema **deve** `<comportamento sempre verdadeiro>`.
- **REQ-4 (Indesejado):** _Se_ `<condição de erro>`, _então_ o sistema **deve**
  `<resposta segura>`.
- **REQ-5 (Opcional):** _Onde_ `<feature presente>`, o sistema **deve** `<...>`.

## 5. Critérios de aceite

_Cenários verificáveis (formato Dado/Quando/Então). Cada cenário vira teste._

```gherkin
Cenário: <nome>
  Dado <contexto>
  Quando <ação>
  Então <resultado observável>
```

## 6. Regras de negócio

- RN-1: …

## 7. Dados & entidades afetadas

_Entidades, campos, validações. Marque dados pessoais/sensíveis. Note impacto em
migrations e em dados já existentes (backfill, compatibilidade)._

## 8. Estados & fluxos

_Fluxo feliz e alternativos._

## 9. Casos de borda & erros

_Entradas inválidas, concorrência, limites, idempotência, falhas externas._

## 10. Segurança & privacidade

- AuthN/AuthZ exigida: …
- Dados sensíveis / retenção / consentimento: …
- O que registrar para auditoria: …

## 11. Observabilidade

_Eventos/métricas/logs relevantes para acompanhar esta feature._

## 12. Plano de testes

_Alinhe com o gate declarado na `constitution.md`._

- Unit: …
- Integração: …
- E2E: …

## 13. Fora de escopo

_O que esta spec **não** cobre._
