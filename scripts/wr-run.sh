#!/usr/bin/env bash
# Dispatch a Warren run.  Usage: wr-run.sh <agent> <project-id> "<prompt>"
# Example: wr-run.sh claude-code abc123 "Add tests for the lead scorer."
# Requires WARREN_API_TOKEN and jq. Never prints the token.
set -euo pipefail

agent="${1:?agent required, e.g. claude-code}"
project_id="${2:?project id required}"
prompt="${3:?prompt required}"

WARREN_BASE_URL="${WARREN_BASE_URL:-http://localhost:8080}"
: "${WARREN_API_TOKEN:?WARREN_API_TOKEN is required}"

if command -v jq >/dev/null 2>&1; then
  payload="$(jq -n \
    --arg agent "$agent" \
    --arg project "$project_id" \
    --arg prompt "$prompt" \
    '{agent:$agent, project:$project, prompt:$prompt}')"
else
  echo "jq is required for wr-run.sh" >&2
  exit 1
fi

curl -fsS \
  -X POST \
  -H "Authorization: Bearer ${WARREN_API_TOKEN}" \
  -H "Content-Type: application/json" \
  "${WARREN_BASE_URL}/runs" \
  -d "$payload" | jq . 2>/dev/null || cat
