"""Dump the FastAPI OpenAPI schema to backend/openapi.json.

This file is the contract that drives the frontend's generated TypeScript client
(`npm run gen:api`). Regenerate via `/sdd-docs`.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.main import app


def main() -> None:
    schema = app.openapi()
    output = Path(__file__).resolve().parent.parent / "openapi.json"
    output.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
