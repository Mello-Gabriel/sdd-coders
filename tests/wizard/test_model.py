"""Tests for the wizard data model and sink routing."""

from __future__ import annotations

from sdd_coders.wizard.model import SECRET_FIELDS, WizardConfig, route


def _full_config() -> WizardConfig:
    return WizardConfig(
        project_name="my-app",
        domain="example.com",
        github_repo="me/my-app",
        create_github_repo=True,
        use_cloudflare=True,
        use_coolify=True,
        use_resend=True,
        use_ga=True,
        use_turnstile=True,
        manage_vps=True,
        resend_api_key="re_key",
        turnstile_secret_key="ts_secret",
        turnstile_site_key="ts_site",
        ga_id="G-ABC123",
        cloudflare_api_token="cf_token",
        cloudflare_zone_id="zone1",
        hostinger_api_key="hg_key",
        vps_ip="203.0.113.5",
        coolify_url="https://coolify.example.com",
        coolify_token="cool_token",
        coolify_uuids={"prod_backend": "uuid-b", "prod_frontend": "uuid-f"},
    )


def test_default_ui_theme() -> None:
    assert WizardConfig(project_name="x").ui_theme == "blue"


def test_derived_urls() -> None:
    cfg = WizardConfig(project_name="x", domain="example.com")
    assert cfg.api_url_dev == "https://api-dev.example.com"
    assert cfg.api_url_prod == "https://api.example.com"
    assert cfg.frontend_url_prod == "https://example.com"


def test_derived_urls_blank_without_domain() -> None:
    cfg = WizardConfig(project_name="x")
    assert cfg.api_url_dev == ""
    assert cfg.api_url_prod == ""
    assert cfg.frontend_url_prod == ""


def test_with_generated_secrets_fills_blanks() -> None:
    cfg = WizardConfig(project_name="x").with_generated_secrets()
    assert len(cfg.jwt_secret) >= 32
    assert cfg.postgres_password
    assert cfg.redis_password


def test_with_generated_secrets_preserves_existing() -> None:
    cfg = WizardConfig(
        project_name="x",
        jwt_secret="keep-jwt",
        postgres_password="keep-pg",
        redis_password="keep-redis",
    ).with_generated_secrets()
    assert cfg.jwt_secret == "keep-jwt"
    assert cfg.postgres_password == "keep-pg"
    assert cfg.redis_password == "keep-redis"


def test_route_minimal_config() -> None:
    cfg = WizardConfig(project_name="x", domain="example.com").with_generated_secrets()
    routed = route(cfg)
    assert routed.repo_data == {"project_name": "x"}
    assert routed.gh_secrets == {}
    # API url vars are always present; GA / turnstile only when enabled.
    assert set(routed.gh_variables) == {"NEXT_PUBLIC_API_URL_DEV", "NEXT_PUBLIC_API_URL_PROD"}
    assert routed.ansible_vars == {}
    assert routed.tf_vars["manage_vps"] == "false"


def test_route_full_config() -> None:
    cfg = _full_config().with_generated_secrets()
    routed = route(cfg)

    assert routed.gh_secrets["COOLIFY_URL"] == "https://coolify.example.com"
    assert routed.gh_secrets["COOLIFY_PROD_BACKEND_UUID"] == "uuid-b"
    assert routed.gh_secrets["COOLIFY_PROD_FRONTEND_UUID"] == "uuid-f"

    assert routed.gh_variables["NEXT_PUBLIC_GA_ID"] == "G-ABC123"
    assert routed.gh_variables["NEXT_PUBLIC_TURNSTILE_SITE_KEY"] == "ts_site"

    backend = routed.coolify_backend_env
    assert backend["APP_ENVIRONMENT"] == "production"
    assert backend["APP_EMAIL_PROVIDER"] == "resend"
    assert backend["APP_RESEND_API_KEY"] == "re_key"
    assert backend["APP_TURNSTILE_SECRET_KEY"] == "ts_secret"
    assert backend["APP_JWT_SECRET"] == cfg.jwt_secret
    assert cfg.postgres_password in backend["APP_DATABASE_URL"]

    front = routed.coolify_frontend_env
    assert front["NEXT_PUBLIC_API_URL"] == "https://api.example.com"
    assert front["NEXT_PUBLIC_GA_ID"] == "G-ABC123"
    assert front["NEXT_PUBLIC_TURNSTILE_SITE_KEY"] == "ts_site"

    tf = routed.tf_vars
    assert tf["cloudflare_api_token"] == "cf_token"
    assert tf["cloudflare_zone_id"] == "zone1"
    assert tf["turnstile_secret_key"] == "ts_secret"
    assert tf["coolify_token"] == "cool_token"
    assert tf["hostinger_api_key"] == "hg_key"
    assert tf["vps_ip"] == "203.0.113.5"
    assert tf["manage_vps"] == "true"

    assert routed.ansible_vars == {
        "host": "203.0.113.5",
        "ansible_user": "root",
        "ansible_ssh_private_key_file": "~/.ssh/id_ed25519",
    }


def test_secret_fields_are_routed_only_to_remote_sinks() -> None:
    # The only repo-bound bucket must never carry a secret value.
    cfg = _full_config().with_generated_secrets()
    routed = route(cfg)
    secret_values = {getattr(cfg, name) for name in SECRET_FIELDS if getattr(cfg, name)}
    assert all(value not in routed.repo_data.values() for value in secret_values)
