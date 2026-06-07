# API documentation

Auto-generated reference for the backend. **Do not hand-edit** — run `/sdd-docs`
(or the CI docs job) to regenerate everything from the source.

- **API reference** — extracted from code docstrings via mkdocstrings.
- **ER diagram** — generated from the SQLAlchemy models.
- The **OpenAPI schema** (`openapi.json`) is the contract that drives the
  frontend's typed client (`npm run gen:api`).

```bash
uv run python scripts/dump_openapi.py   # openapi.json
uv run python scripts/gen_erd.py        # docs/erd.md
uv run mkdocs build --strict            # build this site
```
