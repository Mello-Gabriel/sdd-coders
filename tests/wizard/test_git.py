"""Tests for the minimal git driver."""

from __future__ import annotations

from pathlib import Path

import pytest

from sdd_coders.wizard.providers.git import Git, GitError
from tests.wizard.conftest import FakeRunner


def test_init_commit_sequence() -> None:
    runner = FakeRunner()
    Git(cwd=Path("/repo"), runner=runner).init_commit("Initial commit")
    calls = [c.args for c in runner.calls]
    assert calls == [
        ["git", "init", "-b", "main"],
        ["git", "add", "-A"],
        ["git", "commit", "-m", "Initial commit"],
    ]
    assert runner.calls[0].cwd == "/repo"


def test_commit_tolerates_clean_tree() -> None:
    runner = FakeRunner(returncode=1, stdout="nothing to commit, working tree clean")
    # Should not raise even though git returned non-zero.
    Git(runner=runner).commit("noop")


def test_commit_raises_on_real_failure() -> None:
    runner = FakeRunner(returncode=1, stderr="fatal: bad thing")
    with pytest.raises(GitError, match="bad thing"):
        Git(runner=runner).commit("x")


def test_init_default_error_message() -> None:
    runner = FakeRunner(returncode=128, stderr="")
    with pytest.raises(GitError, match="git init failed"):
        Git(runner=runner).init()


def test_no_cwd() -> None:
    runner = FakeRunner()
    Git(runner=runner).add_all()
    assert runner.calls[0].cwd is None
