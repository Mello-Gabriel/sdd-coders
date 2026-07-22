"""Launch Claude Code into the discovery interview with a scrubbed environment.

This is the final isolation boundary: the AI process is started in the repo (which
holds only throwaway dev values) with every sensitive variable stripped from its
environment, so it cannot read a production secret even from its own ``os.environ``.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Mapping
from pathlib import Path

from sdd_coders.wizard.providers import Runner, default_runner
from sdd_coders.wizard.secrets_store import scrub_env


def build_child_env(base: Mapping[str, str] | None = None) -> dict[str, str]:
    """The environment Claude is launched with — the caller's env minus all secrets."""
    source = dict(base) if base is not None else dict(os.environ)
    return scrub_env(source)


def launch_claude(
    repo: Path,
    *,
    interview: bool = True,
    base_env: Mapping[str, str] | None = None,
    runner: Runner = default_runner,
) -> int:
    """Start ``claude`` in ``repo`` with a scrubbed env; returns its exit code."""
    if shutil.which("claude") is None:
        raise SystemExit(
            "Claude Code is not installed ('claude' not found in PATH). Install it "
            "from https://claude.com/claude-code, or run the /sdd-interview "
            "interview manually inside the generated project."
        )
    args = ["claude"]
    if interview:
        args.append("/sdd-interview")
    result = runner(
        args,
        cwd=str(repo),
        env=build_child_env(base_env),
        capture_output=False,
    )
    return result.returncode
