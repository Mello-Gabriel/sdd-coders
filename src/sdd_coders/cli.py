"""Command-line interface for sdd-coders.

The CLI is the ``uv init`` analog for this project: ``sdd-coders init <dir>``
scaffolds a new production-grade fullstack repository from the bundled template
and wires up the spec-driven, multi-agent workflow.
"""

from __future__ import annotations

import re
import shutil
import textwrap
from pathlib import Path
from typing import Annotated

import typer

from sdd_coders import __version__
from sdd_coders.scaffold import scaffold_project, write_dev_env
from sdd_coders.wizard.themes import DEFAULT_THEME, THEME_KEYS, is_valid_theme

app = typer.Typer(
    name="sdd-coders",
    help=(
        "Spec-Driven Development base model: scaffold production-grade fullstack "
        "apps built by orchestrated AI agents."
    ),
    no_args_is_help=True,
)

REQUIRED_TOOLS = ("git", "uv", "node", "npm", "docker")

# Optional tools unlock extra workflows; their absence only disables features,
# so `doctor` warns about them instead of failing.
OPTIONAL_TOOLS = ("gh", "terraform", "ansible", "claude")

_OPTIONAL_FEATURES = {
    "gh": "the `new` wizard deploy pipeline (GitHub repo + secrets)",
    "terraform": "the `new` wizard deploy pipeline (IaC provisioning)",
    "ansible": "the `new` wizard deploy pipeline (server configuration)",
    "claude": "the AI agent launcher used by the `new` wizard interview",
}

# Project and feature names become directory/file paths and identifiers, so they
# are restricted to a safe slug (also blocks path traversal like "../etc").
_SLUG = re.compile(r"^[a-z][a-z0-9-]{1,62}$")


def _validate_slug(value: str, kind: str) -> str:
    if not _SLUG.match(value):
        typer.echo(
            f"Invalid {kind} '{value}': use lowercase letters, digits and hyphens "
            f"(start with a letter, 2-63 chars)."
        )
        raise typer.Exit(code=1)
    return value


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
    theme: Annotated[
        str, typer.Option("--theme", help="UI color theme (blue, neutral, violet, emerald, rose)")
    ] = DEFAULT_THEME,
) -> None:
    """Scaffold a new project from the template."""
    project_name = _validate_slug(name or path.name, "project name")
    if not is_valid_theme(theme):
        typer.echo(f"Invalid theme '{theme}': choose one of {', '.join(THEME_KEYS)}.")
        raise typer.Exit(code=1)
    scaffold_project(path, project_name, theme)
    write_dev_env(path)
    typer.echo(f"Created project '{project_name}' in {path}")
    typer.echo("Next steps:")
    typer.echo("  1. cd into it and `docker compose -f infra/docker-compose.yml up -d db`")
    typer.echo(
        "  2. create the first admin: `uv run python -m app.scripts.create_admin <email> <pw>`"
    )
    typer.echo("  3. open it in Claude Code and run /sdd-interview")


@app.command()
def new(
    path: Annotated[Path, typer.Argument(help="Directory for the new project")],
    name: Annotated[
        str | None, typer.Option("--name", help="Project name (default: directory name)")
    ] = None,
) -> None:
    """Open the wizard: scaffold, push prod secrets to their remote homes, launch Claude.

    Unlike ``init``, the wizard collects production secrets and pushes them straight to
    GitHub/Coolify/Cloudflare — they never touch the repo — then launches Claude Code
    with a scrubbed environment so no AI can read them.
    """
    project_name = _validate_slug(name or path.name, "project name")
    from sdd_coders.wizard.app import run_wizard  # noqa: PLC0415 (lazy: skip tkinter import)

    run_wizard(path, project_name)


@app.command()
def configure(
    path: Annotated[Path, typer.Argument(help="Existing project directory")],
) -> None:
    """Reopen the wizard for an existing project to rotate or update its secrets."""
    if not path.is_dir():
        typer.echo(f"No such project directory: {path}")
        raise typer.Exit(code=1)
    # `configure` no longer scaffolds, so a wrong path would silently push this
    # project's secrets for a repo that was never generated.
    if not (path / ".copier-answers.yml").is_file():
        typer.echo(
            f"{path} does not look like a generated project (.copier-answers.yml not found). "
            "Use `sdd-coders init` or `sdd-coders new` to create one first."
        )
        raise typer.Exit(code=1)
    project_name = _validate_slug(path.name, "project name")
    from sdd_coders.wizard.app import run_wizard  # noqa: PLC0415 (lazy: skip tkinter import)

    run_wizard(path, project_name, existing=True)


@app.command()
def doctor() -> None:
    """Check the toolchain: missing core tools fail, optional ones only warn."""
    missing_core = [tool for tool in REQUIRED_TOOLS if shutil.which(tool) is None]
    missing_optional = [tool for tool in OPTIONAL_TOOLS if shutil.which(tool) is None]
    for tool in missing_optional:
        typer.echo(
            f"Warning: optional tool '{tool}' not found — needed for {_OPTIONAL_FEATURES[tool]}."
        )
    if missing_core:
        typer.echo(f"Missing tools: {', '.join(missing_core)}")
        raise typer.Exit(code=1)
    if missing_optional:
        typer.echo("Core toolchain OK (optional tools missing — see warnings above)")
    else:
        typer.echo("Toolchain OK")


@app.command(name="add-feature")
def add_feature(
    name: Annotated[str, typer.Argument(help="Feature slug, e.g. billing")],
) -> None:
    """Create a functional spec + code stubs for a new feature (run inside a project)."""
    name = _validate_slug(name, "feature name")
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
    return textwrap.dedent(f"""\
        export default function {title.replace(" ", "")}Page() {{
          return (
            <main className="min-h-screen bg-background p-6">
              <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
              {{/* TODO: implement {title} */}}
            </main>
          );
        }}
    """)


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
