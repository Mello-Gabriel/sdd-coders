# Arquitetura — Observabilidade

> Decorre da `constitution.md` §8. Os **três sinais são distintos**: métricas,
> logs e traces não vão no mesmo lugar. Stack e configs em `infra/monitoring/`.

| Sinal | Origem | Coletor | Backend de armazenamento |
| --- | --- | --- | --- |
| Métricas | `GET /metrics` (Prometheus format) | Prometheus (scrape) | Prometheus / Grafana Cloud |
| Logs | structlog JSON no stdout | Promtail | Loki / Grafana Cloud |
| Traces | OpenTelemetry (opcional) | OTLP collector | Tempo / Grafana Cloud |

> **Logs não vão para o Prometheus.** Prometheus é só métricas. Logs → Loki.

## Logs

- **structlog** em **JSON** (`app/core/logging.py`). Campos: `timestamp`, `level`,
  `event`, `request_id` (e `trace_id`/`user_id` quando houver), `method`, `path`,
  `status`.
- **Correlação**: o middleware gera/propaga `request_id` (header `X-Request-ID`) e
  o vincula via `structlog.contextvars` a todas as linhas do request.
- **Coleta**: Promtail lê o stdout dos containers e envia ao Loki, parseando
  `level`/`event`. **Sem PII** desnecessária (ver LGPD §3).

## Métricas

- **`/metrics`** exposto por `prometheus-fastapi-instrumentator`. RED/USE:
  - Latência (histograma) por rota, taxa de requests, taxa de erros, in-progress.
  - Saturação do host via **Node Exporter** (CPU/RAM/disco).
- Métricas de negócio relevantes definidas por feature (spec §10).

## Tracing (opcional)

- OpenTelemetry (FastAPI, SQLAlchemy, httpx) exportando via OTLP para Tempo /
  Grafana Cloud. Habilitado por projeto; o starter já correlaciona por `request_id`.

## Onde rodar

- **Recomendado:** Grafana Cloud (free tier) — Prometheus + Loki + Tempo
  gerenciados; sobrevive à queda do VPS.
- **Alternativa:** stack self-hosted (`infra/monitoring/docker-compose.yml`:
  Prometheus + Grafana + Loki + Promtail + Node Exporter) no próprio VPS.

## Health

- `GET /health/live` (processo vivo) e `GET /health/ready` (DB e dependências ok).
- Usados pelos `HEALTHCHECK` do Docker e pelo orquestrador.

## SLOs

- Definir por projeto (ex.: p99 < 300ms em rotas críticas, erro < 1%). Alertas
  ligados aos SLOs.
