# Warren Runbook

## Purpose

Warren is this project's sandboxed agent **control plane**. It dispatches
short-lived coding runs against the GitHub repo, streams events, lets you
steer/cancel mid-run, and returns work as a **branch or PR** for human review.
It is not the `freelance-os` app itself — it is the layer that runs agents
*on* this repo.

<!-- This repo's own philosophy (docs/PRD.md) is **"AI prepares. Human commits."**
Warren fits that exactly: agents prepare branches; a human reviews and merges. -->

## Environment (this machine)

- Shell: **Git Bash in Windows Terminal**. All `scripts/wr-*.sh` are POSIX bash
  and run with `bash scripts/wr-...` from the repo root.
- `WARREN_BASE_URL` — Warren HTTP API base. Default `http://localhost:8080`.
- `WARREN_API_TOKEN` — required for authenticated endpoints (everything except
  liveness). **Never** print, commit, echo, or paste it.

**You normally do NOT export the token by hand.** Every `scripts/wr-*.sh` sources
`scripts/wr-env.sh`, which auto-loads `WARREN_API_TOKEN` from the Warren server
checkout's `.env` if it isn't already set — so `bash scripts/wr-projects.sh` just
works in a fresh shell. Resolution order:

1. `WARREN_API_TOKEN` already in the env (left untouched)
2. `$WARREN_ENV_FILE` (set this to override)
3. `~/Documents/Coding/warren-kay/warren/.env`  <- canonical on this machine
4. `~/.warren/.env`, then `~/warren/.env`

If a script ever prints `WARREN_API_TOKEN is required`, the `.env` moved — point
`WARREN_ENV_FILE` at the Warren checkout's `.env` and re-run (never echo it):

```bash
export WARREN_ENV_FILE="/c/Users/you/path/to/warren/.env"   # only if auto-load fails
```

`wr-env.sh` strips CR + quotes (the Windows CRLF `.env` gotcha) and never prints
the token. Manual override (e.g. a token from the Warren UI) still works — an
already-set `WARREN_API_TOKEN` wins:

```bash
export WARREN_BASE_URL="http://localhost:8080"             # optional; this is the default
export WARREN_API_TOKEN="...paste from the Warren UI..."    # only to override; never echo this
```

> The `warren` / `wr` CLI is **not** on PATH on this machine — Warren runs as the
> Docker container + localhost UI. So use the HTTP API via the scripts below, or
> the Warren UI, rather than `warren <cmd>`. If you later install the CLI, the
> CLI forms in this doc become available too.

> API endpoint paths/payloads below follow the Warren integration spec. If your
> installed Warren version differs, adjust the scripts in `scripts/` and re-test.

## Quick Health Check

Liveness is unauthenticated; readiness needs the token.

```bash
bash scripts/wr-health.sh
```

## List Projects

```bash
bash scripts/wr-projects.sh
```

## List Agents / Runtimes

```bash
bash scripts/wr-agents.sh
```

## Add / Register This Project

CLI (only if you install it):

```bash
warren add-project https://github.com/KevinGastelum/freelance-revenue-os.git --default-branch main
```

Otherwise register through the **Warren UI** (point it at the repo above with
default branch `main`). Confirm it appears in `bash scripts/wr-projects.sh`.

## Dispatch a Run

```bash
bash scripts/wr-run.sh claude-code <project-id> "Bounded implementation prompt here"
```

Capture the returned **run id** from the JSON response.

## Stream Events

```bash
bash scripts/wr-events.sh <run-id>
```

## Steer a Run

```bash
bash scripts/wr-steer.sh <run-id> "Adjust course: focus only on tests and docs."
```

## Cancel a Run

```bash
bash scripts/wr-cancel.sh <run-id>
```

## Guided Dispatch (health + projects + prompt)

```bash
bash scripts/wr-dispatch-current-repo.sh                 # interactive
bash scripts/wr-dispatch-current-repo.sh <project-id> "Prompt"
```

## When to Use Warren

- Work that should happen in an isolated sandbox and come back as a branch/PR.
- Larger implementation tasks or risky refactors that should not mutate your
  local working tree.
- Tasks where live event streaming, steering, previews, or scheduling help.

## When NOT to Use Warren

- Tiny edits, local exploration, quick doc tweaks.
- Anything touching secrets or `.env`.
- Work needing tight human back-and-forth every few minutes — do that locally.

## Required checks before a Warren dispatch

1. Read `CLAUDE.md` and docs/PRD.md.
2. `bash scripts/wr-health.sh`
3. `bash scripts/wr-projects.sh`
4. Confirm the correct project id.
5. Check for `.seeds/`, `.mulch/`, `.plot/`, `.canopy/`. If `.seeds/` appears,
   prefer existing ready seeds; if `.plot/` appears, bind to a Plot; if `.mulch/`
   appears, prime/search memory first.

## Dispatch prompt requirements

Every dispatch prompt must include: objective · relevant files/dirs · constraints
· explicit non-goals · validation/test command · branch/PR expectation
(auto-merge to `main` only via the verifier-gated, path-guarded policy in
`CLAUDE.md`) · "do not expose secrets/.env" · "keep changes minimal and
reviewable". For Python builds also require: **use uv (no pip in the sandbox);
override the default JS gate to `uv run pytest -q`; write cross-platform code
(utf-8 + pathlib + guard POSIX features); commit after each phase.**

## Multi-phase work (chaining limits)

Every Warren dispatch's burrow clones the project's **default branch (`main`)** —
`ref`/`continueFromRunId` do NOT repoint the workspace in this build. So you
**cannot stack unmerged phase branches**. Build multi-phase work either as (a) one
comprehensive dispatch with per-phase commits, or (b) phase-by-phase dispatches
where each is **auto-merged to `main` (on green verifier) before the next is
dispatched** — refresh the project clone (`POST /projects/{id}/refresh`) after each
merge so the next dispatch sees it.

## Plan-Runs with Seeds (optional)

Seeds (`sd`) is **not installed** on this machine yet. If you add it, turn large
work into a Seeds plan and dispatch the plan through Warren so each child seed
completes and is verified before the next — see `.claude/skills/warren-plan-run`.

## Plot-Bound Runs (optional)

Plot (`plot`) is **not installed** yet. When present, bind larger initiatives to
a Plot and set `plotSync` in `.warren/config.yaml` (already `mergeStrategy:
manual`, so nothing auto-merges).

## Previews

No dev server exists yet (Python CLI MVP), so `.warren/preview.yaml` is a
commented template. Fill it in if/when the optional FastAPI layer lands.

## Scheduled Triggers

`.warren/triggers.yaml` ships fully commented. **Do not enable cron without
explicit human approval.**

## Safety

- Never print, echo, or commit `WARREN_API_TOKEN`.
- Never paste `.env` contents into a prompt or the terminal.
- Never ask a Warren agent to exfiltrate secrets.
- Never dispatch destructive operations without explicit human approval.
- Auto-merge a Warren branch only via the verifier-gated, path-guarded merge
  policy in `CLAUDE.md`; otherwise review first.
<!-- - Honor docs/PRD.md section 2: **no** automated platform actions (no auto-submit,
  auto-message, scraping, browser/anti-bot automation) may be introduced. -->
- A local Claude Code guard (`.claude/hooks/warren-guard.js`) blocks the most
  obvious token/`.env` leaks and Warren project deletes. It is best-effort
  defense-in-depth, not a guarantee — stay careful.

## Troubleshooting

```bash
bash scripts/wr-health.sh          # liveness + readiness
# In the Warren repo / wherever docker-compose lives:
docker compose ps
docker compose logs --tail=200
# If you install the CLI:
warren doctor
```

- `jq` is required by the dispatch/steer scripts (it builds the JSON payload).
  It resolves in Git Bash here. If missing, install it.
- 401/403 → `WARREN_API_TOKEN` unset or stale.
- Connection refused → Warren container not running, or wrong `WARREN_BASE_URL`.
