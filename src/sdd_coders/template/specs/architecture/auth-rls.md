# Arquitetura — Autenticação & RLS

> Decorre da `constitution.md` §5. **RLS é o mecanismo primário de isolamento de
> dados** — a aplicação nunca confia apenas em filtros no código.

## 1. Autenticação

- **Senha:** Argon2id (via `passlib`/`argon2-cffi`). Política mínima configurável.
- **Tokens:** JWT **access** (curto, ~15min) + **refresh** (longo, rotacionado).
  Ambos em cookies **`HttpOnly; Secure; SameSite=Lax`**. Refresh tem `jti` e é
  rastreado/revogável (tabela `refresh_tokens`); logout revoga.
- **Endpoints:** `POST /auth/register`, `/auth/login`, `/auth/refresh`,
  `/auth/logout`, `/auth/me`, fluxo de reset de senha com token expirável.
- **Proteções:** rate limit + lockout progressivo; timing-safe; mensagens genéricas
  (não revelam se e-mail existe).

## 2. Autorização

- Papéis: `user`, `admin` (extensível a permissões finas).
- Dependência `get_current_user` valida o access token e carrega o usuário.
- Dependência `require_admin` para rotas administrativas.

## 3. Row-Level Security (padrão **obrigatório**)

### 3.1 Roles do Postgres

- A aplicação conecta como role **`app_user`** criada **sem `BYPASSRLS`** e **sem
  superuser**. Migrations/owner usam role separada com mais privilégios.

### 3.2 Contexto por request

A cada request autenticado, dentro de **uma transação**, o backend injeta a
identidade no Postgres e as policies fazem o resto:

```sql
-- executado no início da transação (via SQLAlchemy)
SELECT set_config('app.current_user_id', :user_id, true);  -- 'true' = LOCAL à transação
SELECT set_config('app.current_role', :role, true);
```

### 3.3 Policies (versionadas em migrations)

```sql
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents FORCE ROW LEVEL SECURITY;

-- Usuário só enxerga/edita as próprias linhas...
CREATE POLICY documents_owner ON documents
  USING (owner_id = current_setting('app.current_user_id')::uuid);

-- ...exceto admin, que enxerga tudo.
CREATE POLICY documents_admin ON documents
  USING (current_setting('app.current_role', true) = 'admin');
```

### 3.4 Integração com SQLAlchemy (async)

`core/db.py` expõe um gerador de sessão que abre a transação e aplica o contexto:

```python
async def get_db(user: CurrentUser | None = ...) -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        async with session.begin():
            if user is not None:
                await session.execute(
                    text("SELECT set_config('app.current_user_id', :uid, true)"),
                    {"uid": str(user.id)},
                )
                await session.execute(
                    text("SELECT set_config('app.current_role', :role, true)"),
                    {"role": user.role},
                )
            yield session
```

> `set_config(..., true)` é **LOCAL** à transação: zero vazamento entre requests
> que compartilham conexões do pool.

## 4. Testes obrigatórios de RLS

- Usuário A **não** lê dados do usuário B (esperado: 0 linhas), via integração com
  Postgres real.
- Admin lê tudo.
- Tentativa de burlar via query direta com a role `app_user` falha.
- Cobertura de cada policy nova é requisito de merge.
