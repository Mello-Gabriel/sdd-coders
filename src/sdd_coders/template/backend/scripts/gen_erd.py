"""Generate a Mermaid ER diagram from the ORM metadata (no external deps).

Output: backend/docs/erd.md (rendered by MkDocs Material). Regenerate via `/sdd-docs`.
"""

from __future__ import annotations

from pathlib import Path

from app.models import Base


def render_mermaid() -> str:
    lines: list[str] = ["erDiagram"]
    for table in Base.metadata.sorted_tables:
        for foreign_key in table.foreign_keys:
            parent = foreign_key.column.table.name
            lines.append(f"  {parent} ||--o{{ {table.name} : has")
    for table in Base.metadata.sorted_tables:
        lines.append(f"  {table.name} {{")
        for column in table.columns:
            type_name = type(column.type).__name__
            lines.append(f"    {type_name} {column.name}")
        lines.append("  }")
    return "\n".join(lines)


def main() -> None:
    output = Path(__file__).resolve().parent.parent / "docs" / "erd.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    content = "# Database ER diagram\n\n```mermaid\n" + render_mermaid() + "\n```\n"
    output.write_text(content, encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
