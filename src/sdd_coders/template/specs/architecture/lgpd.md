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

| Direito | Endpoint |
| --- | --- |
| Acesso/portabilidade | `GET /me/data-export` (gera arquivo com os dados pessoais) |
| Exclusão | `DELETE /me` (apaga/anonimiza conforme retenção legal) |
| Correção | fluxos normais de edição |
| Revogar consentimento | `POST /me/consent` |

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
