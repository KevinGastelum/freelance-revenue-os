#!/usr/bin/env bash
# Steer an in-flight Warren run.  Usage: wr-steer.sh <run-id> "<message>" [priority]
# Requires WARREN_API_TOKEN and jq. Keep messages short, imperative, scoped.
set -euo pipefail

run_id="${1:?run id required}"
message="${2:?steering message required}"
priority="${3:-high}"

WARREN_BASE_URL="${WARREN_BASE_URL:-http://localhost:8080}"
source "$(dirname "${BASH_SOURCE[0]}")/wr-env.sh"  # auto-load WARREN_API_TOKEN (see wr-env.sh)
: "${WARREN_API_TOKEN:?WARREN_API_TOKEN is required}"

payload="$(jq -n \
  --arg body "$message" \
  --arg priority "$priority" \
  '{body:$body, priority:$priority}')"

curl -fsS \
  -X POST \
  -H "Authorization: Bearer ${WARREN_API_TOKEN}" \
  -H "Content-Type: application/json" \
  "${WARREN_BASE_URL}/runs/${run_id}/steer" \
  -d "$payload" | jq . 2>/dev/null || cat
