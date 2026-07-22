"""Headless orchestration that the GUI drives step by step.

Every step is injectable, so the whole flow runs under test with fake providers and
a real temp repo — proving the security invariant (no production secret ever lands
in the generated repo) without touching the network or the shell.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from sdd_coders.scaffold import scaffold_project, write_dev_env
from sdd_coders.wizard import workspace
from sdd_coders.wizard.model import SECRET_FIELDS, RoutedValues, WizardConfig, route
from sdd_coders.wizard.providers.ansible import Ansible, render_inventory
from sdd_coders.wizard.providers.coolify import CoolifyClient
from sdd_coders.wizard.providers.git import Git
from sdd_coders.wizard.providers.github import GitHubCLI
from sdd_coders.wizard.providers.terraform import Terraform


def _noop(_message: str) -> None:
    """Default progress sink."""


@dataclass
class Pipeline:
    """Drives scaffold → remote secret push → IaC provisioning for one project."""

    cfg: WizardConfig
    repo: Path
    github: GitHubCLI
    git: Git | None = None
    coolify: CoolifyClient | None = None
    terraform: Terraform | None = None
    ansible: Ansible | None = None
    scaffold: Callable[[Path, str, str], None] = scaffold_project
    write_env: Callable[[Path], None] = write_dev_env
    on_progress: Callable[[str], None] = _noop
    _routed: RoutedValues = field(init=False)
    _git: Git = field(init=False)

    def __post_init__(self) -> None:
        self._routed = route(self.cfg)
        self._git = self.git if self.git is not None else Git(cwd=self.repo)

    @property
    def routed(self) -> RoutedValues:
        return self._routed

    # Steps ----------------------------------------------------------------------

    def scaffold_repo(self) -> None:
        self.on_progress("Scaffolding project")
        self.scaffold(self.repo, self.cfg.project_name, self.cfg.ui_theme)
        self.write_env(self.repo)
        # `gh repo create --source=. --push` needs a committed git repo; the dev
        # .env stays out of the commit because the template's .gitignore excludes it.
        self._git.init_commit("Initial commit from sdd-coders")

    def push_github(self) -> None:
        if self.cfg.create_github_repo:
            self.on_progress("Creating GitHub repository")
            self.github.create_repo(self.cfg.project_name)
        self.on_progress("Pushing GitHub secrets and variables")
        for name, value in self._routed.gh_secrets.items():
            self.github.set_secret(name, value, environment="prod")
        for name, value in self._routed.gh_variables.items():
            self.github.set_variable(name, value)
        if self.cfg.github_repo:
            for env_name in ("dev", "prod"):
                self.github.ensure_environment(self.cfg.github_repo, env_name)

    def push_coolify(self) -> None:
        if self.coolify is None:
            return
        self.on_progress("Pushing Coolify environment variables")
        for key, uuid in self.cfg.coolify_uuids.items():
            if "backend" in key:
                self.coolify.set_env(uuid, self._routed.coolify_backend_env)
            elif "frontend" in key:
                self.coolify.set_env(uuid, self._routed.coolify_frontend_env)

    def provision_terraform(self) -> None:
        if self.terraform is None:
            return
        self.on_progress("Provisioning infrastructure (Terraform)")
        src = self.repo / "infra" / "terraform"
        workdir = workspace.terraform_workdir(self.cfg.project_name)
        workdir.parent.mkdir(parents=True, exist_ok=True)
        if workdir.exists():
            shutil.rmtree(workdir)
        shutil.copytree(src, workdir)
        self.terraform.init()
        self.terraform.validate()
        self.terraform.apply(self._routed.tf_vars)

    def provision_ansible(self) -> None:
        if self.ansible is None or not self._routed.ansible_vars:
            return
        self.on_progress("Hardening the VPS (Ansible)")
        inventory = workspace.inventory_path(self.cfg.project_name)
        inventory.parent.mkdir(parents=True, exist_ok=True)
        inventory.write_text(render_inventory(self._routed.ansible_vars), encoding="utf-8")
        playbook = self.repo / "infra" / "ansible" / "playbooks" / "harden.yml"
        self.ansible.run_playbook(playbook, inventory, cwd=self.repo / "infra" / "ansible")

    def run_all(self, *, scaffold: bool = True) -> None:
        """Run every step. Pass ``scaffold=False`` for a project that already exists.

        Re-rendering the template over a repo someone has been working in is not
        just redundant, it is destructive: Copier refuses to overwrite without an
        interactive session, and ``init_commit`` would sweep the user's
        work-in-progress into a commit. ``configure`` therefore skips straight to
        pushing secrets and provisioning.
        """
        if scaffold:
            self.scaffold_repo()
        self.push_github()
        self.push_coolify()
        self.provision_terraform()
        self.provision_ansible()
        self.on_progress("Done")


def secret_values(cfg: WizardConfig) -> list[str]:
    """Every secret string in a config (for leak auditing)."""
    return [getattr(cfg, name) for name in sorted(SECRET_FIELDS) if getattr(cfg, name)]


def find_secret_leaks(repo: Path, values: list[str]) -> list[Path]:
    """Return repo files that contain any of ``values`` — must be empty after a run."""
    needles = [v for v in values if v]
    leaks: list[Path] = []
    if not needles:
        return leaks
    for candidate in repo.rglob("*"):
        if not candidate.is_file() or ".git" in candidate.parts:
            continue
        try:
            text = candidate.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(needle in text for needle in needles):
            leaks.append(candidate)
    return leaks
