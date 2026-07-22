#!/usr/bin/env bash
# PreToolUse gate for an adopted repository: block `git commit` unless this
# project's own quality gate passes. Reads the hook payload (JSON) from stdin
# and only acts on commits.
#
# The gate command is NOT guessed from the stack — it lives in `.claude/gate.sh`,
# written by /sdd-constitution from the command you declared in
# `specs/constitution.md`. Until that file exists this hook warns instead of
# blocking, so adopting a repo never wedges your commits on day one.
set -uo pipefail

payload="$(cat)"
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"

case "$cmd" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
gate="$root/.claude/gate.sh"

if [ ! -f "$gate" ]; then
  echo "pre-commit-gate: nenhum gate configurado (.claude/gate.sh não existe)." >&2
  echo "Rode /sdd-constitution para declarar o comando de verificação do projeto." >&2
  exit 0
fi

if ! bash "$gate"; then
  echo "Commit bloqueado: o quality gate do projeto falhou (.claude/gate.sh)." >&2
  echo "A constituição exige verde antes de commitar." >&2
  exit 2
fi

exit 0
