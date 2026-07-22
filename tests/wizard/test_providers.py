"""Tests for the provider clients (HTTP via MockTransport, shell via FakeRunner)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import httpx
import pytest

from sdd_coders.wizard import providers
from sdd_coders.wizard.providers.ansible import Ansible, AnsibleError, render_inventory
from sdd_coders.wizard.providers.cloudflare import CloudflareClient
from sdd_coders.wizard.providers.coolify import CoolifyClient
from sdd_coders.wizard.providers.github import GitHubCLI, GitHubError
from sdd_coders.wizard.providers.resend import ResendClient
from sdd_coders.wizard.providers.terraform import Terraform, TerraformError
from tests.wizard.conftest import FakeRunner, mock_client

# --- default_runner --------------------------------------------------------------


def test_default_runner_invokes_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["args"] = args
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args, 0, "out", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = providers.default_runner(["echo", "hi"], cwd="/tmp", env={"A": "1"}, input="x")
    assert result.stdout == "out"
    assert captured["kwargs"]["text"] is True
    assert captured["kwargs"]["check"] is False
    assert captured["kwargs"]["env"] == {"A": "1"}


def test_default_runner_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    providers.default_runner(["ls"])
    assert captured["kwargs"]["env"] is None


# --- Cloudflare ------------------------------------------------------------------


def test_cloudflare_verify_active() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"success": True, "result": {"status": "active"}})

    assert CloudflareClient("t", client=mock_client(handler)).verify() is True


def test_cloudflare_verify_inactive_and_error() -> None:
    def inactive(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"success": True, "result": {"status": "disabled"}})

    def error(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"success": False})

    assert CloudflareClient("t", client=mock_client(inactive)).verify() is False
    assert CloudflareClient("t", client=mock_client(error)).verify() is False


def test_cloudflare_zone_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["name"] == "example.com"
        return httpx.Response(200, json={"result": [{"id": "zone-1"}]})

    assert CloudflareClient("t", client=mock_client(handler)).zone_id("example.com") == "zone-1"


def test_cloudflare_zone_id_missing() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": []})

    with pytest.raises(LookupError, match="no Cloudflare zone"):
        CloudflareClient("t", client=mock_client(handler)).zone_id("example.com")


def test_cloudflare_default_client_constructs() -> None:
    # Just exercises the `client or httpx.Client(...)` default branch.
    assert CloudflareClient("t") is not None


# --- Coolify ---------------------------------------------------------------------


def test_coolify_verify() -> None:
    assert (
        CoolifyClient(
            "https://c",
            "t",
            client=mock_client(lambda _r: httpx.Response(200, json={"version": "4"})),
        ).verify()
        is True
    )
    assert (
        CoolifyClient("https://c", "t", client=mock_client(lambda _r: httpx.Response(401))).verify()
        is False
    )


def test_coolify_resolve_uuids() -> None:
    apps = [
        {"uuid": "u1", "name": "app-backend-prod"},
        {"uuid": "u2", "name": "app-frontend-prod"},
    ]
    client = CoolifyClient(
        "https://c", "t", client=mock_client(lambda _r: httpx.Response(200, json=apps))
    )
    resolved = client.resolve_uuids({"prod_backend": "app-backend-prod", "missing": "nope"})
    assert resolved == {"prod_backend": "u1"}


def test_coolify_set_env() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.read().decode()
        return httpx.Response(200, json={})

    CoolifyClient("https://c", "t", client=mock_client(handler)).set_env("uX", {"K": "V"})
    assert "/applications/uX/envs/bulk" in seen["url"]
    assert "K" in seen["body"]


def test_coolify_set_env_raises_on_error() -> None:
    client = CoolifyClient("https://c", "t", client=mock_client(lambda _r: httpx.Response(500)))
    with pytest.raises(httpx.HTTPStatusError):
        client.set_env("uX", {"K": "V"})


def test_coolify_default_client_constructs() -> None:
    assert CoolifyClient("https://c", "t") is not None


# --- Resend ----------------------------------------------------------------------


def test_resend_verify() -> None:
    assert ResendClient("k", client=mock_client(lambda _r: httpx.Response(200))).verify() is True
    assert ResendClient("k", client=mock_client(lambda _r: httpx.Response(401))).verify() is False
    assert ResendClient("k") is not None


# --- GitHub ----------------------------------------------------------------------


def test_github_auth_ok() -> None:
    assert GitHubCLI(runner=FakeRunner(returncode=0)).auth_ok() is True
    assert GitHubCLI(runner=FakeRunner(returncode=1)).auth_ok() is False


def test_github_create_repo() -> None:
    runner = FakeRunner()
    GitHubCLI(cwd=Path("/repo"), runner=runner).create_repo("app")
    args = runner.calls[0].args
    assert args[:3] == ["gh", "repo", "create"]
    assert "--private" in args
    assert runner.calls[0].cwd == "/repo"


def test_github_create_repo_public() -> None:
    runner = FakeRunner()
    GitHubCLI(runner=runner).create_repo("app", private=False)
    assert "--public" in runner.calls[0].args
    assert runner.calls[0].cwd is None


def test_github_set_secret_uses_stdin() -> None:
    runner = FakeRunner()
    GitHubCLI(runner=runner).set_secret("TOKEN", "s3cr3t", environment="prod")
    call = runner.calls[0]
    assert call.args == ["gh", "secret", "set", "TOKEN", "--env", "prod"]
    assert call.input == "s3cr3t"  # value on stdin, never in argv
    assert "s3cr3t" not in call.args


def test_github_set_secret_no_env() -> None:
    runner = FakeRunner()
    GitHubCLI(runner=runner).set_secret("TOKEN", "s")
    assert runner.calls[0].args == ["gh", "secret", "set", "TOKEN"]


def test_github_set_variable_no_env() -> None:
    runner = FakeRunner()
    GitHubCLI(runner=runner).set_variable("NEXT_PUBLIC_X", "v")
    assert runner.calls[0].args == ["gh", "variable", "set", "NEXT_PUBLIC_X"]


def test_github_set_variable_with_env() -> None:
    runner = FakeRunner()
    GitHubCLI(runner=runner).set_variable("NEXT_PUBLIC_X", "v", environment="prod")
    assert runner.calls[0].args == ["gh", "variable", "set", "NEXT_PUBLIC_X", "--env", "prod"]


def test_github_ensure_environment() -> None:
    runner = FakeRunner()
    GitHubCLI(runner=runner).ensure_environment("me/app", "prod")
    assert runner.calls[0].args == ["gh", "api", "-X", "PUT", "repos/me/app/environments/prod"]


def test_github_error_on_failure() -> None:
    runner = FakeRunner(returncode=1, stderr="boom")
    with pytest.raises(GitHubError, match="boom"):
        GitHubCLI(runner=runner).set_variable("X", "v")


def test_github_error_default_message() -> None:
    runner = FakeRunner(returncode=1, stderr="")
    with pytest.raises(GitHubError, match="failed"):
        GitHubCLI(runner=runner).set_variable("X", "v")


# --- Terraform -------------------------------------------------------------------


def test_terraform_apply_passes_tf_vars(tmp_path: Path) -> None:
    runner = FakeRunner()
    tf = Terraform(tmp_path, env_base={"PATH": "/bin"}, runner=runner)
    tf.init()
    tf.validate()
    tf.apply({"domain": "example.com", "coolify_token": "secret"})
    apply_call = runner.calls[-1]
    assert apply_call.args == ["terraform", "apply", "-auto-approve", "-input=false"]
    assert apply_call.env["TF_VAR_domain"] == "example.com"
    assert apply_call.env["TF_VAR_coolify_token"] == "secret"
    assert apply_call.env["PATH"] == "/bin"
    assert apply_call.cwd == str(tmp_path)


def test_terraform_default_env_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOME_MARKER", "yes")
    runner = FakeRunner()
    Terraform(tmp_path, runner=runner).init()
    assert runner.calls[0].env["SOME_MARKER"] == "yes"


def test_terraform_raises_on_failure(tmp_path: Path) -> None:
    runner = FakeRunner(returncode=1, stderr="bad config")
    with pytest.raises(TerraformError, match="bad config"):
        Terraform(tmp_path, env_base={}, runner=runner).validate()


def test_terraform_default_error_message(tmp_path: Path) -> None:
    runner = FakeRunner(returncode=1, stderr="")
    with pytest.raises(TerraformError, match="terraform init failed"):
        Terraform(tmp_path, env_base={}, runner=runner).init()


# --- Ansible ---------------------------------------------------------------------


def test_render_inventory_defaults() -> None:
    text = render_inventory({"host": "203.0.113.5"})
    assert "ansible_host=203.0.113.5" in text
    assert "ansible_user=root" in text
    assert "id_ed25519" in text


def test_render_inventory_custom() -> None:
    text = render_inventory(
        {"host": "1.2.3.4", "ansible_user": "deploy", "ansible_ssh_private_key_file": "/k"}
    )
    assert "ansible_user=deploy" in text
    assert "/k" in text


def test_ansible_run_playbook(tmp_path: Path) -> None:
    runner = FakeRunner()
    Ansible(runner=runner).run_playbook(tmp_path / "p.yml", tmp_path / "inv", cwd=tmp_path)
    call = runner.calls[0]
    assert call.args[0] == "ansible-playbook"
    assert str(tmp_path / "inv") in call.args
    assert call.cwd == str(tmp_path)


def test_ansible_run_playbook_no_cwd_and_failure(tmp_path: Path) -> None:
    ok = FakeRunner()
    Ansible(runner=ok).run_playbook(tmp_path / "p.yml", tmp_path / "inv")
    assert ok.calls[0].cwd is None

    bad = FakeRunner(returncode=2, stderr="unreachable")
    with pytest.raises(AnsibleError, match="unreachable"):
        Ansible(runner=bad).run_playbook(tmp_path / "p.yml", tmp_path / "inv")
