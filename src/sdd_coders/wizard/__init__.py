"""Project-creation wizard for sdd-coders.

A native (Tkinter) wizard that scaffolds a new project, pushes production secrets
straight to their remote homes (GitHub / Coolify / Cloudflare / Terraform / Ansible)
without ever writing them into the repo, installs the AI secret-guard, and launches
Claude Code into the discovery interview with a scrubbed environment.

The security guarantee — *no AI can read production secrets* — is architectural:
the wizard is a privileged process that keeps secrets in memory and the OS keychain,
while Claude Code runs as an unprivileged child in a repo that, by construction,
contains only throwaway local-dev values.
"""

from __future__ import annotations
