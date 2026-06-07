# Constituição do Projeto

> **O que é este documento.** A _constituição_ define a arquitetura, os padrões e
> os princípios **inegociáveis** deste projeto. Ela é **fixa por default**: você
> normalmente **não** a edita ao iniciar um projeto novo — ela já vem decidida
> pelo modelo base `sdd-coders`. As decisões _funcionais_ (o que o produto faz,
> quais dores resolve, quais páginas existem) ficam nas **specs funcionais**
> (`specs/functional/`), não aqui.
>
> Toda decisão dos agentes (padrões, bibliotecas, segurança, testes) é
> restringida por este documento. Mudanças aqui exigem um **ADR**
> (`docs/adr/`) registrando motivo, alternativas e consequências.

Idioma: **PT-BR** para princípios e specs de negócio; **EN** para código, API,
identificadores, mensagens de commit e documentação técnica.

---

## 1. Princípios inegociáveis (NON-NEGOTIABLE)

1. **Spec-first.** Nenhuma feature é implementada sem uma spec funcional aprovada.
   Código sem spec é dívida, não progresso.
2. **Seguro por padrão.** _Deny by default_. Toda rota é autenticada e autorizada
   salvo decisão explícita; todo dado de usuário é isolado por **RLS**.
3. **100% de cobertura de testes** (unit) no backend e no frontend, com gate no CI
   (`--cov-fail-under=100`). Mais testes de integração e E2E. Cobertura não é meta
   de vaidade: é o piso para refatorar com segurança.
4. **Tipagem estrita.** `mypy --strict` (backend) e `tsc --strict` (frontend). Sem
   `any`/`# type: ignore` sem justificativa em comentário.
5. **Tudo versionado e reprodutível.** Migrations, configs, infra e docs vivem no
   repositório. `uv` trava o backend; lockfile no frontend. Builds determinísticos.
6. **Observável.** Nada vai a produção sem logs estruturados, métricas e tracing.
7. **Documentação é gerada, não escrita à mão e esquecida.** API, referência,
   diagrama ER e changelog são **artefatos de build**, validados no CI.
8. **Simplicidade > esperteza.** A solução mais simples que satisfaz a spec vence.
   Sem over-engineering, sem abstração especulativa.
9. **Privacidade e LGPD são requisito, não enfeite.** Consentimento real, minimização
   de dados, direito de acesso/exclusão.

---

## 2. Stack padrão (fixa)

| Camada | Tecnologia |
| --- | --- |
| Frontend | **Next.js (App Router) + React + TypeScript strict** |
| Estilo/UI | **Tailwind CSS + shadcn/ui** |
| Backend | **Python 3.13 + FastAPI + Pydantic v2** |
| Gerência backend | **uv** (sempre; nunca pip/poetry direto) |
| ORM/DB toolkit | **SQLAlchemy 2.0 (async) + Alembic** (migrations) |
| Driver DB | **asyncpg** |
| Banco | **PostgreSQL** com **Row-Level Security (RLS) sempre** |
| AuthN/AuthZ | **Self-hosted no FastAPI**: senha **Argon2**, **JWT** access+refresh em cookies httpOnly/SameSite; RLS por request |
| Testes backend | **pytest** (+ pytest-asyncio, + pytest-cov) |
| Testes frontend | **Vitest + React Testing Library** (unit), **Playwright** (E2E) |
| Lint/format backend | **ruff** (lint + format) + **mypy --strict** |
| Lint/format frontend | **Biome** (default; ESLint+Prettier é alternativa documentada) |
| Logs | **structlog** (JSON estruturado) |
| Métricas/Tracing | **OpenTelemetry** + endpoint Prometheus |
| Container | **Docker** multi-stage, imagem mínima (distroless/slim), non-root |
| CI/CD | **GitHub Actions** |
| Docs | **MkDocs Material + mkdocstrings**, cliente TS gerado do OpenAPI, ER auto |

Trocar qualquer item desta tabela é uma decisão de **constituição** → requer ADR.

---

## 3. Padrões de qualidade

- **Testes:** unit 100% (gate), integração cobrindo cada rota/fluxo, E2E Playwright
  para jornadas críticas (login, consentimento LGPD, admin). Testes são
  determinísticos e isolados (sem rede/relógio reais sem _fakes_).
- **Lint/Format:** `ruff check` + `ruff format --check`; `biome check`. CI falha em
  qualquer violação.
- **Tipos:** `mypy --strict` e `tsc --noEmit` limpos.
- **Tamanho/complexidade:** funções pequenas e coesas; regras `PL`/`C901` do ruff.
- **Convenções de nomes:** `snake_case` (Python), `camelCase`/`PascalCase` (TS),
  `kebab-case` (arquivos de rota), `UPPER_SNAKE` (env vars).

---

## 4. Segurança da informação

- **OWASP Top 10** como linha de base. Validação de toda entrada via Pydantic/zod.
- **Deny by default** em rotas e em RLS.
- **Segredos** só via variáveis de ambiente / secret manager — **nunca** no repo.
  CI roda `gitleaks` (segredos), `bandit`+`semgrep` (SAST) e `trivy`/`grype` (imagens).
- **Headers** de segurança (CSP, HSTS, X-Content-Type-Options, Referrer-Policy) no
  frontend e backend.
- **Rate limiting** e **lockout** em endpoints de auth. Proteção contra brute force.
- **CORS** restrito a origens conhecidas. **CSRF**: cookies SameSite + token quando
  aplicável.
- **Senhas:** Argon2id. Tokens de reset/refresh com expiração e rotação.
- **Dependências:** atualizações monitoradas (Dependabot/renovate); sem libs banidas.

---

## 5. Autenticação & Autorização — RLS sempre

- Auth implementada **no backend FastAPI** (sem IdP de terceiros por default).
- **Fluxo:** login → JWT **access** (curto) + **refresh** (rotacionado), ambos em
  cookies **httpOnly + Secure + SameSite**. Logout invalida refresh.
- **RLS obrigatório:** a aplicação conecta ao Postgres como uma role **sem
  BYPASSRLS**. A cada request, dentro de uma transação, o backend executa
  `SET LOCAL app.current_user_id = <id>` (e claims relevantes), e **policies RLS**
  versionadas nas migrations garantem que cada usuário só enxerga suas linhas.
- **Autorização** por papéis (`user`, `admin`) e, quando necessário, por permissões
  finas. Admin é uma fronteira explícita (ver §7).
- **Princípio:** a segurança de dados mora no **banco** (RLS), não só na aplicação.

---

## 6. LGPD & Privacidade

- **Banner de cookies funcional**: categorias granulares (necessários, analytics,
  marketing); scripts não essenciais **bloqueados de fato** até o consentimento;
  decisão **persistida** e re-perguntável; registro de consentimento (quem/quando/versão).
- **Direitos do titular:** endpoints para **exportar** e **excluir** dados pessoais.
- **Minimização:** coletar só o necessário; PII marcada e tratada com cuidado.
- **Base legal e finalidade** documentadas em `specs/architecture/lgpd.md`.
- **Logs não vazam PII** sem necessidade; mascaramento quando aplicável.

---

## 7. Admin & Governança

- **Área de admin** protegida (rota e RLS), separada da área do usuário.
- **Audit log de alterações de usuários**: registra _quem, quando, o quê, antes/depois_
  para governança (tabela append-only, imutável pela aplicação).
- **Log de uso da ferramenta**: eventos de uso para acompanhamento do produto.
- Acessos administrativos são auditados e seguem _least privilege_.

---

## 8. Observabilidade

- **Logs estruturados** (structlog, JSON) com `request_id`/`trace_id` correlacionados.
- **Métricas** (OpenTelemetry → Prometheus): latência, throughput, erros, saturação.
- **Tracing** distribuído ponta a ponta (frontend → backend → DB quando viável).
- **Health/readiness** endpoints. Alertas sobre SLOs definidos por projeto.

---

## 9. Docker & Deploy seguro

- **Multi-stage**: build separado do runtime; imagem final **mínima**
  (distroless ou `*-slim`), **somente** o necessário.
- **Usuário non-root**, filesystem **read-only** onde possível, `HEALTHCHECK`,
  sem ferramentas de debug/shell desnecessárias na imagem final.
- **`docker-compose`** para dev (postgres + backend + frontend). Imagens escaneadas
  no CI (trivy/grype).

---

## 10. Git, CI/CD

- Repositório com **remoto no GitHub**, **branch protection** sugerida, fluxo via PR.
- **Conventional Commits** (alimentam o changelog automático).
- **CI (GitHub Actions)** roda em todo push/PR: lint + format + types + testes
  (cov 100) no back e no front, build dos dois, sobe via `docker-compose` e roda
  **Playwright E2E**, build das imagens, **scans** de segurança, **build/publish da
  documentação**. Merge bloqueado se qualquer etapa falhar.

---

## 11. Documentação automatizada (artefato de build)

- **API:** OpenAPI/Swagger gerado pelo FastAPI; **cliente TypeScript gerado** do
  OpenAPI (openapi-typescript/orval) consumido pelo frontend (tipos sempre em sincronia).
- **Referência:** **MkDocs Material + mkdocstrings** gera referência a partir das
  docstrings; specs e ADRs publicados no mesmo site.
- **Banco:** **diagrama ER** gerado das models/migrations.
- **Changelog:** gerado dos Conventional Commits.
- Tudo é **construído e validado no CI** (com link-check) e publicado (GitHub Pages).

---

## 12. Processo SDD & agentes

Pipeline (ver `.claude/skills/sdd-*`):

`/sdd-interview` → `/sdd-specify` → `/sdd-plan` → `/sdd-tasks` → `/sdd-implement`
→ `/sdd-verify` → `/sdd-docs`.

- A **entrevista** (em PT-BR) captura dores, usuários, páginas e funcionalidades em
  `specs/00-product-brief.md`.
- As **specs funcionais** usam **notação EARS** (ver `specs/functional/_template.md`).
- Um **orquestrador** delega a subagentes especializados (backend, frontend, database,
  test, security, devops, docs). Cada agente respeita esta constituição.

### Notação EARS (resumo)

| Padrão | Forma |
| --- | --- |
| Ubíquo | "O `<sistema>` **deve** `<comportamento>`." |
| Estado | "**Enquanto** `<estado>`, o `<sistema>` **deve** `<comportamento>`." |
| Evento | "**Quando** `<gatilho>`, o `<sistema>` **deve** `<comportamento>`." |
| Opcional | "**Onde** `<feature presente>`, o `<sistema>` **deve** `<comportamento>`." |
| Indesejado | "**Se** `<gatilho>`, **então** o `<sistema>` **deve** `<comportamento>`." |

---

## 13. Como evoluir a constituição

Qualquer mudança aqui requer um **ADR** em `docs/adr/NNNN-titulo.md` descrevendo:
contexto, decisão, alternativas consideradas e consequências. A constituição é
estável **por design** — projetos divergem nas specs funcionais, não na arquitetura.
