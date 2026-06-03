#!/usr/bin/env bash
# Stream events for a Warren run (SSE/long-poll).  Usage: wr-events.sh <run-id>
# Requires WARREN_API_TOKEN. Ctrl-C to stop following.
set -euo pipefail

run_id="${1:?run id required}"

WARREN_BASE_URL="${WARREN_BASE_URL:-http://localhost:8080}"
: "${WARREN_API_TOKEN:?WARREN_API_TOKEN is required}"

curl -N \
  -H "Authorization: Bearer ${WARREN_API_TOKEN}" \
  "${WARREN_BASE_URL}/runs/${run_id}/events?follow=1"
