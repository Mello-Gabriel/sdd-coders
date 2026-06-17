"""Terraform driver: runs in an out-of-repo workdir with secrets via ``TF_VAR_*``.

Production tokens are passed only through the apply subprocess's environment and the
state file lives in the out-of-repo workdir — so neither the secrets nor the state
(which can contain sensitive attributes) ever enter the repo the AI works in.
"""

from __future__ import annotations

import os
from pathlib import Path

from sdd_coders.wizard.providers import Runner, default_runner


class TerraformError(RuntimeError):
    """A ``terraform`` command failed."""


class Terraform:
    def __init__(
        self,
        workdir: Path,
        *,
        env_base: dict[str, str] | None = None,
        runner: Runner = default_runner,
    ) -> None:
        self._workdir = workdir
        self._env_base = dict(env_base) if env_base is not None else dict(os.environ)
        self._run = runner

    def _exec(self, args: list[str], *, extra_env: dict[str, str] | None = None) -> str:
        env = dict(self._env_base)
        if extra_env:
            env.update(extra_env)
        result = self._run(["terraform", *args], cwd=str(self._workdir), env=env)
        if result.returncode != 0:
            raise TerraformError(
                (result.stderr or "").strip() or f"terraform {args[0]} failed"
            )
        return (result.stdout or "").strip()

    def init(self) -> None:
        self._exec(["init", "-input=false"])

    def validate(self) -> None:
        self._exec(["validate"])

    def apply(self, tf_vars: dict[str, str]) -> None:
        extra_env = {f"TF_VAR_{key}": value for key, value in tf_vars.items()}
        self._exec(["apply", "-auto-approve", "-input=false"], extra_env=extra_env)
