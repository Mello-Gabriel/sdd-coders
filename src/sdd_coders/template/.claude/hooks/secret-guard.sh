#!/usr/bin/env bash
# PreToolUse secret guard (defense-in-depth for the "no AI reads prod secrets"
# guarantee). The primary guarantee is architectural — production secrets never
# land in this repo or in this process's environment (the sdd-coders wizard pushes
# them straight to GitHub/Coolify and keeps Terraform state/inventory outside the
# repo). This hook is the belt-and-suspenders layer: it blocks the agent from
# reading secret-shaped files or dumping the environment, since deny-rules on the
# Read tool do not cover `cat`/`grep` run through Bash.
#
# Reads the hook payload (JSON) from stdin. Exit 2 blocks the tool and feeds the
# message back to the model; exit 0 allows it.
set -uo pipefail

payload="$(cat)"
tool="$(printf '%s' "$payload" | jq -r '.tool_name // empty' 2>/dev/null || true)"

# Paths/commands that must never be read or printed by the agent.
secret_re='(\.env($|[^a-zA-Z])|\.env\.[a-zA-Z]|\.tfvars|\.tfstate|\.secrets/|secrets[^/]*\.env|ansible/inventory|id_ed25519|id_rsa|\.pem($|[^a-zA-Z]))'

block() {
  echo "secret-guard: bloqueado — esta ação tocaria segredos de produção." >&2
  echo "Segredos não vivem neste repo nem neste processo: o wizard sdd-coders os" >&2
  echo "envia direto para GitHub/Coolify e mantém o state/inventário fora do repo." >&2
  echo "Trabalhe com os NOMES das variáveis de ambiente, nunca com os valores." >&2
  exit 2
}

case "$tool" in
  Bash)
    cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
    # Dumping the environment.
    if printf '%s' "$cmd" | grep -Eq '(^|[^a-zA-Z_])(printenv|env)([[:space:]]*$|[[:space:]]*\|)'; then
      block
    fi
    # Reading secret-shaped files via common readers, or `gh secret`/`terraform output`.
    if printf '%s' "$cmd" | grep -Eq "(cat|less|more|head|tail|grep|rg|awk|sed|cp|nl|xxd|od|strings|source|\.)[[:space:]]+[^|&;]*${secret_re}"; then
      block
    fi
    if printf '%s' "$cmd" | grep -Eq '(gh[[:space:]]+secret[[:space:]]+(list|get)|terraform[[:space:]]+output|keyring[[:space:]]+get)'; then
      block
    fi
    ;;
  Read|Grep|Glob)
    target="$(printf '%s' "$payload" \
      | jq -r '.tool_input.file_path // .tool_input.path // .tool_input.pattern // empty' 2>/dev/null || true)"
    if printf '%s' "$target" | grep -Eq "$secret_re"; then
      block
    fi
    ;;
esac

exit 0
