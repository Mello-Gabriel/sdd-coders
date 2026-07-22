# sdd-deploy

Gerencia o ciclo de deploy: provisiona infra via Terraform, hardeniza via Ansible,
e dispara deploys dev/prod via Coolify. Use para configurar um novo ambiente, fazer
deploy de uma release, ou depurar uma pipeline de CD.

## Quando usar
- Provisionar infra pela primeira vez (Terraform apply)
- Fazer deploy de uma release para `dev` ou `prod`
- Depurar falha em `deploy-dev.yml` ou `deploy-prod.yml`
- Adicionar/alterar variáveis de ambiente em um ambiente Coolify
- Rodar hardening Ansible em um VPS novo

## Pré-requisitos

```bash
# Ferramentas necessárias (verificar com `sdd-coders doctor`)
terraform   >= 1.9
ansible     >= 2.17
gh          >= 2.0      # GitHub CLI (para secrets e environments)
curl / jq              # para a Coolify API
```

## Fluxo de deploy inicial

### 1. Terraform — provisionar infra
```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# edite terraform.tfvars com suas credenciais reais

terraform init
terraform plan   # revise o output — nada é aplicado ainda
terraform apply  # confirme após revisar
```

### 2. Ansible — hardening do VPS
```bash
cd infra/ansible
# edite inventory.ini com o IP do VPS
ansible-playbook -i inventory.ini playbooks/harden.yml --check  # dry-run
ansible-playbook -i inventory.ini playbooks/harden.yml          # aplica
```

### 3. Coolify — configurar environments
```bash
# Via API ou dashboard do Coolify:
# - Criar environment "dev" (auto-deploy) e "prod" (manual)
# - Apontar para os repositórios Docker das imagens
# - Injetar variáveis de ambiente (ver infra/secrets.example.env)
```

### 4. GitHub — configurar secrets e environments
```bash
# Secrets necessários em GitHub → Settings → Secrets:
gh secret set COOLIFY_TOKEN
gh secret set COOLIFY_DEV_APP_ID
gh secret set COOLIFY_PROD_APP_ID
gh secret set CLOUDFLARE_ZONE_ID

# Environment "prod" com required reviewer:
# GitHub → Settings → Environments → prod → Required reviewers
```

## Deploy de uma release
```bash
# Dev (automático no push para main):
git push origin main

# Prod (manual via release tag):
git tag v1.0.0
git push origin v1.0.0
# → abre pull de aprovação no GitHub Environment "prod"
```

## Variáveis de ambiente

Consulte `infra/secrets.example.env` para a lista completa. As variáveis de produção
**nunca** ficam no repositório — apenas no Coolify e nos GitHub Secrets.

| Variável | Ambiente | Descrição |
|----------|----------|-----------|
| `APP_DATABASE_URL` | prod/dev | asyncpg connection string |
| `APP_JWT_SECRET` | prod/dev | segredo de assinatura JWT |
| `APP_REDIS_URL` | prod | URI do Redis |
| `APP_RESEND_API_KEY` | prod | chave da API Resend |
| `APP_TURNSTILE_SECRET_KEY` | prod | segredo server-side do Turnstile |
| `NEXT_PUBLIC_API_URL` | prod/dev | URL pública do backend |
| `NEXT_PUBLIC_GA_ID` | prod | Measurement ID do Google Analytics |
| `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | prod | site key do Turnstile |
