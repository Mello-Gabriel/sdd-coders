"""Secret persistence (OS keychain) and environment scrubbing.

Secrets are persisted only to the OS keychain (via ``keyring``) — encrypted, outside
the repo, addressable per project for later rotation. ``scrub_env`` strips every
sensitive variable before the wizard launches Claude Code, so the AI process never
even inherits a production secret from its environment.
"""

from __future__ import annotations

import contextlib

import keyring
from keyring.errors import PasswordDeleteError

from sdd_coders.wizard.model import SECRET_FIELDS, WizardConfig
from sdd_coders.wizard.workspace import keyring_service

# A key is sensitive if it carries any of these substrings or prefixes.
_SENSITIVE_SUBSTRINGS: tuple[str, ...] = (
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "PASSWD",
    "API_KEY",
    "APIKEY",
    "CREDENTIAL",
    "PRIVATE_KEY",
)
_SENSITIVE_PREFIXES: tuple[str, ...] = (
    "TF_VAR_",
    "COOLIFY_",
    "CLOUDFLARE_",
    "HOSTINGER_",
    "RESEND_",
)


def is_sensitive_env(name: str) -> bool:
    """True if an env var name looks like it carries a secret/credential."""
    upper = name.upper()
    if any(upper.startswith(prefix) for prefix in _SENSITIVE_PREFIXES):
        return True
    return any(sub in upper for sub in _SENSITIVE_SUBSTRINGS)


def scrub_env(env: dict[str, str]) -> dict[str, str]:
    """Return a copy of ``env`` with all sensitive variables removed."""
    return {key: value for key, value in env.items() if not is_sensitive_env(key)}


def save_secrets(slug: str, cfg: WizardConfig) -> None:
    """Persist the config's non-empty secret fields to the OS keychain."""
    service = keyring_service(slug)
    for name in sorted(SECRET_FIELDS):
        value = getattr(cfg, name)
        if value:
            keyring.set_password(service, name, value)


def load_secrets(slug: str) -> dict[str, str]:
    """Read previously stored secret fields for a project from the OS keychain."""
    service = keyring_service(slug)
    loaded: dict[str, str] = {}
    for name in sorted(SECRET_FIELDS):
        value = keyring.get_password(service, name)
        if value is not None:
            loaded[name] = value
    return loaded


def delete_secrets(slug: str) -> None:
    """Remove all stored secrets for a project (best-effort)."""
    service = keyring_service(slug)
    for name in sorted(SECRET_FIELDS):
        with contextlib.suppress(PasswordDeleteError):
            keyring.delete_password(service, name)
