"""Tests for `sdd-coders adopt` — installing the workflow into an existing repo."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from sdd_coders.adopt import ADOPT_ASSETS_DIR, CopyReport, adopt_project, copy_tree
from sdd_coders.cli import app

runner = CliRunner()


def make_repo(tmp_path: Path) -> Path:
    """A minimal existing project: a git repo with its own file."""
    repo = tmp_path / "legacy-app"
    (repo / ".git").mkdir(parents=True)
    (repo / "main.py").write_text("print('hi')\n", encoding="utf-8")
    return repo


def test_copy_tree_reports_added_and_skips_existing(tmp_path: Path) -> None:
    src = tmp_path / "src"
    (src / "nested").mkdir(parents=True)
    (src / "nested" / "a.txt").write_text("new", encoding="utf-8")
    (src / "b.txt").write_text("new", encoding="utf-8")
    dst = tmp_path / "dst"
    dst.mkdir()
    (dst / "b.txt").write_text("mine", encoding="utf-8")

    report = copy_tree(src, dst, base=dst)

    assert report.added == [Path("nested/a.txt")]
    assert report.skipped == [Path("b.txt")]
    assert report.overwritten == []
    # The pre-existing file is untouched.
    assert (dst / "b.txt").read_text(encoding="utf-8") == "mine"


def test_copy_tree_force_overwrites(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "b.txt").write_text("new", encoding="utf-8")
    dst = tmp_path / "dst"
    dst.mkdir()
    (dst / "b.txt").write_text("mine", encoding="utf-8")

    report = copy_tree(src, dst, base=dst, force=True)

    assert report.overwritten == [Path("b.txt")]
    assert report.added == []
    assert (dst / "b.txt").read_text(encoding="utf-8") == "new"


def test_copy_report_extend_merges_all_buckets() -> None:
    first = CopyReport(added=[Path("a")], skipped=[Path("b")], overwritten=[Path("c")])
    first.extend(CopyReport(added=[Path("d")], skipped=[Path("e")], overwritten=[Path("f")]))

    assert first.added == [Path("a"), Path("d")]
    assert first.skipped == [Path("b"), Path("e")]
    assert first.overwritten == [Path("c"), Path("f")]


def test_adopt_project_installs_agents_skills_hooks_and_specs(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)

    adopt_project(repo)

    assert (repo / ".claude" / "agents" / "orchestrator.md").is_file()
    # The two skills a brownfield repo starts from, plus the rest of the pipeline.
    assert (repo / ".claude" / "skills" / "sdd-constitution" / "SKILL.md").is_file()
    assert (repo / ".claude" / "skills" / "sdd-import" / "SKILL.md").is_file()
    assert (repo / ".claude" / "skills" / "sdd-specify" / "SKILL.md").is_file()
    assert (repo / ".claude" / "settings.json").is_file()
    assert (repo / "specs" / "constitution.md").is_file()
    assert (repo / "specs" / "functional" / "_template.md").is_file()
    # The repo's own code is left alone.
    assert (repo / "main.py").read_text(encoding="utf-8") == "print('hi')\n"


def test_adopt_installs_the_stack_agnostic_constitution_not_the_template_one(
    tmp_path: Path,
) -> None:
    repo = make_repo(tmp_path)

    adopt_project(repo)

    constitution = (repo / "specs" / "constitution.md").read_text(encoding="utf-8")
    assert "TODO" in constitution  # a starter to fill in, not a decided stack
    assert "FastAPI" not in constitution
    assert "/sdd-constitution" in constitution


def test_adopt_keeps_hook_scripts_executable(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)

    adopt_project(repo)

    for name in ("pre-commit-gate.sh", "secret-guard.sh"):
        hook = repo / ".claude" / "hooks" / name
        assert hook.stat().st_mode & stat.S_IXUSR, name


def test_adopt_installs_a_gate_hook_that_is_not_stack_specific(tmp_path: Path) -> None:
    """The template gate no-ops without backend/ or frontend/ — adopt must not ship that."""
    repo = make_repo(tmp_path)

    adopt_project(repo)

    gate = (repo / ".claude" / "hooks" / "pre-commit-gate.sh").read_text(encoding="utf-8")
    assert "backend/pyproject.toml" not in gate
    assert "frontend/package.json" not in gate
    assert ".claude/gate.sh" in gate


def test_adopt_settings_deny_secrets_without_allowlisting_an_unknown_toolchain(
    tmp_path: Path,
) -> None:
    repo = make_repo(tmp_path)

    adopt_project(repo)

    settings = json.loads((repo / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "Read(./.env)" in settings["permissions"]["deny"]
    # An adopted repo's toolchain is unknown, so nothing is pre-approved.
    assert "allow" not in settings["permissions"]


def test_adopt_is_non_destructive_by_default(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text('{"mine": true}', encoding="utf-8")

    report = adopt_project(repo)

    assert Path(".claude/settings.json") in report.skipped
    assert (repo / ".claude" / "settings.json").read_text(encoding="utf-8") == '{"mine": true}'


def test_adopt_force_overwrites_settings(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text('{"mine": true}', encoding="utf-8")

    report = adopt_project(repo, force=True)

    assert Path(".claude/settings.json") in report.overwritten
    assert (repo / ".claude" / "settings.json").read_text(encoding="utf-8") != '{"mine": true}'


def test_adopt_command_reports_and_points_at_sdd_constitution(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)

    result = runner.invoke(app, ["adopt", str(repo)])

    assert result.exit_code == 0, result.stdout
    assert "added" in result.stdout
    assert "/sdd-constitution" in result.stdout
    assert "Warning" not in result.stdout  # it is a git repo


def test_adopt_command_defaults_to_the_current_directory(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    cwd = Path.cwd()
    os.chdir(repo)
    try:
        result = runner.invoke(app, ["adopt"])
    finally:
        os.chdir(cwd)

    assert result.exit_code == 0, result.stdout
    assert (repo / "specs" / "constitution.md").is_file()


def test_adopt_command_warns_when_not_a_git_repo(tmp_path: Path) -> None:
    repo = tmp_path / "plain"
    repo.mkdir()

    result = runner.invoke(app, ["adopt", str(repo)])

    assert result.exit_code == 0, result.stdout
    assert "not a git repository" in result.stdout


def test_adopt_command_fails_on_missing_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["adopt", str(tmp_path / "nope")])

    assert result.exit_code == 1
    assert "No such directory" in result.stdout


def test_adopt_command_reports_a_no_op_second_run(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    runner.invoke(app, ["adopt", str(repo)])

    result = runner.invoke(app, ["adopt", str(repo)])

    assert result.exit_code == 0, result.stdout
    assert "Nothing to do" in result.stdout
    assert "skipped" in result.stdout


def test_adopt_command_force_rewrites_everything(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    runner.invoke(app, ["adopt", str(repo)])

    result = runner.invoke(app, ["adopt", str(repo), "--force"])

    assert result.exit_code == 0, result.stdout
    assert "overwritten" in result.stdout


def test_adopt_assets_ship_with_the_package() -> None:
    """Guards against the assets dir being dropped from the wheel."""
    assert (ADOPT_ASSETS_DIR / "specs" / "constitution.md").is_file()
    assert (ADOPT_ASSETS_DIR / "specs" / "README.md").is_file()
    assert (ADOPT_ASSETS_DIR / ".claude" / "settings.json").is_file()
    assert (ADOPT_ASSETS_DIR / ".claude" / "hooks" / "pre-commit-gate.sh").is_file()


def run_gate(repo: Path, command: str) -> subprocess.CompletedProcess[str]:
    """Drive the installed commit gate the way Claude Code would."""
    return subprocess.run(  # noqa: S603
        ["bash", str(repo / ".claude" / "hooks" / "pre-commit-gate.sh")],  # noqa: S607
        input=json.dumps({"tool_input": {"command": command}}),
        capture_output=True,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo)},
        check=False,
    )


def test_gate_hook_ignores_commands_that_are_not_commits(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    adopt_project(repo)

    result = run_gate(repo, "ls -la")

    assert result.returncode == 0
    assert result.stderr == ""


def test_gate_hook_warns_but_allows_commits_before_the_gate_is_configured(
    tmp_path: Path,
) -> None:
    repo = make_repo(tmp_path)
    adopt_project(repo)

    result = run_gate(repo, "git commit -m 'wip'")

    assert result.returncode == 0  # adopting must not wedge commits on day one
    assert "/sdd-constitution" in result.stderr


def test_gate_hook_blocks_the_commit_when_the_project_gate_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    adopt_project(repo)
    (repo / ".claude" / "gate.sh").write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")

    result = run_gate(repo, "git commit -m 'wip'")

    assert result.returncode == 2  # exit 2 is what makes Claude Code block the tool
    assert "Commit bloqueado" in result.stderr


def test_gate_hook_allows_the_commit_when_the_project_gate_passes(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    adopt_project(repo)
    (repo / ".claude" / "gate.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")

    result = run_gate(repo, "git commit -m 'wip'")

    assert result.returncode == 0
