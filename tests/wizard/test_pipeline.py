"""Tests for the orchestration pipeline, including the no-secret-in-repo invariant."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from sdd_coders.scaffold import write_dev_env
from sdd_coders.wizard import workspace
from sdd_coders.wizard.model import WizardConfig
from sdd_coders.wizard.pipeline import (
    Pipeline,
    find_secret_leaks,
    secret_values,
)
from sdd_coders.wizard.providers.ansible import Ansible
from sdd_coders.wizard.providers.coolify import CoolifyClient
from sdd_coders.wizard.providers.git import Git
from sdd_coders.wizard.providers.github import GitHubCLI
from sdd_coders.wizard.providers.terraform import Terraform
from tests.wizard.conftest import FakeRunner, mock_client


def _fake_scaffold(repo: Path, name: str, ui_theme: str = "blue") -> None:
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "CLAUDE.md").write_text(f"# {name} ({ui_theme})\n", encoding="utf-8")
    (repo / "infra" / "terraform").mkdir(parents=True, exist_ok=True)
    (repo / "infra" / "terraform" / "main.tf").write_text("# terraform\n", encoding="utf-8")
    playbooks = repo / "infra" / "ansible" / "playbooks"
    playbooks.mkdir(parents=True, exist_ok=True)
    (playbooks / "harden.yml").write_text("---\n", encoding="utf-8")


@pytest.fixture
def isolated_state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    return tmp_path


def _full_config() -> WizardConfig:
    return WizardConfig(
        project_name="my-app",
        domain="example.com",
        github_repo="me/my-app",
        create_github_repo=True,
        use_cloudflare=True,
        use_coolify=True,
        use_resend=True,
        use_turnstile=True,
        manage_vps=True,
        resend_api_key="re_secret",
        turnstile_secret_key="ts_secret",
        cloudflare_api_token="cf_secret",
        cloudflare_zone_id="zone1",
        hostinger_api_key="hg_secret",
        vps_ip="203.0.113.5",
        coolify_url="https://coolify.example.com",
        coolify_token="cool_secret",
        coolify_uuids={"prod_backend": "ub", "prod_frontend": "uf", "other": "uo"},
    ).with_generated_secrets()


def _build_pipeline(cfg: WizardConfig, repo: Path, coolify_calls: list[str]) -> Pipeline:
    def coolify_handler(request: httpx.Request) -> httpx.Response:
        coolify_calls.append(str(request.url))
        return httpx.Response(200, json={})

    return Pipeline(
        cfg=cfg,
        repo=repo,
        github=GitHubCLI(cwd=repo, runner=FakeRunner()),
        git=Git(cwd=repo, runner=FakeRunner()),
        coolify=CoolifyClient(
            cfg.coolify_url, cfg.coolify_token, client=mock_client(coolify_handler)
        ),
        terraform=Terraform(
            workspace.terraform_workdir(cfg.project_name), env_base={}, runner=FakeRunner()
        ),
        ansible=Ansible(runner=FakeRunner()),
        scaffold=_fake_scaffold,
        write_env=write_dev_env,
    )


def test_run_all_provisions_without_leaking_secrets(isolated_state: Path) -> None:
    repo = isolated_state / "my-app"
    cfg = _full_config()
    coolify_calls: list[str] = []
    progress: list[str] = []
    pipeline = _build_pipeline(cfg, repo, coolify_calls)
    pipeline.on_progress = progress.append

    pipeline.run_all()

    # (a) Security invariant: no production secret made it into the repo.
    assert find_secret_leaks(repo, secret_values(cfg)) == []
    # (b) A local-dev .env was generated.
    assert (repo / ".env").read_text(encoding="utf-8").startswith("# Local development")
    # Coolify env was pushed to both apps; progress was reported.
    assert len(coolify_calls) == 2
    assert "Done" in progress
    # Terraform state workdir lives OUTSIDE the repo.
    assert workspace.terraform_workdir("my-app").is_dir()
    assert repo not in workspace.terraform_workdir("my-app").parents
    # The Ansible inventory (with the VPS IP) is outside the repo too.
    inv = workspace.inventory_path("my-app")
    assert "203.0.113.5" in inv.read_text(encoding="utf-8")
    assert repo not in inv.parents


def test_push_github_sets_secrets_and_envs(isolated_state: Path) -> None:
    repo = isolated_state / "my-app"
    cfg = _full_config()
    gh_runner = FakeRunner()
    pipeline = Pipeline(
        cfg=cfg,
        repo=repo,
        github=GitHubCLI(cwd=repo, runner=gh_runner),
        scaffold=_fake_scaffold,
    )
    pipeline.push_github()
    commands = [c.args for c in gh_runner.calls]
    assert ["gh", "repo", "create", "my-app", "--private", "--source=.", "--push"] in commands
    # COOLIFY_TOKEN goes via stdin, never argv.
    secret_call = next(c for c in gh_runner.calls if c.args[:3] == ["gh", "secret", "set"])
    assert "cool_secret" not in secret_call.args
    # Both environments are created.
    assert ["gh", "api", "-X", "PUT", "repos/me/my-app/environments/prod"] in commands


def test_push_github_skips_repo_and_environments(isolated_state: Path) -> None:
    repo = isolated_state / "minimal"
    cfg = WizardConfig(
        project_name="minimal",
        domain="example.com",
        create_github_repo=False,  # skip repo creation
        github_repo="",  # skip environment creation
    ).with_generated_secrets()
    gh_runner = FakeRunner()
    Pipeline(
        cfg=cfg, repo=repo, github=GitHubCLI(runner=gh_runner), scaffold=_fake_scaffold
    ).push_github()
    commands = [c.args[:2] for c in gh_runner.calls]
    assert ["repo", "create"] not in commands
    assert ["api", "-X"] not in [c.args[:2] for c in gh_runner.calls]
    # Only variable sets happen (no coolify secrets, no envs).
    assert all(c.args[1] == "variable" for c in gh_runner.calls)


def test_routed_property_exposes_buckets(isolated_state: Path) -> None:
    cfg = WizardConfig(project_name="x").with_generated_secrets()
    pipeline = Pipeline(cfg=cfg, repo=isolated_state / "x", github=GitHubCLI(runner=FakeRunner()))
    assert pipeline.routed.repo_data == {"project_name": "x"}


def test_pipeline_defaults_git_when_not_injected(isolated_state: Path) -> None:
    cfg = WizardConfig(project_name="x").with_generated_secrets()
    pipeline = Pipeline(cfg=cfg, repo=isolated_state / "x", github=GitHubCLI(runner=FakeRunner()))
    assert isinstance(pipeline._git, Git)


def test_scaffold_repo_passes_chosen_theme(isolated_state: Path) -> None:
    repo = isolated_state / "themed"
    cfg = WizardConfig(project_name="themed", ui_theme="violet").with_generated_secrets()
    captured: dict[str, str] = {}

    def capturing_scaffold(dest: Path, name: str, ui_theme: str) -> None:
        captured["theme"] = ui_theme
        _fake_scaffold(dest, name, ui_theme)

    Pipeline(
        cfg=cfg,
        repo=repo,
        github=GitHubCLI(runner=FakeRunner()),
        git=Git(cwd=repo, runner=FakeRunner()),
        scaffold=capturing_scaffold,
    ).scaffold_repo()
    assert captured["theme"] == "violet"


def test_scaffold_repo_inits_and_commits(isolated_state: Path) -> None:
    repo = isolated_state / "g"
    cfg = WizardConfig(project_name="g").with_generated_secrets()
    git_runner = FakeRunner()
    Pipeline(
        cfg=cfg,
        repo=repo,
        github=GitHubCLI(runner=FakeRunner()),
        git=Git(cwd=repo, runner=git_runner),
        scaffold=_fake_scaffold,
    ).scaffold_repo()
    verbs = [c.args[1] for c in git_runner.calls]
    assert verbs == ["init", "add", "commit"]


def test_optional_steps_skip_when_disabled(isolated_state: Path) -> None:
    repo = isolated_state / "lean"
    cfg = WizardConfig(project_name="lean", domain="example.com").with_generated_secrets()
    pipeline = Pipeline(
        cfg=cfg,
        repo=repo,
        github=GitHubCLI(runner=FakeRunner()),
        coolify=None,
        terraform=None,
        ansible=None,
        scaffold=_fake_scaffold,
    )
    # None of these should raise when their providers are absent.
    pipeline.push_coolify()
    pipeline.provision_terraform()
    pipeline.provision_ansible()


def test_provision_terraform_replaces_existing_workdir(isolated_state: Path) -> None:
    repo = isolated_state / "app"
    cfg = WizardConfig(project_name="app", use_cloudflare=True).with_generated_secrets()
    _fake_scaffold(repo, "app")
    # Pre-create the workdir so the rmtree branch runs.
    stale = workspace.terraform_workdir("app")
    stale.mkdir(parents=True)
    (stale / "stale.txt").write_text("old", encoding="utf-8")

    Pipeline(
        cfg=cfg,
        repo=repo,
        github=GitHubCLI(runner=FakeRunner()),
        terraform=Terraform(stale, env_base={}, runner=FakeRunner()),
        scaffold=_fake_scaffold,
    ).provision_terraform()

    assert (stale / "main.tf").is_file()
    assert not (stale / "stale.txt").exists()


def test_provision_ansible_skips_without_vps(isolated_state: Path) -> None:
    repo = isolated_state / "novps"
    cfg = WizardConfig(project_name="novps", manage_vps=True).with_generated_secrets()
    _fake_scaffold(repo, "novps")
    pipeline = Pipeline(
        cfg=cfg,
        repo=repo,
        github=GitHubCLI(runner=FakeRunner()),
        ansible=Ansible(runner=FakeRunner()),
        scaffold=_fake_scaffold,
    )
    pipeline.provision_ansible()  # no vps_ip → ansible_vars empty → skipped
    assert not workspace.inventory_path("novps").exists()


def test_find_secret_leaks_detects_and_skips(tmp_path: Path) -> None:
    (tmp_path / "ok.txt").write_text("nothing here", encoding="utf-8")
    (tmp_path / "leak.txt").write_text("token=SUPERSECRET", encoding="utf-8")
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "obj").write_text("SUPERSECRET", encoding="utf-8")  # ignored
    (tmp_path / "binary.bin").write_bytes(b"\xff\xfe\x00SUPERSECRET")  # undecodable → skipped

    leaks = find_secret_leaks(tmp_path, ["SUPERSECRET"])
    assert leaks == [tmp_path / "leak.txt"]


def test_find_secret_leaks_empty_when_no_values(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_text("data", encoding="utf-8")
    assert find_secret_leaks(tmp_path, []) == []
    assert find_secret_leaks(tmp_path, [""]) == []


def test_secret_values_lists_only_set_secrets() -> None:
    cfg = WizardConfig(project_name="x", coolify_token="c", jwt_secret="j")
    values = secret_values(cfg)
    assert "c" in values
    assert "j" in values
    assert "" not in values
