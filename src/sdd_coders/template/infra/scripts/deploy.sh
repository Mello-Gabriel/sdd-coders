#!/usr/bin/env bash
# Trigger a Coolify deploy for a given application UUID.
# Usage: ./deploy.sh <app-uuid> [tag]
#
# Required env vars:
#   COOLIFY_URL    — Coolify instance URL (e.g. https://coolify.example.com)
#   COOLIFY_TOKEN  — Coolify API token
#
# Example:
#   COOLIFY_URL=https://coolify.example.com \
#   COOLIFY_TOKEN=my-token \
#   ./deploy.sh abc-123-def prod-v1.2.3

set -euo pipefail

APP_UUID="${1:?Usage: $0 <app-uuid> [tag]}"
TAG="${2:-}"

if [[ -z "${COOLIFY_URL:-}" || -z "${COOLIFY_TOKEN:-}" ]]; then
  echo "ERROR: COOLIFY_URL and COOLIFY_TOKEN must be set." >&2
  exit 1
fi

PAYLOAD='{"uuid":"'"${APP_UUID}"'","force":false}'

echo "→ Triggering deploy for ${APP_UUID}${TAG:+ (tag: ${TAG})}…"

RESPONSE=$(curl -sf -X POST "${COOLIFY_URL}/api/v1/deploy" \
  -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}")

echo "✓ Deploy triggered: ${RESPONSE}"
