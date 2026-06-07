# Arquitetura — Observabilidade

> Decorre da `constitution.md` §8. Nada vai a produção sem logs, métricas e traces.

## Logs

- **structlog** em **JSON**. Campos mínimos: `timestamp`, `level`, `event`,
  `request_id`, `trace_id`, `user_id` (quando houver), `route`, `status`, `latency_ms`.
- **Correlação**: middleware gera/propaga `request_id` (header `X-Request-ID`) e o
  vincula ao `trace_id` do OpenTelemetry.
- **Sem PII** desnecessária (ver LGPD §3).

## Métricas

- **OpenTelemetry** → exporter Prometheus (`/metrics`). RED/USE:
  - Latência (histograma) por rota, taxa de requests, taxa de erros.
  - Saturação: pool de conexões, fila, uso de CPU/memória do processo.
- Métricas de negócio relevantes definidas por feature (spec §10).

## Tracing

- Instrumentação automática de FastAPI, SQLAlchemy e httpx. Spans propagam do
  frontend (quando aplicável) ao backend e ao banco.

## Health

- `GET /health/live` (processo vivo) e `GET /health/ready` (DB e dependências ok).
- Usados pelos `HEALTHCHECK` do Docker e pelo orquestrador.

## SLOs

- Definir por projeto (ex.: p99 < 300ms em rotas críticas, erro < 1%). Alertas
  ligados aos SLOs.
