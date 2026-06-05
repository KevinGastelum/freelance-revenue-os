#!/usr/bin/env bash
# Show the current state of a Warren run (single GET, no streaming).
# Usage: wr-run-status.sh <run-id>
# Requires WARREN_API_TOKEN. Pairs with wr-run.sh / wr-events.sh.
set -euo pipefail

run_id="${1:?run id required}"

WARREN_BASE_URL="${WARREN_BASE_URL:-http://localhost:8080}"
source "$(dirname "${BASH_SOURCE[0]}")/wr-env.sh"  # auto-load WARREN_API_TOKEN (see wr-env.sh)
: "${WARREN_API_TOKEN:?WARREN_API_TOKEN is required}"

curl -fsS \
  -H "Authorization: Bearer ${WARREN_API_TOKEN}" \
  "${WARREN_BASE_URL}/runs/${run_id}" | jq . 2>/dev/null || cat
