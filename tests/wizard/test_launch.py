"""Tests for launching Claude with a scrubbed environment."""

from __future__ import annotations

from pathlib import Path

import pytest

from sdd_coders.wizard.launch import build_child_env, launch_claude
from tests.wizard.conftest import FakeRunner


def test_build_child_env_strips_secrets() -> None:
    env = build_child_env({"PATH": "/bin", "COOLIFY_TOKEN": "x", "APP_JWT_SECRET": "y"})
    assert env == {"PATH": "/bin"}


def test_build_child_env_defaults_to_os_environ(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HARMLESS_MARKER", "1")
    monkeypatch.setenv("SOME_SECRET", "leak")
    env = build_child_env()
    assert env["HARMLESS_MARKER"] == "1"
    assert "SOME_SECRET" not in env


def test_launch_claude_runs_with_scrubbed_env(tmp_path: Path) -> None:
    runner = FakeRunner(returncode=0)
    code = launch_claude(
        tmp_path,
        base_env={"PATH": "/bin", "CLOUDFLARE_API_TOKEN": "secret"},
        runner=runner,
    )
    assert code == 0
    call = runner.calls[0]
    assert call.args == ["claude", "/sdd-interview"]
    assert call.cwd == str(tmp_path)
    assert "CLOUDFLARE_API_TOKEN" not in (call.env or {})


def test_launch_claude_without_interview(tmp_path: Path) -> None:
    runner = FakeRunner()
    launch_claude(tmp_path, interview=False, base_env={"PATH": "/bin"}, runner=runner)
    assert runner.calls[0].args == ["claude"]
