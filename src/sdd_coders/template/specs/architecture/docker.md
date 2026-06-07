# Arquitetura — Docker & Deploy seguro

> Decorre da `constitution.md` §9. Imagens **mínimas, específicas e non-root**.

## Princípios

- **Multi-stage**: estágio de build separado do runtime. O runtime recebe só o
  artefato e as dependências de execução — **nada de compiladores, shells ou
  ferramentas de debug** que não sejam necessárias.
- **Base mínima**: `distroless` ou `*-slim`. Quanto menos houver na imagem, menor a
  superfície de ataque.
- **Non-root**: `USER` dedicado sem privilégios. Filesystem **read-only**
  (`read_only: true`) + `tmpfs` para escrita temporária. `cap_drop: [ALL]`.
- **`HEALTHCHECK`** ligado aos endpoints de readiness.
- **Sem segredos na imagem**: injetados em runtime (env/secret).

## Backend (FastAPI) — esboço

```dockerfile
# build
FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN uv sync --frozen --no-dev

# runtime
FROM gcr.io/distroless/python3-debian12:nonroot AS runtime
WORKDIR /app
COPY --from=build /app /app
USER nonroot
EXPOSE 8000
ENTRYPOINT ["/app/.venv/bin/python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Frontend (Next.js) — esboço

- `output: "standalone"` no `next.config`. Runtime em `node:*-slim`/distroless,
  non-root, copiando só `.next/standalone` + `.next/static` + `public`.

## Compose (dev)

`infra/docker-compose.yml`: serviços `db` (postgres), `backend`, `frontend`, com
healthchecks, rede isolada, volumes nomeados e variáveis de `.env`.

## CI

- Build das imagens + scan (`trivy`/`grype`). Falha o pipeline em CVE crítica.
