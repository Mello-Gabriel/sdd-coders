# Arquitetura — Segurança da informação

> Decorre da `constitution.md` §4. Linha de base: **OWASP Top 10** + _deny by default_.

## Checklist (válido para toda feature)

- [ ] **Validação de entrada** com Pydantic (back) e zod (front). Nada confia no cliente.
- [ ] **AuthZ explícita** em toda rota; default é negar. RLS para dados.
- [ ] **Headers de segurança**: `Content-Security-Policy`, `Strict-Transport-Security`,
      `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `X-Frame-Options: DENY`,
      `Permissions-Policy`.
- [ ] **CORS** restrito a origens conhecidas (lista por ambiente).
- [ ] **CSRF**: cookies `SameSite=Lax` + token anti-CSRF em mutações state-changing
      quando aplicável.
- [ ] **Rate limiting progressivo** (`slowapi`/Redis): global + reforçado em auth.
      **Ban de IP escalado**: 5→30→240→1440→permanente (middleware + tabela `ip_bans`).
      **Cloudflare Turnstile** em register e reset-password.
- [ ] **E-mail verificado** obrigatório antes do primeiro login.
- [ ] **Segredos** só via env/secret manager. `.env` no `.gitignore`.
- [ ] **SQL**: sempre parametrizado (SQLAlchemy). Sem string interpolation.
- [ ] **Uploads**: validar tipo/tamanho; armazenar fora do webroot; antivírus quando aplicável.
- [ ] **Erros**: mensagens genéricas ao cliente; detalhes só nos logs (sem PII).
- [ ] **Dependências**: Dependabot/renovate; sem libs banidas; lockfiles versionados.

## Gates automáticos no CI

| Ferramenta | Alvo |
| --- | --- |
| `gitleaks` | segredos vazados |
| `bandit` | SAST Python |
| `semgrep` | SAST multi-linguagem (regras OWASP) |
| `trivy` / `grype` | CVEs nas imagens Docker |
| `npm audit` / `pip-audit` | CVEs em dependências |

## Modelagem de ameaças

Cada feature de risco documenta, na sua spec funcional (§9), um mini threat-model:
ativos, atores maliciosos, vetores e mitigação. STRIDE como guia.
