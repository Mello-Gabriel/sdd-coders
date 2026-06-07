"""Tests for the sdd-coders command-line interface."""

from __future__ import annotations

from typer.testing import CliRunner

from sdd_coders import __version__
from sdd_coders.cli import app

runner = CliRunner()


def test_version_command_prints_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout
    assert "version" in result.stdout
