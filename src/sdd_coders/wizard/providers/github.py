"""GitHub provisioning via the ``gh`` CLI.

Secret values are passed on **stdin**, never as command-line arguments, so they
never appear in the process table. The wizard pushes them straight to repo/Env
secrets and variables — they are not written to the repo.
"""

from __future__ import annotations

from pathlib import Path

from sdd_coders.wizard.providers import Runner, default_runner


class GitHubError(RuntimeError):
    """A ``gh`` command failed."""


class GitHubCLI:
    def __init__(self, *, cwd: Path | None = None, runner: Runner = default_runner) -> None:
        self._cwd = cwd
        self._run = runner

    def _gh(self, args: list[str], *, stdin: str | None = None) -> str:
        result = self._run(
            ["gh", *args],
            cwd=str(self._cwd) if self._cwd else None,
            input=stdin,
        )
        if result.returncode != 0:
            raise GitHubError((result.stderr or "").strip() or f"gh {' '.join(args)} failed")
        return (result.stdout or "").strip()

    def auth_ok(self) -> bool:
        """True if ``gh`` is authenticated."""
        result = self._run(["gh", "auth", "status"], cwd=None, input=None)
        return result.returncode == 0

    def create_repo(self, slug: str, *, private: bool = True) -> None:
        """Create the GitHub repo from the current dir and push the initial commit."""
        visibility = "--private" if private else "--public"
        self._gh(["repo", "create", slug, visibility, "--source=.", "--push"])

    def set_secret(self, name: str, value: str, *, environment: str | None = None) -> None:
        args = ["secret", "set", name]
        if environment:
            args += ["--env", environment]
        self._gh(args, stdin=value)

    def set_variable(self, name: str, value: str, *, environment: str | None = None) -> None:
        args = ["variable", "set", name]
        if environment:
            args += ["--env", environment]
        self._gh(args, stdin=value)

    def ensure_environment(self, repo: str, name: str) -> None:
        """Create (idempotently) a deployment Environment on the repo."""
        self._gh(["api", "-X", "PUT", f"repos/{repo}/environments/{name}"])
