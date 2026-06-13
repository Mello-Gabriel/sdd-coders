"""Render the bundled template into a new project directory using Copier."""

from __future__ import annotations

from pathlib import Path

import copier

#: The template that ships inside the package (rendered by Copier).
TEMPLATE_DIR = Path(__file__).resolve().parent / "template"


def scaffold_project(destination: Path, project_name: str) -> None:
    """Copy and render the template into ``destination`` for ``project_name``."""
    copier.run_copy(
        str(TEMPLATE_DIR),
        str(destination),
        data={"project_name": project_name},
        defaults=True,
        quiet=True,
    )
