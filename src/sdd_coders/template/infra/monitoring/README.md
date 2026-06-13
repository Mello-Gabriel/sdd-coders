# Observabilidade

Os **três sinais** são tratados separadamente — métricas, logs e traces não são a
mesma coisa e não vão no mesmo lugar:

| Sinal | O que é | Origem | Ferramenta |
|-------|---------|--------|-----------|
| **Métricas** | números no tempo (latência, RPS, erros) | backend `/metrics` | **Prometheus** |
| **Logs** | eventos estruturados (JSON) | structlog → stdout | **Loki** (via Promtail) |
| **Host** | CPU/RAM/disco do VPS | kernel | **Node Exporter** |
| **Dashboards** | visualização + alertas | — | **Grafana** |

> ⚠️ **Logs não vão para o Prometheus.** Prometheus é só para métricas (séries
> numéricas). Logs vão para o Loki. Confundir os dois é um erro comum.

## Opção A — Grafana Cloud (recomendado)

Não rode nada no VPS. O **free tier do Grafana Cloud** já inclui Prometheus, Loki
e Tempo gerenciados. Vantagem: se o VPS cair, o monitoramento continua de pé.

1. Crie conta em [grafana.com](https://grafana.com) → free tier.
2. Pegue o endpoint remote-write do Prometheus e as credenciais do Loki.
3. Configure o backend/Promtail para empurrar via OTLP / remote-write
   (variáveis no `.env`).

## Opção B — Stack self-hosted no VPS

Pragmático para começar, com a ressalva acima. Sobe tudo via compose:

```bash
docker compose -f infra/monitoring/docker-compose.yml up -d
```

| Serviço | Porta (loopback) | Função |
|---------|------------------|--------|
| Grafana | `127.0.0.1:3001` | dashboards (login: admin / `GRAFANA_ADMIN_PASSWORD`) |
| Prometheus | `127.0.0.1:9090` | métricas |
| Loki | `127.0.0.1:3100` | logs |
| Node Exporter | — | métricas do host |
| Promtail | — | coleta logs dos containers → Loki |

Acesse o Grafana por um túnel SSH (as portas são loopback-only):

```bash
ssh -L 3001:127.0.0.1:3001 deploy@<IP_DO_VPS>
# abra http://localhost:3001
```

Os datasources (Prometheus + Loki) já vêm provisionados. Importe dashboards
prontos pelo ID no grafana.com: **1860** (Node Exporter Full) e
**FastAPI/Prometheus** para a aplicação.

### Apontar o Prometheus para o backend

`prometheus.yml` raspa `host.docker.internal:8000/metrics`. Se o backend roda em
outra rede/host, ajuste o `target` do job `backend`.

## O que o backend expõe

- **`GET /metrics`** — formato Prometheus (contadores de request, latência por
  rota, requests em andamento). Adicionado por `prometheus-fastapi-instrumentator`.
- **Logs JSON** no stdout via `structlog`, com `request_id` por request
  (`app/core/logging.py`). O Promtail lê o stdout dos containers e manda pro Loki,
  já parseando `level` e `event`.
