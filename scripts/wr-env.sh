#!/usr/bin/env bash
# Resolve + export WARREN_API_TOKEN if it is not already set.
#
# Sourced by every wr-*.sh so the Warren scripts self-load the token — you never
# have to `export WARREN_API_TOKEN=...` by hand at the start of a session. This is
# the single fix for the recurring "WARREN_API_TOKEN is required" session-start
# failure: a fresh shell has an empty env, and nothing else sets the token.
#
# - Never prints the token.
# - Strips CR + surrounding quotes (Windows CRLF .env gotcha -> 401 with \r appended).
# - set -e safe (wrapped in a function returning 0).
# - Override the source .env with:  export WARREN_ENV_FILE=/abs/path/to/.env
#
# Candidate .env files are tried in order; the first that yields a token wins.

_wr_load_token() {
  [ -n "${WARREN_API_TOKEN:-}" ] && return 0
  local f tok
  for f in \
    "${WARREN_ENV_FILE:-}" \
    "${HOME}/Documents/Coding/warren-kay/warren/.env" \
    "${HOME}/.warren/.env" \
    "${HOME}/warren/.env"; do
    [ -n "$f" ] && [ -f "$f" ] || continue
    tok="$(sed -n 's/^[[:space:]]*\(export[[:space:]]*\)\?WARREN_API_TOKEN=//p' "$f" 2>/dev/null \
            | head -n1 | tr -d '\r\n' | sed 's/^["'"'"']//; s/["'"'"']$//')"
    if [ -n "$tok" ]; then
      export WARREN_API_TOKEN="$tok"
      return 0
    fi
  done
  return 0
}
_wr_load_token
