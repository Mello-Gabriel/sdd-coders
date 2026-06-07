# Arquitetura — Área de Admin

> Decorre da `constitution.md` §7. Fronteira administrativa **explícita** e auditada.

## Escopo

- Rotas sob `/admin` (frontend) e `/admin/*` (API), protegidas por `require_admin`
  **e** por RLS (policies que liberam visão ampla só para `role = 'admin'`).
- Funcionalidades base:
  - **Usuários**: listar, ver detalhe, ativar/desativar, trocar papel, forçar logout.
  - **Audit log**: consultar alterações (somente leitura).
  - **Logs de uso**: métricas de uso da ferramenta.
  - **Consentimentos LGPD**: visão de consentimentos e solicitações de titular.
  - **Feature flags / configurações** (quando aplicável).

## Princípios

- **Least privilege**: ações administrativas são as mínimas necessárias.
- **Tudo auditado**: cada ação de admin gera entrada no audit log (ver
  `audit-logging.md`), incluindo o admin responsável.
- **Sem backdoor de dados**: admin opera pelas mesmas APIs/policies, não por acesso
  direto ao banco.
- **Confirmações** para ações destrutivas; **2FA** recomendada para admins.

## Testes

- Usuário comum recebe `403` em toda rota `/admin/*`.
- Ações de admin aparecem no audit log com `actor = admin.id`.
