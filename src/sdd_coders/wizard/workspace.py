"""Where the wizard keeps things that must live *outside* the generated repo.

Terraform state and the Ansible inventory contain production values, so they are
written under the user's XDG state dir, never inside the project the AI works in.
"""

from __future__ import annotations

import os
from pathlib import Path


def state_root() -> Path:
    """Base dir for all wizard-managed, out-of-repo state."""
    xdg = os.environ.get("XDG_STATE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "state"
    return base / "sdd-coders"


def project_state_dir(slug: str) -> Path:
    """Per-project out-of-repo workspace (Terraform state, transient inventory)."""
    return state_root() / slug


def terraform_workdir(slug: str) -> Path:
    """Where the Terraform config is copied and applied (keeps state out of the repo)."""
    return project_state_dir(slug) / "terraform"


def inventory_path(slug: str) -> Path:
    """Transient Ansible inventory holding the VPS IP — outside the repo."""
    return project_state_dir(slug) / "inventory.ini"


def keyring_service(slug: str) -> str:
    """OS-keychain service name namespacing this project's secrets."""
    return f"sdd-coders:{slug}"
