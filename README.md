# sdd-coders

**Modelo base Spec-Driven para apps fullstack prontos para produção.**

`sdd-coders` é um _engine_ de scaffolding (análogo ao `uv init`) que replica um
modelo completo e opinativo para construir sistemas fullstack **seguros, rápidos,
escaláveis, padronizados e observáveis** — desenvolvidos por **múltiplos agentes
de IA especializados, coordenados por um orquestrador**.

A arquitetura é **fixa por default** (ver [`constitution.md`](src/sdd_coders/template/specs/constitution.md));
cada projeto novo só descreve suas necessidades **funcionais** numa grande
**entrevista** na primeira interação com o repositório gerado.

## Stack padrão

- **Frontend:** Next.js (App Router) + React + TypeScript + Tailwind/shadcn
- **Backend:** Python 3.13 + FastAPI + Pydantic v2 (gerenciado por **uv**)
- **Banco:** PostgreSQL com **Row-Level Security (RLS) sempre**
- **Auth:** self-hosted no FastAPI (Argon2 + JWT) com RLS por request
- **Qualidade:** 100% de cobertura (unit) back e front, integração + Playwright E2E,
  `ruff`/`mypy --strict`/`biome`, CI completo, Docker endurecido, observabilidade,
  LGPD, área de admin, auditoria e **documentação automatizada**.

## Uso (alvo)

```bash
uvx sdd-coders init meu-app
cd meu-app
# abra no Claude Code e rode /sdd-interview
```

## Status

Em construção — ver o roadmap de fases (F0–F7) no arquivo de plano do projeto.

## Licença

MIT
