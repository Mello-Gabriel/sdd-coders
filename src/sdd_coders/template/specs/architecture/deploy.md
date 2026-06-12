# Architecture Spec — Deploy

## Stack de deploy

| Camada | Ferramenta | Decisão |
|--------|-----------|---------|
| VPS | Hostinger | Self-hosted, previsível, EU-compliant |
| Proxy / DNS / DDoS | Cloudflare | WAF, Turnstile, CDN sem custo adicional |
| Plataforma de deploy | Coolify (self-hosted) | Open-source, git-based, sem lock-in |
| IaC provisionamento | Terraform ≥ 1.9 | Estado versionado, `plan` antes de `apply` |
| Hardening OS | Ansible ≥ 2.17 | Idempotente, auditável |
| CD | GitHub Actions + GitHub Environments | Aprovação manual para prod |
| Cache / rate-limit | Redis 7 | Stateless em dev (in-memory); persistido em prod |

## Ambientes

### dev
- Deploy automático em todo push para `main`.
- URL: `https://dev.example.com` (configurar via `NEXT_PUBLIC_API_URL_DEV`).
- GitHub Environment: `dev` (sem revisores obrigatórios).

### prod
- Deploy em tags `v*.*.*`.
- **Requer aprovação manual** de pelo menos um revisor configurado no GitHub
  Environment `prod`.
- URL: `https://example.com` + `https://api.example.com`.

## Fluxo de CI/CD

```
push → CI (lint + types + tests + build + IaC validate) → OK?
                                                              │
                              ┌───────────────────────────────┘
                              │
          push main ──────────▶ deploy-dev.yml (auto)
          tag v*.*.* ─────────▶ deploy-prod.yml → aguarda aprovação → deploy
```

## Terraform

- **Não** usa `apply` no CI — só `fmt`, `validate`, `tflint`.
- `apply` manual por humano após `terraform plan` revisado.
- Estado remoto recomendado (ex: bucket S3 ou Terraform Cloud).
- Providers: `cloudflare/cloudflare` (DNS + WAF), `hashicorp/null` (Hostinger API
  + Coolify API via `local-exec`).

## Ansible

- Playbook `infra/ansible/playbooks/harden.yml`: SSH key-only, UFW, fail2ban,
  Docker, unattended-upgrades.
- Sempre rodar com `--check` antes de aplicar em prod.
- Nunca armazenar senhas no playbook — usar Ansible Vault ou variáveis de ambiente.

## Segredos

Todos os segredos de produção são injetados pelo Coolify e pelos GitHub Secrets.
Consulte `infra/secrets.example.env` para a lista completa.

**Hierarquia de segredos (nenhum vai para o repositório):**
1. GitHub Secrets → injetados pelos workflows de deploy.
2. Coolify env vars → injetados nas imagens Docker em runtime.
3. `infra/terraform/terraform.tfvars` → gitignored, nunca commitado.

## Networking

- Cloudflare fica na frente de tudo (modo proxy ativo).
- O backend escuta em `0.0.0.0:8000` mas só recebe conexões do proxy Cloudflare
  (UFW bloqueia acesso direto).
- Redis não é exposto externamente — só acessível pela rede Docker interna.
- Postgres não é exposto externamente em prod (porta fechada no UFW).

## Rollback

```bash
# Rollback para versão anterior via Coolify:
curl -X POST "$COOLIFY_URL/api/v1/deploy" \
  -H "Authorization: Bearer $COOLIFY_TOKEN" \
  -d '{"uuid":"APP_UUID","tag":"v1.2.3"}'
```
