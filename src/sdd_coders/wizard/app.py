"""The native (Tkinter) wizard window.

A thin shell: it collects values into a ``WizardConfig`` and drives the fully-tested
``Pipeline``. No business logic lives here, which is why it is excluded from the
coverage gate (driving a Tk event loop in unit tests is impractical).
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from sdd_coders.wizard.launch import launch_claude
from sdd_coders.wizard.model import WizardConfig
from sdd_coders.wizard.pipeline import Pipeline
from sdd_coders.wizard.providers.ansible import Ansible
from sdd_coders.wizard.providers.cloudflare import CloudflareClient
from sdd_coders.wizard.providers.coolify import CoolifyClient
from sdd_coders.wizard.providers.git import Git
from sdd_coders.wizard.providers.github import GitHubCLI
from sdd_coders.wizard.providers.resend import ResendClient
from sdd_coders.wizard.providers.terraform import Terraform
from sdd_coders.wizard.secrets_store import load_secrets, save_secrets
from sdd_coders.wizard.themes import DEFAULT_THEME, THEMES
from sdd_coders.wizard.validators import validate_domain
from sdd_coders.wizard.workspace import terraform_workdir


class WizardApp:
    """Builds the form, validates connections, and runs the pipeline."""

    def __init__(self, path: Path, project_name: str, *, existing: bool = False) -> None:
        self.path = path
        self.project_name = project_name
        self.existing = existing
        self.root = tk.Tk()
        self.root.title(f"sdd-coders · {project_name}")
        self.root.geometry("560x720")

        self._vars: dict[str, tk.Variable] = {}
        self.status = tk.StringVar(value="Preencha os campos e clique em Criar.")
        self._theme = tk.StringVar(value=DEFAULT_THEME)
        self._build()

        if existing:
            self._prefill_from_keychain()

    # UI construction ------------------------------------------------------------

    _HINT = "#888"

    def _row(
        self, parent: tk.Widget, label: str, key: str, *, secret: bool = False, hint: str = ""
    ) -> None:
        group = ttk.Frame(parent)
        group.pack(fill="x", pady=(6, 0))
        line = ttk.Frame(group)
        line.pack(fill="x")
        ttk.Label(line, text=label, width=22).pack(side="left")
        var = tk.StringVar()
        self._vars[key] = var
        ttk.Entry(line, textvariable=var, show="•" if secret else "").pack(
            side="left", fill="x", expand=True
        )
        if hint:
            ttk.Label(
                group, text=hint, foreground=self._HINT, wraplength=500, justify="left"
            ).pack(anchor="w", padx=(2, 0))

    def _check(self, parent: tk.Widget, label: str, key: str, *, hint: str = "") -> None:
        var = tk.BooleanVar(value=False)
        self._vars[key] = var
        ttk.Checkbutton(parent, text=label, variable=var).pack(anchor="w", pady=(5, 0))
        if hint:
            ttk.Label(
                parent, text=hint, foreground=self._HINT, wraplength=500, justify="left"
            ).pack(anchor="w", padx=(22, 0))

    def _theme_picker(self, parent: tk.Widget) -> None:
        for theme in THEMES:
            line = ttk.Frame(parent)
            line.pack(anchor="w", pady=(3, 0))
            tk.Label(line, background=theme.swatch, width=3, relief="solid", borderwidth=1).pack(
                side="left", padx=(0, 8)
            )
            ttk.Radiobutton(
                line, text=theme.label, value=theme.key, variable=self._theme
            ).pack(side="left")

    def _build(self) -> None:
        # Fixed action bar at the bottom, always reachable regardless of scroll.
        bottom = ttk.Frame(self.root, padding=(16, 8))
        bottom.pack(side="bottom", fill="x")
        ttk.Label(
            bottom, textvariable=self.status, foreground="#0a7", wraplength=520, justify="left"
        ).pack(anchor="w", pady=(0, 6))
        actions = ttk.Frame(bottom)
        actions.pack(fill="x")
        ttk.Button(actions, text="Testar conexões", command=self._test).pack(side="left")
        ttk.Button(actions, text="Criar →", command=self._create).pack(side="right")

        # Scrollable body (the form is long once every field carries a description).
        canvas = tk.Canvas(self.root, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        body = ttk.Frame(canvas, padding=16)
        body.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw", width=540)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<Button-4>", lambda _e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda _e: canvas.yview_scroll(1, "units"))

        ttk.Label(body, text="Projeto", font=("", 12, "bold")).pack(anchor="w")
        self._row(
            body, "Domínio (prod)", "domain",
            hint="Domínio raiz de produção, ex.: meuapp.com (sem http://). "
                 "Vira as URLs de API, e-mail e DNS. Deixe em branco se ainda não tiver.",
        )
        self._row(
            body, "GitHub (owner/repo)", "github_repo",
            hint="Repositório no formato usuario/repo. Onde os secrets de CI e os "
                 "Environments dev/prod são criados.",
        )
        self._check(
            body, "Criar repositório no GitHub e dar push", "create_github_repo",
            hint="Cria o repo no GitHub a partir desta pasta e faz o primeiro push (requer gh).",
        )

        ttk.Separator(body).pack(fill="x", pady=8)
        ttk.Label(body, text="Tema visual", font=("", 12, "bold")).pack(anchor="w")
        ttk.Label(
            body, text="Paleta primária do shadcn/Tailwind (mesmas telas, cor diferente).",
            foreground=self._HINT, wraplength=500, justify="left",
        ).pack(anchor="w", pady=(0, 2))
        self._theme_picker(body)

        ttk.Separator(body).pack(fill="x", pady=8)
        ttk.Label(body, text="Provedores", font=("", 12, "bold")).pack(anchor="w")
        for label, key, hint in (
            ("Cloudflare (DNS + WAF)", "use_cloudflare",
             "DNS e rate-limit na borda, via Terraform. Requer terraform instalado."),
            ("Coolify (deploy)", "use_coolify",
             "Painel de deploy self-hosted; recebe as variáveis de ambiente de produção."),
            ("Resend (e-mail)", "use_resend",
             "E-mail transacional: verificação de conta e reset de senha."),
            ("Google Analytics", "use_ga",
             "GA4 — só carrega depois do consentimento de cookies (LGPD)."),
            ("Turnstile (captcha)", "use_turnstile",
             "Captcha da Cloudflare nas rotas de registro e reset de senha."),
            ("Provisionar VPS (Hostinger + Ansible)", "manage_vps",
             "Cria e endurece o VPS via Ansible. Requer ansible instalado."),
        ):
            self._check(body, label, key, hint=hint)

        ttk.Separator(body).pack(fill="x", pady=8)
        ttk.Label(
            body, text="Segredos (vão direto pro destino remoto, nunca pro repo)",
            font=("", 12, "bold"),
        ).pack(anchor="w")
        self._row(
            body, "Cloudflare API token", "cloudflare_api_token", secret=True,
            hint="Token da API Cloudflare (Zone DNS + Firewall). Cria DNS/WAF via Terraform.",
        )
        self._row(
            body, "Coolify URL", "coolify_url",
            hint="URL da sua instância Coolify, ex.: https://coolify.meuapp.com",
        )
        self._row(
            body, "Coolify token", "coolify_token", secret=True,
            hint="Token de API do Coolify (Settings → API Tokens). Dispara os deploys.",
        )
        self._row(
            body, "Resend API key", "resend_api_key", secret=True,
            hint="API key do Resend (começa com re_). Vai pro backend em produção.",
        )
        self._row(
            body, "Turnstile secret key", "turnstile_secret_key", secret=True,
            hint="Chave secreta (lado servidor) do widget Turnstile.",
        )
        self._row(
            body, "Turnstile site key", "turnstile_site_key",
            hint="Chave pública (site key) do Turnstile, embutida no frontend.",
        )
        self._row(
            body, "GA measurement id", "ga_id",
            hint="ID de medição do GA4 no formato G-XXXXXXXXXX.",
        )
        self._row(
            body, "Hostinger API key", "hostinger_api_key", secret=True,
            hint="Token da API Hostinger (vps:read, vps:write) — só se provisionar o VPS.",
        )
        self._row(
            body, "VPS IP", "vps_ip",
            hint="IP do VPS de produção. Usado no DNS e no inventário do Ansible.",
        )

        ttk.Label(
            body,
            text="JWT, senha do Postgres e do Redis são geradas automaticamente — "
                 "você não precisa preencher.",
            foreground="#666", wraplength=500, justify="left",
        ).pack(anchor="w", pady=8)

    # Helpers --------------------------------------------------------------------

    def _get(self, key: str) -> str:
        var = self._vars.get(key)
        return str(var.get()) if var is not None else ""  # type: ignore[no-untyped-call]

    def _flag(self, key: str) -> bool:
        var = self._vars.get(key)
        return bool(var.get()) if var is not None else False  # type: ignore[no-untyped-call]

    def _prefill_from_keychain(self) -> None:
        for name, value in load_secrets(self.project_name).items():
            if name in self._vars:
                self._vars[name].set(value)

    def _collect(self) -> WizardConfig:
        cfg = WizardConfig(
            project_name=self.project_name,
            domain=validate_domain(self._get("domain")) if self._get("domain") else "",
            github_repo=self._get("github_repo"),
            create_github_repo=self._flag("create_github_repo"),
            ui_theme=self._theme.get(),
            use_cloudflare=self._flag("use_cloudflare"),
            use_coolify=self._flag("use_coolify"),
            use_resend=self._flag("use_resend"),
            use_ga=self._flag("use_ga"),
            use_turnstile=self._flag("use_turnstile"),
            manage_vps=self._flag("manage_vps"),
            resend_api_key=self._get("resend_api_key"),
            turnstile_secret_key=self._get("turnstile_secret_key"),
            turnstile_site_key=self._get("turnstile_site_key"),
            ga_id=self._get("ga_id"),
            cloudflare_api_token=self._get("cloudflare_api_token"),
            hostinger_api_key=self._get("hostinger_api_key"),
            vps_ip=self._get("vps_ip"),
            coolify_url=self._get("coolify_url"),
            coolify_token=self._get("coolify_token"),
        ).with_generated_secrets()
        if cfg.use_cloudflare and cfg.domain and cfg.cloudflare_api_token:
            cfg.cloudflare_zone_id = CloudflareClient(cfg.cloudflare_api_token).zone_id(
                cfg.domain
            )
        if cfg.use_coolify and cfg.coolify_url and cfg.coolify_token:
            cfg.coolify_uuids = CoolifyClient(cfg.coolify_url, cfg.coolify_token).resolve_uuids(
                {
                    "dev_backend": f"{cfg.project_name}-backend-dev",
                    "dev_frontend": f"{cfg.project_name}-frontend-dev",
                    "prod_backend": f"{cfg.project_name}-backend-prod",
                    "prod_frontend": f"{cfg.project_name}-frontend-prod",
                }
            )
        return cfg

    def _test(self) -> None:
        results: list[str] = []
        if self._flag("use_cloudflare") and self._get("cloudflare_api_token"):
            ok = CloudflareClient(self._get("cloudflare_api_token")).verify()
            results.append(f"Cloudflare {'✓' if ok else '✗'}")
        if self._flag("use_coolify") and self._get("coolify_url") and self._get("coolify_token"):
            ok = CoolifyClient(self._get("coolify_url"), self._get("coolify_token")).verify()
            results.append(f"Coolify {'✓' if ok else '✗'}")
        if self._flag("use_resend") and self._get("resend_api_key"):
            ok = ResendClient(self._get("resend_api_key")).verify()
            results.append(f"Resend {'✓' if ok else '✗'}")
        ok_gh = GitHubCLI().auth_ok()
        results.append(f"GitHub {'✓' if ok_gh else '✗'}")
        self.status.set("  ".join(results) or "Nada para testar.")

    def _progress(self, message: str) -> None:
        self.status.set(message)
        self.root.update_idletasks()

    def _create(self) -> None:
        try:
            cfg = self._collect()
        except ValueError as exc:
            messagebox.showerror("Dados inválidos", str(exc))
            return
        save_secrets(cfg.project_name, cfg)

        coolify = (
            CoolifyClient(cfg.coolify_url, cfg.coolify_token) if cfg.use_coolify else None
        )
        terraform = (
            Terraform(terraform_workdir(cfg.project_name)) if cfg.use_cloudflare else None
        )
        ansible = Ansible() if cfg.manage_vps else None
        pipeline = Pipeline(
            cfg=cfg,
            repo=self.path,
            github=GitHubCLI(cwd=self.path),
            git=Git(cwd=self.path),
            coolify=coolify,
            terraform=terraform,
            ansible=ansible,
            on_progress=self._progress,
        )
        try:
            pipeline.run_all()
        except Exception as exc:  # surface any provider error to the user
            messagebox.showerror("Falha no provisionamento", str(exc))
            return

        self.root.destroy()
        launch_claude(self.path)

    def run(self) -> None:
        self.root.mainloop()


def run_wizard(path: Path, project_name: str, *, existing: bool = False) -> None:
    """Entry point used by the CLI: open the wizard window."""
    WizardApp(path, project_name, existing=existing).run()
