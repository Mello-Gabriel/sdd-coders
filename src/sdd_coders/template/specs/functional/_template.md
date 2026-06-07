# Spec Funcional — <NOME_DA_FEATURE>

| Campo | Valor |
| --- | --- |
| ID | `FEAT-NNN` |
| Status | `draft` \| `approved` \| `implemented` |
| Prioridade | `must` \| `should` \| `could` |
| Origem | Seção do `00-product-brief.md` |
| Depende de | `FEAT-...` (ou nenhuma) |

> **Regra:** esta spec descreve **comportamento** (o quê/por quê), não implementação.
> Decisões técnicas vêm da `constitution.md` e de `architecture/`.

## 1. Contexto & objetivo

_Que dor resolve? Qual valor entrega? (1–3 frases.)_

## 2. Atores & permissões

_Quem usa esta feature e com qual papel? Qual o recorte de **RLS** (que dados cada
ator pode ver/alterar)?_

| Ator | Pode | Não pode |
| --- | --- | --- |
| Usuário | … | … |
| Admin | … | … |

## 3. Requisitos (notação EARS)

> Use os padrões EARS. Cada requisito é testável e tem um ID.

- **REQ-1 (Evento):** _Quando_ `<gatilho>`, o sistema **deve** `<comportamento>`.
- **REQ-2 (Estado):** _Enquanto_ `<estado>`, o sistema **deve** `<comportamento>`.
- **REQ-3 (Ubíquo):** O sistema **deve** `<comportamento sempre verdadeiro>`.
- **REQ-4 (Indesejado):** _Se_ `<condição de erro>`, _então_ o sistema **deve**
  `<resposta segura>`.
- **REQ-5 (Opcional):** _Onde_ `<feature presente>`, o sistema **deve** `<...>`.

## 4. Critérios de aceite

_Cenários verificáveis (formato Dado/Quando/Então). Cada cenário vira teste._

```gherkin
Cenário: <nome>
  Dado <contexto>
  Quando <ação>
  Então <resultado observável>
```

## 5. Regras de negócio

- RN-1: …

## 6. Dados & entidades afetadas

_Entidades, campos, validações (Pydantic/zod). Marque **PII**. Note impacto em
**migrations** e **policies RLS**._

## 7. Estados & fluxos

_Diagrama/lista de estados, fluxo feliz e alternativos._

## 8. Casos de borda & erros

_Entradas inválidas, concorrência, limites, idempotência, falhas externas._

## 9. Segurança & privacidade

- AuthN/AuthZ exigida: …
- Isolamento RLS: …
- Dados sensíveis / retenção / consentimento (LGPD): …
- Auditoria: o que registrar no audit log.

## 10. Observabilidade

_Eventos/métricas/logs relevantes para acompanhar esta feature._

## 11. Plano de testes

- Unit (cobrir 100% da lógica): …
- Integração (rota + DB + RLS): …
- E2E (Playwright, jornada): …

## 12. Fora de escopo

_O que esta spec **não** cobre._
