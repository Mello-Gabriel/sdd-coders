"""Tests for workspace locations and secret storage / env scrubbing."""

from __future__ import annotations

from pathlib import Path

import pytest

from sdd_coders.wizard import workspace
from sdd_coders.wizard.model import WizardConfig
from sdd_coders.wizard.secrets_store import (
    delete_secrets,
    is_sensitive_env,
    load_secrets,
    save_secrets,
    scrub_env,
)
from tests.wizard.conftest import MemoryKeyring


def test_state_root_uses_xdg(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert workspace.state_root() == tmp_path / "sdd-coders"


def test_state_root_falls_back_to_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda _cls: tmp_path))
    assert workspace.state_root() == tmp_path / ".local" / "state" / "sdd-coders"


def test_project_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert workspace.project_state_dir("app") == tmp_path / "sdd-coders" / "app"
    assert workspace.terraform_workdir("app").name == "terraform"
    assert workspace.inventory_path("app").name == "inventory.ini"


def test_keyring_service() -> None:
    assert workspace.keyring_service("app") == "sdd-coders:app"


@pytest.mark.parametrize(
    "name",
    ["APP_JWT_SECRET", "COOLIFY_TOKEN", "CF_API_KEY", "TF_VAR_x", "db_password", "MY_CREDENTIAL"],
)
def test_is_sensitive_env_true(name: str) -> None:
    assert is_sensitive_env(name)


@pytest.mark.parametrize("name", ["PATH", "HOME", "APP_ENVIRONMENT", "NEXT_PUBLIC_API_URL"])
def test_is_sensitive_env_false(name: str) -> None:
    assert not is_sensitive_env(name)


def test_scrub_env_removes_secrets() -> None:
    scrubbed = scrub_env({"PATH": "/bin", "APP_JWT_SECRET": "s", "TF_VAR_coolify_token": "t"})
    assert scrubbed == {"PATH": "/bin"}


def test_save_load_delete_secrets(memory_keyring: MemoryKeyring) -> None:
    cfg = WizardConfig(
        project_name="app",
        jwt_secret="j",
        coolify_token="c",
        resend_api_key="",  # blank values are not stored
    )
    save_secrets("app", cfg)
    loaded = load_secrets("app")
    assert loaded == {"jwt_secret": "j", "coolify_token": "c"}

    delete_secrets("app")
    assert load_secrets("app") == {}
    # Deleting again is a no-op (PasswordDeleteError suppressed).
    delete_secrets("app")
