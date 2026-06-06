#!/usr/bin/env bash
# Guided Warren dispatch for this repo: health -> projects -> prompt -> run.
# Usage: wr-dispatch-current-repo.sh [project-id] ["prompt"]
# If args are omitted, prompts interactively. Requires WARREN_API_TOKEN.
set -euo pipefail

WARREN_BASE_URL="${WARREN_BASE_URL:-http://localhost:8080}"
source "$(dirname "${BASH_SOURCE[0]}")/wr-env.sh"  # auto-load WARREN_API_TOKEN (see wr-env.sh)
: "${WARREN_API_TOKEN:?WARREN_API_TOKEN is required}"

here="$(cd "$(dirname "$0")" && pwd)"

project_id="${1:-${WARREN_PROJECT_ID:-}}"   # defaults to .warren/project.json via wr-env.sh
prompt="${2:-}"

bash "${here}/wr-health.sh"

if [ -z "$project_id" ]; then
  echo
  echo "Available Warren projects:"
  bash "${here}/wr-projects.sh"
  echo
  read -r -p "Enter Warren project id: " project_id
fi

if [ -z "$prompt" ]; then
  echo
  echo "Enter bounded Warren prompt. Finish with Ctrl-D:"
  prompt="$(cat)"
fi

bash "${here}/wr-run.sh" claude-code "$project_id" "$prompt"
