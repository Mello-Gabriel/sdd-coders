# Guia de Setup — Novo Projeto

Este guia cobre **tudo que precisa ser feito uma vez** ao criar um projeto novo
a partir do `sdd-coders`: segredos, e-mail, Cloudflare, VPS, Coolify e domínio.
Execute na ordem — cada passo depende do anterior.

> ## ⚡ Caminho recomendado: o wizard
>
> A maior parte deste guia é **automatizada** por `uvx sdd-coders new <app>`. O
> wizard abre uma janela nativa, coleta os segredos (gerando JWT/DB/Redis
> sozinho, resolvendo Zone ID e UUIDs por API), faz o scaffold e **empurra os
> segredos direto para GitHub/Coolify/Cloudflare** — eles nunca tocam o repo —
> roda Terraform/Ansible com o *state* fora do repositório, e por fim abre o
> Claude já na entrevista, com o ambiente higienizado. Você ainda precisa ter
> contas/tokens nos provedores (passos 1–7 abaixo descrevem onde obtê-los), mas
> não precisa colar nada em arquivo nem rodar `gh`/`terraform` na mão.
>
> Use `sdd-coders configure <app>` para reabrir o wizard e rotacionar segredos.
> O restante deste guia é a **referência manual** (e o fallback headless via
> `sdd-coders init`).

---

## Visão geral do fluxo

```
Domínio → Cloudflare (DNS + Turnstile)
         → Hostinger VPS (criar servidor)
              → Ansible (hardening SSH/UFW/fail2ban/Docker)
                   → Coolify (instalar + criar apps dev/prod)
                        → Resend (e-mail verificado)
                        → Google Analytics (GA4 Consent Mode)
                        → Secrets (.env local + GitHub)
                             → Terraform (apply)
                                  → Primeiro deploy (tag v0.1.0)
```

---

## Pré-requisitos

Instale as ferramentas uma vez na sua máquina de trabalho:

```bash
# Terraform ≥ 1.9
brew install terraform          # macOS
# ou: https://developer.hashicorp.com/terraform/install

# Ansible ≥ 2.17
pip install ansible

# tflint (validador Terraform)
brew install tflint

# ansible-lint
pip install ansible-lint

# GitHub CLI (para criar Environments via CLI)
brew install gh && gh auth login
```

---

## Passo 1 — Domínio

1. Compre (ou transfira) o domínio — **Hostinger Domínios** ou qualquer registrar.
2. Anote o domínio: `example.com` (usado em todos os passos seguintes).
3. Você vai apontar os nameservers para o Cloudflare no Passo 2.

---

## Passo 2 — Cloudflare

### 2.1 Criar conta e adicionar zona

1. Acesse [dash.cloudflare.com](https://dash.cloudflare.com) → **Add a Site**.
2. Digite `example.com` → plano **Free**.
3. Copie os 2 nameservers fornecidos pelo Cloudflare (ex.: `aida.ns.cloudflare.com`).
4. No painel do seu registrar, substitua os nameservers pelos do Cloudflare.
   - Propagação: até 24h, geralmente < 30min.

### 2.2 Pegar o Zone ID

Dashboard do Cloudflare → seu domínio → barra lateral direita → **Zone ID**.  
Anote: é o `CLOUDFLARE_ZONE_ID`.

### 2.3 Criar API Token

1. [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens) → **Create Token**.
2. Use o template **"Edit zone DNS"** → selecione sua zona.
3. Adicione permissão extra: **Zone > Firewall Services > Edit** (para o WAF/Turnstile).
4. Copie o token. Anote: é o `CLOUDFLARE_API_TOKEN`.

### 2.4 Criar widget Turnstile (captcha)

1. Cloudflare dashboard → **Turnstile** (menu esquerdo) → **Add site**.
2. Nome: `myapp-prod`, domínio: `example.com`.
3. Tipo: **Managed** (recomendado — adaptativo).
4. Copie:
   - **Site Key** → `NEXT_PUBLIC_TURNSTILE_SITE_KEY` (vai no frontend)
   - **Secret Key** → `APP_TURNSTILE_SECRET_KEY` (vai no backend)
5. Repita para `myapp-dev` com domínio `dev.example.com` (ou use o mesmo widget em dev com localhost adicionado).

> **Dev/teste local:** adicione `localhost` como domínio permitido no widget dev —
> o Turnstile aceita localhost sem validação real quando `APP_TURNSTILE_ENABLED=false`.

---

## Passo 3 — Hostinger VPS

### 3.1 Criar o VPS

1. [hPanel](https://hpanel.hostinger.com) → **VPS** → **Create new VPS**.
2. Configuração mínima recomendada: **KVM 2** (2 vCPU, 8 GB RAM, 100 GB NVMe).
3. Sistema operacional: **Ubuntu 24.04 LTS**.
4. Região: escolha a mais próxima dos seus usuários.
5. Adicione sua **chave SSH pública** durante a criação (ou via hPanel após).
   ```bash
   cat ~/.ssh/id_ed25519.pub   # sua chave pública
   ```
6. Anote o **IP do VPS** — usado em todo o resto.

### 3.2 Criar API key do Hostinger (para Terraform)

1. hPanel → **API** → **Manage API Tokens** → **Create new token**.
2. Escopo mínimo: `vps:read`, `vps:write`.
3. Anote: é o `HOSTINGER_API_KEY`.

---

## Passo 4 — Ansible: hardening do VPS

O playbook `infra/ansible/playbooks/harden.yml` configura:
- UFW (firewall): só 22/80/443 abertos
- fail2ban (brute-force SSH)
- SSH: apenas chave, sem senha, sem root
- Docker instalado para o usuário `deploy`
- Atualizações de segurança automáticas

### 4.1 Criar inventory

Crie `infra/ansible/inventory/hosts.ini`:

```ini
[vps]
prod ansible_host=<IP_DO_VPS> ansible_user=root ansible_ssh_private_key_file=~/.ssh/id_ed25519
```

> Use `root` apenas na primeira execução (o playbook cria o usuário `deploy`).
> Após rodar, mude para `ansible_user=deploy`.

### 4.2 Rodar o playbook

```bash
cd infra/ansible
ansible-playbook -i inventory/hosts.ini playbooks/harden.yml
```

Após concluir, teste o acesso:

```bash
ssh -i ~/.ssh/id_ed25519 deploy@<IP_DO_VPS>
```

---

## Passo 5 — Coolify: instalação e apps

O Coolify é o painel de deploy self-hosted. Roda no próprio VPS.

### 5.1 Instalar Coolify

```bash
ssh deploy@<IP_DO_VPS>
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

Aguarde ~2min. Acesse: `http://<IP_DO_VPS>:8000` → crie a conta admin.

### 5.2 Configurar domínio do Coolify

1. No Cloudflare, crie um registro A:
   - Nome: `coolify`, Valor: `<IP_DO_VPS>`, Proxy: **DNS only** (nuvem cinza).
2. No Coolify → **Settings** → **Instance Domain**: `https://coolify.example.com`.
3. Habilite SSL (Let's Encrypt automático).

### 5.3 Criar um projeto e dois ambientes

1. Coolify → **Projects** → **New Project** → nome: `myapp`.
2. Dentro do projeto → **Environments** → crie `dev` e `prod`.

### 5.4 Criar as 4 aplicações (backend + frontend × dev + prod)

Para cada app:
1. **New Resource** → **Docker Image** (ou **Git** se preferir build no Coolify).
2. Configurações mínimas:
   - **Source**: `ghcr.io/<seu-usuario>/myapp/backend:dev` (ou `:prod`)
   - **Port**: backend `8000`, frontend `3000`
   - **Domain**: veja tabela abaixo
3. Adicione as variáveis de ambiente (veja Passo 7).
4. Salve e **Deploy** uma vez para gerar o UUID.

| App | Ambiente | Domínio sugerido |
|-----|----------|-----------------|
| backend | dev | `api-dev.example.com` |
| frontend | dev | `dev.example.com` |
| backend | prod | `api.example.com` |
| frontend | prod | `example.com` |

### 5.5 Pegar os UUIDs das aplicações

Cada app criada tem um UUID visível na URL do Coolify:
`https://coolify.example.com/project/xxx/environment/yyy/application/**UUID**`

Anote os 4 UUIDs:
- `COOLIFY_DEV_BACKEND_UUID`
- `COOLIFY_DEV_FRONTEND_UUID`
- `COOLIFY_PROD_BACKEND_UUID`
- `COOLIFY_PROD_FRONTEND_UUID`

### 5.6 Criar API token do Coolify

Coolify → **Settings** → **API Tokens** → **New token**.  
Anote: é o `COOLIFY_TOKEN`.

---

## Passo 6 — E-mail: Resend

O template usa [Resend](https://resend.com) como provider de e-mail transacional
(verificação de conta, reset de senha). Você também pode usar SMTP no lugar.

### 6.1 Criar conta e verificar domínio

1. [resend.com](https://resend.com) → crie conta → **Domains** → **Add Domain**.
2. Digite `example.com` → Resend mostra registros DNS para adicionar.
3. No Cloudflare, adicione os registros exatamente como mostrado (SPF, DKIM, DMARC).
4. Clique em **Verify** no Resend — aguarde até virar verde (< 5min com Cloudflare).

### 6.2 Criar API key

Resend → **API Keys** → **Create API Key**.  
Escopo: **Full Access** (ou `emails:send` apenas).  
Anote: é o `APP_RESEND_API_KEY`.

### 6.3 Configurar remetente

No backend, o remetente padrão é `noreply@example.com`. Certifique-se que o domínio
verificado corresponde.  
Para alterar: `APP_EMAIL_FROM=noreply@example.com` (adicione ao `.env`/Coolify).

> **Alternativa SMTP:** defina `APP_EMAIL_PROVIDER=smtp` e as variáveis:
> `APP_SMTP_HOST`, `APP_SMTP_PORT`, `APP_SMTP_USER`, `APP_SMTP_PASSWORD`.

---

## Passo 7 — Google Analytics 4

O componente `GoogleAnalytics` **só carrega após consentimento** da categoria
`analytics`. Sem `NEXT_PUBLIC_GA_ID` no env, ele não monta.

### 7.1 Criar propriedade GA4

1. [analytics.google.com](https://analytics.google.com) → **Admin** → **Create** → **Property**.
2. Nome: `myapp-prod`, fuso horário e moeda corretos.
3. Em **Data Streams** → **Add stream** → **Web** → URL: `https://example.com`.
4. Copie o **Measurement ID** (formato `G-XXXXXXXXXX`).  
   Anote: é o `NEXT_PUBLIC_GA_ID`.

### 7.2 Configurar Consent Mode v2 (obrigatório LGPD/GDPR)

O componente já implementa Google Consent Mode v2 — ele define
`analytics_storage: denied` por padrão e atualiza quando o usuário consente.
Nenhuma configuração extra necessária no código.

No GA4: **Admin → Data Settings → Data Collection** → habilite
**Consent Mode** e **Modeling for consented users**.

---

## Passo 8 — Secrets: `.env` local e GitHub

### 8.1 `.env` local (desenvolvimento)

```bash
cp infra/secrets.example.env .env
```

Preencha todos os `CHANGE_ME`. Valores mínimos para rodar localmente:

```env
POSTGRES_PASSWORD=qualquer_senha_forte
APP_DATABASE_URL=postgresql+asyncpg://app_user:qualquer_senha_forte@localhost:55432/app
ALEMBIC_DATABASE_URL=postgresql+asyncpg://postgres:qualquer_senha_forte@localhost:55432/app
REDIS_PASSWORD=qualquer_senha_forte
APP_REDIS_URL=redis://:qualquer_senha_forte@localhost:6379/0
APP_JWT_SECRET=gere_32_chars_aleatorios_aqui
APP_EMAIL_PROVIDER=memory        # não precisa de Resend em dev
APP_TURNSTILE_ENABLED=false      # desativa captcha em dev
APP_FRONTEND_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Gere o JWT secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 8.2 GitHub Secrets (para CI/CD)

No repositório GitHub → **Settings** → **Secrets and variables** → **Actions** →
**New repository secret**. Adicione:

| Secret | Valor |
|--------|-------|
| `COOLIFY_URL` | `https://coolify.example.com` |
| `COOLIFY_TOKEN` | token criado no Passo 5.6 |
| `COOLIFY_DEV_BACKEND_UUID` | UUID do Passo 5.5 |
| `COOLIFY_DEV_FRONTEND_UUID` | UUID do Passo 5.5 |
| `COOLIFY_PROD_BACKEND_UUID` | UUID do Passo 5.5 |
| `COOLIFY_PROD_FRONTEND_UUID` | UUID do Passo 5.5 |

### 8.3 GitHub Variables (públicas, não sensíveis)

**Settings → Secrets and variables → Actions → Variables**:

| Variable | Valor |
|----------|-------|
| `NEXT_PUBLIC_API_URL_DEV` | `https://api-dev.example.com` |
| `NEXT_PUBLIC_API_URL_PROD` | `https://api.example.com` |
| `NEXT_PUBLIC_GA_ID` | `G-XXXXXXXXXX` |
| `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | site key do Passo 2.4 |

### 8.4 GitHub Environments

Crie dois ambientes para controle de deploy:

```bash
# Ambiente dev (sem aprovação — deploy automático)
gh api repos/:owner/:repo/environments/dev -X PUT \
  -f wait_timer=0

# Ambiente prod (aprovação manual obrigatória)
gh api repos/:owner/:repo/environments/prod -X PUT \
  -f wait_timer=0 \
  --field 'reviewers[][type]=User' \
  --field 'reviewers[][id]=<seu_github_user_id>'
```

Ou via interface: **Settings → Environments → New environment** → `prod` →
**Required reviewers** → adicione seu usuário.

### 8.5 Variáveis de ambiente no Coolify

Para cada app no Coolify, adicione as variáveis via **Environment Variables**:

**Backend (dev e prod)**:
```
APP_DATABASE_URL=postgresql+asyncpg://app_user:<senha>@postgres:5432/app
APP_JWT_SECRET=<mesmo valor do .env>
APP_REDIS_URL=redis://:<senha_redis>@redis:6379/0
APP_EMAIL_PROVIDER=resend
APP_RESEND_API_KEY=<sua_key>
APP_FRONTEND_URL=https://example.com
APP_TURNSTILE_ENABLED=true
APP_TURNSTILE_SECRET_KEY=<secret_key_turnstile>
```

**Frontend (dev e prod)**:
```
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_TURNSTILE_SITE_KEY=<site_key_turnstile>
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
```

---

## Passo 9 — Terraform: provisionar infra

### 9.1 Preencher tfvars

```bash
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
```

Edite com os valores coletados nos passos anteriores:

```hcl
app_name = "myapp"
domain   = "example.com"

# O VPS é criado manualmente no Passo 3; cole o IP aqui.
vps_ip = "<IP_DO_VPS>"

# Provisionamento automático do VPS via API da Hostinger é opt-in (off por
# default). O caminho suportado é o VPS manual acima.
manage_vps         = false
hostinger_api_key  = "" # só necessário se manage_vps = true
hostinger_vps_plan = "KVM 2"
hostinger_region   = "eu-west-1"

cloudflare_api_token = "<CLOUDFLARE_API_TOKEN>"
cloudflare_zone_id   = "<CLOUDFLARE_ZONE_ID>"
turnstile_secret_key = "<APP_TURNSTILE_SECRET_KEY>"

coolify_url   = "https://coolify.example.com"
coolify_token = "<COOLIFY_TOKEN>"
```

> `terraform.tfvars` está no `.gitignore` — **nunca commite esse arquivo**.

### 9.2 Inicializar e aplicar

```bash
cd infra/terraform
terraform init
terraform fmt -check      # deve passar
terraform validate        # deve passar
terraform plan            # revise o que será criado
terraform apply           # confirme com 'yes'
```

O Terraform vai:
- Criar registros DNS A (`@` e `api`) no Cloudflare apontando para o VPS
- Criar regra WAF/Turnstile nos endpoints de auth
- Criar ambientes dev/prod no Coolify

> **Nota:** Hostinger e Coolify usam `null_resource` (REST API via curl).
> Se o VPS já existe (criado manualmente no Passo 3), o módulo `hostinger`
> pode ser ignorado comentando o bloco em `infra/terraform/main.tf`.

---

## Passo 10 — Primeiro deploy

### 10.1 Deploy de dev (automático)

Qualquer push para `main` dispara o workflow `deploy-dev.yml`:

```bash
git push origin main
```

Acompanhe em: **GitHub → Actions → Deploy — dev**.

### 10.2 Deploy de prod (tag + aprovação manual)

```bash
git tag v0.1.0
git push origin v0.1.0
```

1. GitHub Actions abre o workflow `deploy-prod.yml`.
2. Fica aguardando aprovação no **Environment `prod`**.
3. O revisor configurado recebe notificação por e-mail/GitHub.
4. Após aprovar, as imagens são publicadas no GHCR e o Coolify faz o deploy.

### 10.3 Verificar saúde

```bash
curl https://api.example.com/health
# {"status":"ok","db":"ok","redis":"ok"}
```

### 10.4 Criar o primeiro admin

O cadastro normal cria sempre um usuário comum. Para criar/promover o admin
inicial, rode dentro do container backend (ou localmente com as creds de prod):

```bash
uv run python -m app.scripts.create_admin admin@example.com 'umaSenhaForte123'
```

O comando é idempotente (cria ou promove) e já marca o e-mail como verificado.

---

## Passo 10.5 — Observabilidade (opcional)

Métricas, logs e traces são **sinais distintos**: métricas→Prometheus,
logs→Loki, traces→Tempo. **Logs não vão para o Prometheus.**

- **Recomendado:** Grafana Cloud (free tier) — gerenciado, sobrevive à queda do VPS.
- **Self-hosted:** `docker compose -f infra/monitoring/docker-compose.yml up -d`
  (Prometheus + Grafana + Loki + Promtail + Node Exporter). Detalhes e o túnel SSH
  para o Grafana em `infra/monitoring/README.md`.

O backend já expõe `GET /metrics` (Prometheus) e loga JSON estruturado por request.

---

## Passo 10.6 — Backup do banco

O compose tem um serviço de backup opt-in (pg_dump diário, retenção 7 dias):

```bash
docker compose -f infra/docker-compose.yml --profile backup up -d backup
```

Restaurar um dump:

```bash
gunzip -c /caminho/do/backup.sql.gz | \
  docker compose -f infra/docker-compose.yml exec -T db psql -U postgres app
```

> **Atenção (Docker × UFW):** o Docker publica portas direto no iptables,
> furando o UFW. Por isso o compose faz bind em `127.0.0.1` e o Ansible escreve
> `/etc/docker/daemon.json` com `{"ip":"127.0.0.1"}`. Exponha serviços ao mundo
> **apenas** via Cloudflare/Coolify, nunca publicando a porta direto.

---

## Checklist final

- [ ] Domínio comprado e nameservers apontando para Cloudflare
- [ ] Cloudflare: zona ativa, Zone ID anotado, API token criado
- [ ] Turnstile: widgets criados (dev + prod), site key e secret key anotados
- [ ] VPS criado no Hostinger, SSH configurado com chave pública
- [ ] Ansible rodado: UFW/fail2ban/Docker configurados, usuário `deploy` criado
- [ ] Coolify instalado, domínio configurado com SSL
- [ ] Projeto, ambientes (dev/prod) e 4 apps criados no Coolify
- [ ] UUIDs das 4 apps anotados
- [ ] API token do Coolify criado
- [ ] Resend: conta criada, domínio verificado (SPF/DKIM/DMARC), API key coletada
- [ ] GA4: propriedade criada, Measurement ID anotado, Consent Mode habilitado
- [ ] `.env` local preenchido (JWT secret gerado)
- [ ] GitHub Secrets e Variables configurados (9 itens)
- [ ] GitHub Environments: `dev` (sem aprovação) e `prod` (aprovação manual)
- [ ] Variáveis de ambiente adicionadas em cada app no Coolify (backend + frontend)
- [ ] `terraform.tfvars` preenchido e `terraform apply` executado
- [ ] Push para `main` → deploy de dev passou
- [ ] Tag `v0.1.0` criada → aprovação dada → deploy de prod passou
- [ ] `GET /health` retorna `{"status":"ok","db":"ok","redis":"ok"}`
- [ ] Login, verificação de e-mail e Turnstile funcionando em prod

---

## Solução de problemas frequentes

**Deploy falha com `401 Unauthorized` no Coolify**  
→ Verifique se `COOLIFY_TOKEN` está correto e não expirou.

**E-mail de verificação não chega**  
→ Confirme que o domínio está verificado no Resend (SPF/DKIM verdes).  
→ Cheque `APP_EMAIL_PROVIDER=resend` e `APP_RESEND_API_KEY` no Coolify.

**Turnstile sempre falha em dev**  
→ Defina `APP_TURNSTILE_ENABLED=false` no `.env` local.  
→ Em staging, adicione `localhost` como domínio permitido no widget.

**`terraform apply` falha no módulo Hostinger**  
→ O VPS já foi criado manualmente? Comente o módulo `hostinger` em `main.tf`
  e aplique apenas Cloudflare + Coolify.

**`next build` falha com erro de tipo**  
→ Rode `npm run typecheck` localmente antes de fazer push.  
→ O CI bloqueia merge se `tsc --noEmit` falhar.
