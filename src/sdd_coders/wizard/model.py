"""The wizard's data model and the routing that sends each value to its home.

``WizardConfig`` holds everything collected from the user. ``route()`` turns it into
``RoutedValues`` — the exact buckets that go to GitHub secrets, GitHub variables,
Coolify env, Terraform variables and Ansible. This separation is what guarantees no
production secret is ever written into the generated repo: only ``repo_data`` (the
project name) reaches Copier; every secret is addressed to a remote sink.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field, replace

from sdd_coders.wizard.themes import DEFAULT_THEME

#: Config fields that hold secrets — persisted only to the OS keychain, never to disk,
#: and redacted from any diagnostic output.
SECRET_FIELDS: frozenset[str] = frozenset(
    {
        "jwt_secret",
        "postgres_password",
        "redis_password",
        "resend_api_key",
        "turnstile_secret_key",
        "cloudflare_api_token",
        "hostinger_api_key",
        "coolify_token",
    }
)


@dataclass
class WizardConfig:
    """Everything the wizard collects for one project."""

    project_name: str
    domain: str = ""
    github_repo: str = ""  # "owner/repo"
    create_github_repo: bool = False
    ui_theme: str = DEFAULT_THEME

    # Provider toggles
    use_cloudflare: bool = False
    use_coolify: bool = False
    use_resend: bool = False
    use_ga: bool = False
    use_turnstile: bool = False
    manage_vps: bool = False

    # Auto-generated app secrets
    jwt_secret: str = ""
    postgres_password: str = ""
    redis_password: str = ""

    # Email
    resend_api_key: str = ""

    # Turnstile
    turnstile_secret_key: str = ""
    turnstile_site_key: str = ""

    # Analytics
    ga_id: str = ""

    # Cloudflare
    cloudflare_api_token: str = ""
    cloudflare_zone_id: str = ""

    # Hostinger / VPS
    hostinger_api_key: str = ""
    vps_ip: str = ""
    ssh_key_path: str = "~/.ssh/id_ed25519"
    ansible_user: str = "root"

    # Coolify
    coolify_url: str = ""
    coolify_token: str = ""
    coolify_uuids: dict[str, str] = field(default_factory=dict)

    # Derived URLs ---------------------------------------------------------------

    @property
    def api_url_dev(self) -> str:
        return f"https://api-dev.{self.domain}" if self.domain else ""

    @property
    def api_url_prod(self) -> str:
        return f"https://api.{self.domain}" if self.domain else ""

    @property
    def frontend_url_prod(self) -> str:
        return f"https://{self.domain}" if self.domain else ""

    def with_generated_secrets(self) -> WizardConfig:
        """Return a copy with any blank auto-gen secret filled with strong randomness.

        JWT uses hex (matches the dev ``.env`` and ``config.py`` expectations); the DB
        and Redis passwords use url-safe tokens.
        """
        return replace(
            self,
            jwt_secret=self.jwt_secret or secrets.token_hex(32),
            postgres_password=self.postgres_password or secrets.token_urlsafe(32),
            redis_password=self.redis_password or secrets.token_urlsafe(32),
        )


@dataclass(frozen=True)
class RoutedValues:
    """The fully-addressed buckets — each goes to exactly one remote sink."""

    repo_data: dict[str, str]
    gh_secrets: dict[str, str]
    gh_variables: dict[str, str]
    coolify_backend_env: dict[str, str]
    coolify_frontend_env: dict[str, str]
    tf_vars: dict[str, str]
    ansible_vars: dict[str, str]


def _gh_secrets(cfg: WizardConfig) -> dict[str, str]:
    secrets_out: dict[str, str] = {}
    if cfg.use_coolify:
        secrets_out["COOLIFY_URL"] = cfg.coolify_url
        secrets_out["COOLIFY_TOKEN"] = cfg.coolify_token
        for key, uuid in cfg.coolify_uuids.items():
            secrets_out[f"COOLIFY_{key.upper()}_UUID"] = uuid
    return secrets_out


def _gh_variables(cfg: WizardConfig) -> dict[str, str]:
    variables = {
        "NEXT_PUBLIC_API_URL_DEV": cfg.api_url_dev,
        "NEXT_PUBLIC_API_URL_PROD": cfg.api_url_prod,
    }
    if cfg.use_ga:
        variables["NEXT_PUBLIC_GA_ID"] = cfg.ga_id
    if cfg.use_turnstile:
        variables["NEXT_PUBLIC_TURNSTILE_SITE_KEY"] = cfg.turnstile_site_key
    return variables


def _coolify_backend_env(cfg: WizardConfig) -> dict[str, str]:
    env = {
        "APP_ENVIRONMENT": "production",
        "APP_JWT_SECRET": cfg.jwt_secret,
        "POSTGRES_PASSWORD": cfg.postgres_password,
        "REDIS_PASSWORD": cfg.redis_password,
        "APP_DATABASE_URL": f"postgresql+asyncpg://app_user:{cfg.postgres_password}@db:5432/app",
        "APP_REDIS_URL": f"redis://:{cfg.redis_password}@redis:6379/0",
        "APP_FRONTEND_URL": cfg.frontend_url_prod,
    }
    if cfg.use_resend:
        env["APP_EMAIL_PROVIDER"] = "resend"
        env["APP_RESEND_API_KEY"] = cfg.resend_api_key
    if cfg.use_turnstile:
        env["APP_TURNSTILE_ENABLED"] = "true"
        env["APP_TURNSTILE_SECRET_KEY"] = cfg.turnstile_secret_key
    return env


def _coolify_frontend_env(cfg: WizardConfig) -> dict[str, str]:
    env = {"NEXT_PUBLIC_API_URL": cfg.api_url_prod}
    if cfg.use_ga:
        env["NEXT_PUBLIC_GA_ID"] = cfg.ga_id
    if cfg.use_turnstile:
        env["NEXT_PUBLIC_TURNSTILE_SITE_KEY"] = cfg.turnstile_site_key
    return env


def _tf_vars(cfg: WizardConfig) -> dict[str, str]:
    tf_vars = {
        "app_name": cfg.project_name,
        "domain": cfg.domain,
        "manage_vps": "true" if cfg.manage_vps else "false",
    }
    if cfg.vps_ip:
        tf_vars["vps_ip"] = cfg.vps_ip
    if cfg.use_cloudflare:
        tf_vars["cloudflare_api_token"] = cfg.cloudflare_api_token
        tf_vars["cloudflare_zone_id"] = cfg.cloudflare_zone_id
    if cfg.use_turnstile:
        tf_vars["turnstile_secret_key"] = cfg.turnstile_secret_key
    if cfg.use_coolify:
        tf_vars["coolify_url"] = cfg.coolify_url
        tf_vars["coolify_token"] = cfg.coolify_token
    if cfg.manage_vps:
        tf_vars["hostinger_api_key"] = cfg.hostinger_api_key
    return tf_vars


def _ansible_vars(cfg: WizardConfig) -> dict[str, str]:
    if not cfg.vps_ip:
        return {}
    return {
        "host": cfg.vps_ip,
        "ansible_user": cfg.ansible_user,
        "ansible_ssh_private_key_file": cfg.ssh_key_path,
    }


def route(cfg: WizardConfig) -> RoutedValues:
    """Map a config onto its sinks. Pure: no I/O, deterministic for a given config."""
    return RoutedValues(
        repo_data={"project_name": cfg.project_name},
        gh_secrets=_gh_secrets(cfg),
        gh_variables=_gh_variables(cfg),
        coolify_backend_env=_coolify_backend_env(cfg),
        coolify_frontend_env=_coolify_frontend_env(cfg),
        tf_vars=_tf_vars(cfg),
        ansible_vars=_ansible_vars(cfg),
    )
