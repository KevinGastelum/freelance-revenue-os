# Warren Project Contract

This repository is Warren-aware. Read this before dispatching any Warren run.

## Resolved constants (do NOT re-query)

Discovered Warren constants are recorded in **`.warren/project.json`** — the single
source of truth so neither agents nor humans re-query the API each session:

- **projectId** — `prj_cj3a8t7sdxyn`
- **baseUrl** — `http://localhost:8080`
- **defaultBranch** — `main`
- **API token** — auto-loads via `scripts/wr-env.sh` from the Warren server `.env`
  (`~/Documents/Coding/warren-kay/warren/.env`). Never `export` it by hand.

These are also pinned as env in `.claude/settings.local.json` and exported to the
shell by `wr-env.sh`, and `warren-guard.js` surfaces project id + base url into
context at SessionStart. If the Warren project is recreated, update `projectId` in
both `.warren/project.json` and `.claude/settings.local.json`.

## Warren Files

- `.warren/config.yaml` — default agent/runtime/branch behavior (review-first;
  `mergeStrategy: manual`).
- `.warren/triggers.yaml` — scheduled runs (all commented/disabled by default).
- `.warren/preview.yaml` — optional preview server (template only; no server yet).
- `.warren/pr-template.md` — PR body template (reminds humans to review).

## Agent Rules

1. Read `CLAUDE.md` and docs/PRD.md before making changes.
2. Prefer existing Seeds/Plot/Mulch context if those tools are present (they are
   not installed here yet).
3. Keep Warren prompts bounded, scoped, and testable.
4. Do not leak tokens or `.env` values.
5. Treat Warren output branches as **untrusted until reviewed**.
6. Do not enable cron triggers without explicit human approval.
7. Do not set or request auto-merge unless the human explicitly asks.
8. Never introduce automated platform actions (docs/PRD.md section 2): no
   auto-submit, auto-message, scraping, browser/anti-bot automation.

## Dispatch Prompt Checklist

Every Warren dispatch prompt must include:

- objective
- relevant files / directories
- constraints
- explicit out-of-scope / non-goals
- test / validation commands
- expected output branch behavior (branch/PR, no auto-merge)
- instruction to avoid secrets and `.env`
- instruction to keep changes minimal and reviewable

## Branch & Attribution

- Warren run branches use the `warren/...` prefix (`.warren/config.yaml`).
  The repo's own client-work branches follow the PRD convention
  `client/<platform>-<client>-<task-slug>` — keep those concerns separate.
- Commit/PR attribution: agent-authored commits (including Warren output) are
  attributed to **Kay / K-Bot-T1**; human commits to **KevinGastelum**. Do not
  add Claude/AI `Co-Authored-By` trailers.
