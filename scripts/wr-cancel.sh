#!/usr/bin/env bash
# Cancel a Warren run.  Usage: wr-cancel.sh <run-id>
# Requires WARREN_API_TOKEN. Use when a run is unsafe, drifting, or wrong.
set -euo pipefail

run_id="${1:?run id required}"

WARREN_BASE_URL="${WARREN_BASE_URL:-http://localhost:8080}"
source "$(dirname "${BASH_SOURCE[0]}")/wr-env.sh"  # auto-load WARREN_API_TOKEN (see wr-env.sh)
: "${WARREN_API_TOKEN:?WARREN_API_TOKEN is required}"

curl -fsS \
  -X POST \
  -H "Authorization: Bearer ${WARREN_API_TOKEN}" \
  "${WARREN_BASE_URL}/runs/${run_id}/cancel" | jq . 2>/dev/null || cat
