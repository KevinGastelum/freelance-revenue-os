#!/usr/bin/env bash
# List Warren agents / runtimes. Requires WARREN_API_TOKEN.
set -euo pipefail

WARREN_BASE_URL="${WARREN_BASE_URL:-http://localhost:8080}"
: "${WARREN_API_TOKEN:?WARREN_API_TOKEN is required}"

curl -fsS \
  -H "Authorization: Bearer ${WARREN_API_TOKEN}" \
  "${WARREN_BASE_URL}/agents" | jq . 2>/dev/null || cat
