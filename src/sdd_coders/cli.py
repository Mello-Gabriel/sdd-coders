"""Command-line interface for sdd-coders.

The CLI is the ``uv init`` analog for this project: ``sdd-coders init <dir>``
scaffolds a new production-grade fullstack repository from the bundled template
and wires up the spec-driven, multi-agent workflow.
"""

from __future__ import annotations

import shutil
import textwrap
from pathlib import Path
from typing import Annotated

import typer

from sdd_coders import __version__
from sdd_coders.scaffold import scaffold_project

app = typer.Typer(
    name="sdd-coders",
    help=(
        "Spec-Driven Development base model: scaffold production-grade fullstack "
        "apps built by orchestrated AI agents."
    ),
    no_args_is_help=True,
)

REQUIRED_TOOLS = ("git", "uv", "node", "npm", "docker")


@app.callback()
def _root() -> None:
    """Spec-Driven Development base model for production-grade fullstack apps."""
    # Group-level callback so subcommands are invoked by name.


@app.command()
def version() -> None:
    """Print the installed sdd-coders version."""
    typer.echo(__version__)


@app.command()
def init(
    path: Annotated[Path, typer.Argument(help="Directory for the new project")],
    name: Annotated[
        str | None, typer.Option("--name", help="Project name (default: directory name)")
    ] = None,
) -> None:
    """Scaffold a new project from the template."""
    project_name = name or path.name
    scaffold_project(path, project_name)
    typer.echo(f"Created project '{project_name}' in {path}")
    typer.echo("Next: open it in Claude Code and run /sdd-interview")


@app.command()
def doctor() -> None:
    """Check that the required toolchain is installed."""
    missing = [tool for tool in REQUIRED_TOOLS if shutil.which(tool) is None]
    if missing:
        typer.echo(f"Missing tools: {', '.join(missing)}")
        raise typer.Exit(code=1)
    typer.echo("Toolchain OK")


@app.command(name="add-feature")
def add_feature(
    name: Annotated[str, typer.Argument(help="Feature slug, e.g. billing")],
) -> None:
    """Create a functional spec + code stubs for a new feature (run inside a project)."""
    template = Path("specs/functional/_template.md")
    if not template.exists():
        typer.echo("Run this inside a generated project (specs/functional/_template.md not found)")
        raise typer.Exit(code=1)

    target = Path(f"specs/functional/{name}.md")
    target.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    typer.echo(f"Created spec: {target}")

    backend_routes = Path("backend/app/api/routes")
    if backend_routes.is_dir():
        router_file = backend_routes / f"{name}.py"
        router_file.write_text(_backend_router_stub(name), encoding="utf-8")
        typer.echo(f"Created stub: {router_file}")

    frontend_app = Path("frontend/app")
    if frontend_app.is_dir():
        page_dir = frontend_app / name
        page_dir.mkdir(exist_ok=True)
        page_file = page_dir / "page.tsx"
        page_file.write_text(_frontend_page_stub(name), encoding="utf-8")
        typer.echo(f"Created stub: {page_file}")

    backend_tests = Path("backend/tests/integration")
    if backend_tests.is_dir():
        test_file = backend_tests / f"test_{name}.py"
        test_file.write_text(_backend_test_stub(name), encoding="utf-8")
        typer.echo(f"Created stub: {test_file}")


def _backend_router_stub(name: str) -> str:
    return textwrap.dedent(f'''\
        """{name.replace("-", " ").title()} endpoints."""

        from __future__ import annotations

        from fastapi import APIRouter

        from app.api.deps import CurrentUser, UserSession

        router = APIRouter(prefix="/{name}", tags=["{name}"])


        # TODO: implement {name} endpoints
        # Example:
        #
        # @router.get("")
        # async def list_{name.replace("-", "_")}(
        #     session: UserSession, current_user: CurrentUser
        # ) -> list[dict]:
        #     return []
    ''')


def _frontend_page_stub(name: str) -> str:
    title = name.replace("-", " ").title()
    return textwrap.dedent(f'''\
        export default function {title.replace(" ", "")}Page() {{
          return (
            <main className="min-h-screen bg-background p-6">
              <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
              {{/* TODO: implement {title} */}}
            </main>
          );
        }}
    ''')


def _backend_test_stub(name: str) -> str:
    return textwrap.dedent(f'''\
        """Integration tests for {name} endpoints."""

        from __future__ import annotations

        import pytest


        # TODO: add integration tests for the /{name} endpoints.
        # Follow the pattern in test_projects.py — use the owner_client fixture
        # and assert status codes, response shapes, and RLS isolation.
    ''')


if __name__ == "__main__":  # pragma: no cover
    app()
