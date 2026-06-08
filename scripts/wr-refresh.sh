#!/usr/bin/env bash
# Refresh a Warren project's clone (re-fetch the default branch from GitHub) so the
# next dispatch's burrow sees current `main`. Run after merges / before a dispatch.
# Usage: wr-refresh.sh [project-id]   (defaults to $WARREN_PROJECT_ID)
# Requires WARREN_API_TOKEN + jq. Never prints the token.
set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/wr-env.sh"  # auto-load token + WARREN_PROJECT_ID/BASE_URL
WARREN_BASE_URL="${WARREN_BASE_URL:-http://localhost:8080}"
: "${WARREN_API_TOKEN:?WARREN_API_TOKEN is required}"
project_id="${1:-${WARREN_PROJECT_ID:?project id required (arg or WARREN_PROJECT_ID)}}"

curl -fsS \
  -X POST \
  -H "Authorization: Bearer ${WARREN_API_TOKEN}" \
  -H "Content-Type: application/json" \
  "${WARREN_BASE_URL}/projects/${project_id}/refresh" | jq . 2>/dev/null || cat
