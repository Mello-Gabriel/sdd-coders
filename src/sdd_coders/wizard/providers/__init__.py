"""Thin provider clients used by the wizard pipeline.

HTTP clients (Cloudflare/Coolify/Resend) accept an injectable ``httpx.Client`` and
subprocess clients (GitHub/Terraform/Ansible) accept an injectable ``Runner`` so the
whole pipeline is testable without touching the network or the shell.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Mapping, Sequence

#: A subprocess runner compatible with the wizard's needs (a ``subprocess.run`` shim).
Runner = Callable[..., "subprocess.CompletedProcess[str]"]


def default_runner(
    args: Sequence[str],
    *,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
    input: str | None = None,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Real subprocess runner (text output, never raises on non-zero)."""
    return subprocess.run(  # noqa: S603 - args are wizard-constructed, never shell
        list(args),
        cwd=cwd,
        env=dict(env) if env is not None else None,
        input=input,
        capture_output=capture_output,
        text=True,
        check=False,
    )
