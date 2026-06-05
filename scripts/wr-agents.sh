#!/usr/bin/env bash
# List Warren agents / runtimes. Requires WARREN_API_TOKEN.
set -euo pipefail

WARREN_BASE_URL="${WARREN_BASE_URL:-http://localhost:8080}"
source "$(dirname "${BASH_SOURCE[0]}")/wr-env.sh"  # auto-load WARREN_API_TOKEN (see wr-env.sh)
: "${WARREN_API_TOKEN:?WARREN_API_TOKEN is required}"

curl -fsS \
  -H "Authorization: Bearer ${WARREN_API_TOKEN}" \
  "${WARREN_BASE_URL}/agents" | jq . 2>/dev/null || cat
