"""Minimal git driver: init the scaffolded repo and make the initial commit.

`gh repo create --source=. --push` requires an existing git repo with a commit, and
the local pre-commit hook expects git too — so every wizard project is initialized
and committed right after scaffolding. The dev `.env` is ignored by the template's
`.gitignore`, so it never enters the initial commit.
"""

from __future__ import annotations

from pathlib import Path

from sdd_coders.wizard.providers import Runner, default_runner


class GitError(RuntimeError):
    """A ``git`` command failed."""


class Git:
    def __init__(self, *, cwd: Path | None = None, runner: Runner = default_runner) -> None:
        self._cwd = cwd
        self._run = runner

    def _git(self, args: list[str], *, tolerate: tuple[str, ...] = ()) -> str:
        result = self._run(["git", *args], cwd=str(self._cwd) if self._cwd else None)
        if result.returncode != 0:
            combined = (result.stderr or "") + (result.stdout or "")
            if any(token in combined for token in tolerate):
                return combined.strip()
            raise GitError((result.stderr or "").strip() or f"git {args[0]} failed")
        return (result.stdout or "").strip()

    def init(self) -> None:
        self._git(["init", "-b", "main"])

    def add_all(self) -> None:
        self._git(["add", "-A"])

    def commit(self, message: str) -> None:
        # Tolerate a clean tree so re-runs (e.g. `configure`) don't fail.
        self._git(["commit", "-m", message], tolerate=("nothing to commit",))

    def init_commit(self, message: str) -> None:
        self.init()
        self.add_all()
        self.commit(message)
