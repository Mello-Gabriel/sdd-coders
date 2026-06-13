# Arquitetura — LGPD & Privacidade

> Decorre da `constitution.md` §6. Privacidade é **requisito**, com banner que
> **funciona de verdade**.

## 1. Consentimento de cookies

- **Categorias**: `necessários` (sempre on), `analytics`, `marketing`,
  `preferências`. Granular — o usuário aceita/recusa por categoria.
- **Gating real**: scripts/tags não essenciais **só carregam após consentimento**
  da categoria correspondente. Nada de "banner decorativo".
- **Persistência**: decisão salva (cookie `consent` + registro no backend com
  `versão da política`, timestamp, hash do usuário/sessão).
- **Re-consentimento**: ao mudar a política, pede de novo. Link permanente para
  "Gerenciar cookies".

## 2. Direitos do titular (endpoints)

| Direito | Endpoint | Implementação |
| --- | --- | --- |
| Acesso/portabilidade | `GET /me/data-export` | JSON com user + projects + consents + trilha de audit do próprio usuário |
| Exclusão | `DELETE /me` | **anonimiza** (e-mail → `deleted-<id>@anon.invalid`), desativa, apaga projetos próprios, revoga tokens, audita |
| Correção | fluxos normais de edição | — |
| Consentimento | `GET`/`POST /me/consent` | histórico append-only na tabela `consents` (RLS por dono) |

- **Registro de consentimento** é persistido no backend (`consents`: versão,
  categorias, timestamp) além do `localStorage` do banner — base para a trilha de
  auditoria LGPD. A tela `/settings` é o ponto único de self-service.
- **Retenção de IPs**: a tabela `ip_bans` (dado pessoal) tem expurgo lazy de
  registros não-permanentes após 30 dias; bans permanentes permanecem por
  legítimo interesse de segurança.

## 3. Princípios de dados

- **Minimização**: coletar só o necessário à finalidade.
- **Finalidade & base legal**: documentadas por dado pessoal (tabela abaixo).
- **Retenção**: prazo por categoria; expurgo/anonimização automático ao expirar.
- **PII em logs**: proibido sem necessidade; mascarar quando inevitável.

## 4. Registro de tratamento (preencher por projeto)

| Dado pessoal | Finalidade | Base legal | Retenção |
| --- | --- | --- | --- |
| e-mail | autenticação/contato | execução de contrato | enquanto conta ativa |
| TODO | TODO | TODO | TODO |

## 5. Telas com impacto LGPD

| Tela | Função LGPD |
| --- | --- |
| `/login` | E-mail verificado obrigatório antes do primeiro acesso |
| `/` (dashboard) | Nenhum script analytics carrega sem consentimento |
| `/settings` | Self-service: gerenciar categorias de cookies, exportar dados, excluir conta, trocar senha |
| `/verify-email` | Confirmação de e-mail (token de uso único); reenviável via `/auth/request-verification` |

A tela `/settings` é o **ponto único de controle LGPD para o usuário final**:
não é necessário abrir modais ou sair do app.

## 6. Verificação (E2E)

- Playwright valida: banner aparece; recusar mantém scripts não essenciais
  **bloqueados**; aceitar libera; decisão persiste entre sessões; "gerenciar"
  reabre as opções (tela `/settings`); export e delete funcionam.
- Login bloqueado até verificar e-mail; reenvio de token funciona.
- Modo escuro/claro não vaza estado entre sessões (preferência em `localStorage`).
