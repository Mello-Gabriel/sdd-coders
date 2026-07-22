"""Tests for the sdd-coders command-line interface."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sdd_coders import __main__ as main_module
from sdd_coders import __version__
from sdd_coders.cli import OPTIONAL_TOOLS, app
from sdd_coders.scaffold import write_dev_env

runner = CliRunner()


def test_python_module_entrypoint_runs_version() -> None:
    assert main_module.__name__ == "sdd_coders.__main__"  # import must not start the CLI

    result = subprocess.run(
        [sys.executable, "-m", "sdd_coders", "version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert __version__ in result.stdout


def test_write_dev_env_does_not_overwrite_existing(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("EXISTING=1", encoding="utf-8")
    write_dev_env(tmp_path)
    assert (tmp_path / ".env").read_text(encoding="utf-8") == "EXISTING=1"


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
    # A working local-dev .env is generated with a fresh JWT secret, and the
    # Copier answers file is written so `copier update` works later.
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "APP_JWT_SECRET=" in env
    assert "APP_JWT_SECRET=\n" not in env  # non-empty
    assert (dest / ".copier-answers.yml").is_file()


def test_init_with_explicit_name(tmp_path: Path) -> None:
    dest = tmp_path / "dir"
    result = runner.invoke(app, ["init", str(dest), "--name", "custom-name"])
    assert result.exit_code == 0, result.stdout
    assert "custom-name" in (dest / "CLAUDE.md").read_text(encoding="utf-8")


def test_init_rejects_invalid_name(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path / "dir"), "--name", "../evil"])
    assert result.exit_code == 1
    assert "Invalid project name" in result.stdout


def test_init_applies_chosen_theme(tmp_path: Path) -> None:
    dest = tmp_path / "themed-app"
    result = runner.invoke(app, ["init", str(dest), "--theme", "violet"])
    assert result.exit_code == 0, result.stdout
    css = (dest / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
    assert "262.1 83.3% 57.8%" in css  # violet primary token
    assert not (dest / "frontend" / "app" / "globals.css.jinja").exists()


def test_init_rejects_invalid_theme(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path / "dir"), "--theme", "chartreuse"])
    assert result.exit_code == 1
    assert "Invalid theme" in result.stdout


def test_new_command_launches_wizard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    def fake_run_wizard(path: Path, name: str, **kwargs: object) -> None:
        calls["path"] = path
        calls["name"] = name
        calls["kwargs"] = kwargs

    monkeypatch.setattr("sdd_coders.wizard.app.run_wizard", fake_run_wizard)
    result = runner.invoke(app, ["new", str(tmp_path / "demo-app")])
    assert result.exit_code == 0, result.stdout
    assert calls["name"] == "demo-app"


def test_new_rejects_invalid_name(tmp_path: Path) -> None:
    result = runner.invoke(app, ["new", str(tmp_path / "dir"), "--name", "../evil"])
    assert result.exit_code == 1
    assert "Invalid project name" in result.stdout


def test_configure_launches_wizard_for_existing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "demo-app"
    project.mkdir()
    captured: dict[str, object] = {}

    def fake_run_wizard(path: Path, name: str, **kwargs: object) -> None:
        captured["existing"] = kwargs.get("existing")

    monkeypatch.setattr("sdd_coders.wizard.app.run_wizard", fake_run_wizard)
    result = runner.invoke(app, ["configure", str(project)])
    assert result.exit_code == 0, result.stdout
    assert captured["existing"] is True


def test_configure_missing_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["configure", str(tmp_path / "nope")])
    assert result.exit_code == 1
    assert "No such project" in result.stdout


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


def test_doctor_warns_but_passes_when_optional_tools_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sdd_coders.cli.shutil.which",
        lambda tool: None if tool in OPTIONAL_TOOLS else "/usr/bin/tool",
    )
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Warning: optional tool 'gh' not found" in result.stdout
    assert "deploy pipeline" in result.stdout
    assert "Warning: optional tool 'claude' not found" in result.stdout
    assert "Core toolchain OK" in result.stdout


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
    assert (tmp_path / "specs" / "functional" / "billing.md").read_text(
        encoding="utf-8"
    ) == "# Template"
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


def test_add_feature_rejects_invalid_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["add-feature", "../evil"])
    assert result.exit_code == 1
    assert "Invalid feature name" in result.stdout
