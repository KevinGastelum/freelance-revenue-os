# HANDOFF — freelance-os
_Updated 2026-06-05. For the next human + Claude Code + Warren session. Run `/session-start-wr` to rehydrate._

## Status: COMPLETE on `main` (MVP + Command Center)
334 tests green; cross-platform (Windows utf-8) clean. Shipped: MVP phases 1-7 + Command Center CC-1..6 — job board, 22-platform source directory, email ingestion, feasibility/quick-wins, web dashboard (`freelance-os dashboard`), reputation dashboard, client-delivery scaffolds.

## In-flight Warren runs: NONE (all dispatched runs verified + merged).

## Next actions (pick one)
- Polish backlog: tasks #21,#23,#24,#25,#33 (proposal grammar, client-name parse, datetime deprecation, scoring tuning, price-vs-budget).
- Autonomous orchestration (task #19) for hands-off future builds.
- Apply to the Freelancehunt Next.js+Supabase job with the drafted proposal.
- Mirror work-env into the os-warren scaffold CLAUDE.warren-section (task #17, minor).

## Blockers / human-action items
- Delete junk branch (agent blocked from remote-branch deletes w/o explicit OK): `git push origin --delete warren/run_x3tt8sds7mtn` (empty creds + sandbox junk; not merged).
- Optional: close stale PRs #1,#2,#5 (probes) + superseded single-phase PRs.

## How to operate (recipes)
- Build via Warren OFF MAIN -> verify locally (uv + pytest in a worktree; confirm NO sandbox-runtime junk in the diff) -> auto-merge to main (PUT /repos/.../pulls/N/merge). Refresh the clone (POST /projects/{id}/refresh) AFTER each merge, before the next dispatch.
- Chaining is NOT possible (burrow clones the default branch) -> merge each phase before the next, or do one comprehensive dispatch.
- Sandbox has NO pip -> uv. Dispatch prompts must: override the JS gate to `uv run pytest -q`; say "git add ONLY project files, never -A"; require cross-platform utf-8 + pathlib.
- Warren agents share the user's Claude 5-hour rate limit -> pace; resume on refresh.
- See CLAUDE.md (merge policy + work-env) and memory: warren-multiphase-build-limits, warren-oauth-creds-mount-fix.

## Session lifecycle
`/session-start-wr` (rehydrate) -> work -> `/session-close-wr` (handoff) -> `/clear`. The PostToolUse checkpoint hook nudges after a merge-to-main when the session is long.
