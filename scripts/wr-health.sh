#!/usr/bin/env bash
# Warren health: liveness (unauthenticated) + readiness (needs token).
# See docs/warren-runbook.md. Never prints WARREN_API_TOKEN.
set -euo pipefail

WARREN_BASE_URL="${WARREN_BASE_URL:-http://localhost:8080}"

echo "Checking Warren liveness at ${WARREN_BASE_URL}/healthz"
curl -fsS "${WARREN_BASE_URL}/healthz"
echo

if [ -n "${WARREN_API_TOKEN:-}" ]; then
  echo "Checking Warren readiness at ${WARREN_BASE_URL}/readyz"
  curl -fsS \
    -H "Authorization: Bearer ${WARREN_API_TOKEN}" \
    "${WARREN_BASE_URL}/readyz" | jq . 2>/dev/null || true
else
  echo "WARREN_API_TOKEN is not set; skipping authenticated readiness check."
fi
