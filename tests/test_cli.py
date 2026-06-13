"""Tests for the sdd-coders command-line interface."""

from __future__ import annotations

from pathlib import Path

import pytest
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
    assert "init" in result.stdout


def test_init_scaffolds_project(tmp_path: Path) -> None:
    dest = tmp_path / "demo-app"
    result = runner.invoke(app, ["init", str(dest)])
    assert result.exit_code == 0, result.stdout
    assert (dest / "backend" / "pyproject.toml").is_file()
    assert (dest / "frontend" / "package.json").is_file()
    assert (dest / "specs" / "constitution.md").is_file()
    # .jinja templates are rendered (suffix stripped) with the project name.
    claude = (dest / "CLAUDE.md").read_text(encoding="utf-8")
    assert "demo-app" in claude
    # node_modules / .venv are excluded from the render.
    assert not (dest / "frontend" / "node_modules").exists()


def test_init_with_explicit_name(tmp_path: Path) -> None:
    dest = tmp_path / "dir"
    result = runner.invoke(app, ["init", str(dest), "--name", "custom-name"])
    assert result.exit_code == 0, result.stdout
    assert "custom-name" in (dest / "CLAUDE.md").read_text(encoding="utf-8")


def test_doctor_reports_ok_when_tools_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sdd_coders.cli.shutil.which", lambda _tool: "/usr/bin/tool")
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Toolchain OK" in result.stdout


def test_doctor_reports_missing_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sdd_coders.cli.shutil.which", lambda _tool: None)
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "Missing tools" in result.stdout


def _setup_project(tmp_path: Path) -> None:
    """Create the minimum directory structure of a generated project."""
    (tmp_path / "specs" / "functional").mkdir(parents=True)
    (tmp_path / "specs" / "functional" / "_template.md").write_text("# Template", encoding="utf-8")
    (tmp_path / "backend" / "app" / "api" / "routes").mkdir(parents=True)
    (tmp_path / "backend" / "tests" / "integration").mkdir(parents=True)
    (tmp_path / "frontend" / "app").mkdir(parents=True)


def test_add_feature_creates_spec_and_stubs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["add-feature", "billing"])

    assert result.exit_code == 0
    assert (tmp_path / "specs" / "functional" / "billing.md").read_text(encoding="utf-8") == "# Template"
    assert (tmp_path / "backend" / "app" / "api" / "routes" / "billing.py").exists()
    assert (tmp_path / "frontend" / "app" / "billing" / "page.tsx").exists()
    assert (tmp_path / "backend" / "tests" / "integration" / "test_billing.py").exists()
    assert "billing" in result.stdout


def test_add_feature_creates_spec_only_when_no_stubs_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    functional = tmp_path / "specs" / "functional"
    functional.mkdir(parents=True)
    (functional / "_template.md").write_text("# Template", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["add-feature", "billing"])

    assert result.exit_code == 0
    assert (functional / "billing.md").exists()
    assert not (tmp_path / "backend").exists()
    assert not (tmp_path / "frontend").exists()


def test_add_feature_outside_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["add-feature", "billing"])
    assert result.exit_code == 1
