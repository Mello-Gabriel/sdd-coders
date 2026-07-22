"""Ansible driver: runs the hardening playbook against a transient inventory.

The inventory (carrying the VPS IP) is written to the out-of-repo workspace, so the
production host address never lands in the generated repo.
"""

from __future__ import annotations

from pathlib import Path

from sdd_coders.wizard.providers import Runner, default_runner


class AnsibleError(RuntimeError):
    """An ``ansible-playbook`` run failed."""


def render_inventory(ansible_vars: dict[str, str]) -> str:
    """Build a one-host INI inventory from routed Ansible vars."""
    host = ansible_vars["host"]
    user = ansible_vars.get("ansible_user", "root")
    key = ansible_vars.get("ansible_ssh_private_key_file", "~/.ssh/id_ed25519")
    return (
        f"[vps]\nprod ansible_host={host} ansible_user={user} ansible_ssh_private_key_file={key}\n"
    )


class Ansible:
    def __init__(self, *, runner: Runner = default_runner) -> None:
        self._run = runner

    def run_playbook(self, playbook: Path, inventory: Path, *, cwd: Path | None = None) -> None:
        result = self._run(
            ["ansible-playbook", "-i", str(inventory), str(playbook)],
            cwd=str(cwd) if cwd else None,
        )
        if result.returncode != 0:
            raise AnsibleError((result.stderr or "").strip() or "ansible-playbook failed")
