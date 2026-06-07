---
name: sdd-docs
description: Regenerate documentation as a build artifact — the OpenAPI-derived TypeScript API client, the mkdocstrings reference, the database ER diagram, and the changelog. Run after a feature is verified, or whenever the API/schema changes.
---

# /sdd-docs

Documentação é **artefato de build** (constituição §11). Delegue ao **`docs-writer`**.

## Como agir
1. **Cliente TS**: regenere `frontend/lib/api/` do **OpenAPI** do backend
   (openapi-typescript/orval). Tipos devem bater com a API atual.
2. **Referência**: `mkdocs build --strict` (MkDocs Material + mkdocstrings a partir
   das docstrings); publica specs e ADRs. Corrija links quebrados (link-check).
3. **Diagrama ER**: regenere das models/migrations.
4. **Changelog**: atualize a partir dos Conventional Commits.

## Saída
- Docs construídas sem erro/links quebrados; cliente TS sincronizado; changelog atual.
