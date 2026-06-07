#!/usr/bin/env bash
# PreToolUse gate (constitution §10): block `git commit` unless fast quality
# checks pass. Reads the hook payload (JSON) from stdin and only acts on commits.
# Runs lint + type checks (fast); full tests are enforced by CI.
set -uo pipefail

payload="$(cat)"
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"

case "$cmd" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
fail=0

if [ -f "$root/backend/pyproject.toml" ]; then
  ( cd "$root/backend" \
      && uv run ruff check . \
      && uv run ruff format --check . \
      && uv run mypy ) || fail=1
fi

if [ -f "$root/frontend/package.json" ]; then
  ( cd "$root/frontend" \
      && npm run --silent lint \
      && npm run --silent typecheck ) || fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "Commit bloqueado: lint/types falharam. A constituição exige verde antes de commitar." >&2
  exit 2
fi

exit 0
