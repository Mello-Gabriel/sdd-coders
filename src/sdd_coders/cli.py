"""Command-line interface for sdd-coders.

The CLI is the ``uv init`` analog for this project: it scaffolds a new
production-grade fullstack repository from the bundled template and wires up the
spec-driven, multi-agent workflow. Subcommands are added incrementally per the
implementation roadmap (``init``, ``add-feature``, ``doctor``).
"""

from __future__ import annotations

import typer

from sdd_coders import __version__

app = typer.Typer(
    name="sdd-coders",
    help=(
        "Spec-Driven Development base model: scaffold production-grade fullstack "
        "apps built by orchestrated AI agents."
    ),
    no_args_is_help=True,
)


@app.callback()
def _root() -> None:
    """Spec-Driven Development base model for production-grade fullstack apps."""
    # Group-level callback: keeps the app a multi-command group so subcommands
    # are invoked by name (e.g. `sdd-coders version`) rather than collapsed.


@app.command()
def version() -> None:
    """Print the installed sdd-coders version."""
    typer.echo(__version__)


if __name__ == "__main__":  # pragma: no cover
    app()
