# Arquitetura — Auditoria & Logs de Governança

> Decorre da `constitution.md` §7. Dois registros distintos: **audit log** (governança,
> alterações de usuários) e **log de uso** (produto).

## 1. Audit log (alterações de usuários)

Tabela **append-only**, imutável pela aplicação (sem `UPDATE`/`DELETE` via `app_user`;
policy/`GRANT` permitem só `INSERT`/`SELECT`).

| Coluna | Descrição |
| --- | --- |
| `id` | PK |
| `occurred_at` | timestamp (UTC) |
| `actor_id` | quem fez (usuário/admin) |
| `actor_role` | papel no momento |
| `action` | `create` \| `update` \| `delete` \| `login` \| `role_change` … |
| `entity_type` | tabela/agregado afetado |
| `entity_id` | id do registro |
| `before` | JSONB do estado anterior (sem segredos) |
| `after` | JSONB do estado novo |
| `request_id` | correlação com logs/traces |
| `ip` / `user_agent` | contexto da origem |

- **O que auditar (mínimo):** login/logout, criação/edição/exclusão de usuários,
  troca de papel/permissão, ações administrativas, alterações de consentimento.
- **Implementação:** serviço `audit/` chamado pelos services; opcionalmente
  reforçado por triggers no Postgres para alterações sensíveis.
- **PII:** `before/after` mascaram campos sensíveis conforme LGPD.

## 2. Log de uso (acompanhamento do produto)

- Eventos de uso (ex.: `feature_used`, `page_viewed`) com `user_id`, `event`,
  `props` (JSONB), `occurred_at`. Alimenta métricas de produto.
- Distinto do audit log: uso é analítico; audit é de governança/compliance.

## 3. Verificação

- Toda ação sensível gera **exatamente uma** entrada de audit (testado).
- Tentar `UPDATE`/`DELETE` no audit log como `app_user` falha.
