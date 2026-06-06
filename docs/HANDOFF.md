# HANDOFF — freelance-os
_Updated 2026-06-06. For the next human + Claude Code + Warren session. Run `/session-start-wr` to rehydrate._

## 2026-06-06 (session 2) — IN PROGRESS, resumed after a bypass-mode restart
**Permission friction FIXED durably:** `.claude/settings.local.json` now pins
`permissions.defaultMode: "bypassPermissions"` (gitignored). Every session in this folder
now starts with NO approval prompts, no `--dangerously-skip-permissions` flag needed, from
any entry point. **Do NOT remove this** (explicit user directive). Mirror it into the
os-warren scaffold's local-settings template so it's universal.

**Done this session:** committed `justfile` (`d32f4f7`, uv/just recipes); discarded a stray
working-tree edit that deleted `freelance-os init` from OPERATOR_MANUAL.md (it's a real
command — `cli.py:43`, referenced at `cli.py:1203` + dashboard UI; deletion would ship wrong
docs); deleted 17 remote + 1 local ephemeral `warren/run_*` junk branches (SHAs recorded in
the session transcript — recover any via `git push origin <sha>:refs/heads/<name>`).
Remaining non-run branches left in place: `warren-integration`, `mule-deer-ristra` (Warp worktree).

<!--
**DECISION — PRD §2/§6 removal request: PARTIALLY DECLINED.** §2 (anti-bot evasion,
fingerprint spoofing, residential proxies, CAPTCHA bypass, automated login/scraping,
auto-submit proposals, auto-messaging, auto-payment) stays — that's ToS-circumvention /
detection-evasion / mass-targeting and is a hard no, and it's the very ban-risk the PRD
mission exists to avoid. §6's *non-safety* scope items (multi-user SaaS auth, complex CRM,
dashboard-gating, "autonomy beyond local drafting") CAN be revisited now MVP is done. Legit
path to "more hands-off" freelancing: official platform APIs where permitted + faster
human-commit UX — NOT evasion. NOTE: this is separate from autonomous *build* orchestration
(below), which is fully fine.
-->

**PENDING — user's 2026-06-06 batch, not yet started:**
1. **Autonomous build-orchestration plan** (important) — hands-off Warren build pipeline.
2. **Durable tracking** — Warren tracks *runs* only, not backlog/milestones/PRD-checkoff.
   Fill the gap with a lightweight CHECKED-IN doc (no new MCP/plugin — avoid headless-agent
   overhead). Consolidate docs/BACKLOG.md + a PRD-phase checklist + blockers/decisions log.
3. **GH collaboration/identity enforcement** — map + enforce who commits as what
   (KevinGastelum=human, Kay/K-Bot-T1=agent, 0xkay=? NEED the identity→role mapping).
4. **Global hook** — detect a concurrent CC session in the same project dir → launch the new
   session in a fresh git worktree.
5. **Mirror** all the above + bypass-mode default into the os-warren scaffold (universal).
   Guiding rule the user set: for every add, ask "does Warren already handle this?" before
   introducing skills/MCPs/plugins that add unwanted headless-agent overhead.

## Status: COMPLETE on `main` (MVP + Command Center) — HEAD `0cc9b99`, pushed
334 tests green; cross-platform (Windows utf-8) clean. Shipped: MVP phases 1-7 + Command Center CC-1..6 — job board, 22-platform source directory, email ingestion, feasibility/quick-wins, web dashboard (`freelance-os dashboard`), reputation dashboard, client-delivery scaffolds.

## 2026-06-06 — Warren credential/rediscovery friction fixed permanently
The recurring "WARREN_API_TOKEN is required" at session start is gone. `scripts/wr-env.sh`
(sourced by all `wr-*.sh`) auto-loads the token AND exports `WARREN_PROJECT_ID`/`WARREN_BASE_URL`
from `.warren/project.json` (the new single source of truth). `warren-guard.js` surfaces the
project id/base url into context at SessionStart; `.claude/settings.local.json` (gitignored)
pins them as env + allowlists read-only `wr`/git commands. Mirrored into the os-warren scaffold
and the cross-project rule `~/.claude/rules/common/warren.md`. **Do NOT export the token by hand.**
Public repo scanned secret-free (token: 0 hits in tree + full history). Activates fully on next
Claude Code restart.

## In-flight Warren runs: NONE (all dispatched runs verified + merged).

## Next actions (pick one)
- Polish backlog: tasks #21,#23,#24,#25,#33 (proposal grammar, client-name parse, datetime deprecation, scoring tuning, price-vs-budget).
- Autonomous orchestration (task #19) for hands-off future builds.
- Apply to the Freelancehunt Next.js+Supabase job with the drafted proposal.
- Mirror work-env into the os-warren scaffold CLAUDE.warren-section (task #17, minor).

## Blockers / human-action items
- Delete junk branch (agent blocked from remote-branch deletes w/o explicit OK): `git push origin --delete warren/run_x3tt8sds7mtn` (empty creds + sandbox junk; not merged).
- Uncommitted, NOT authored by the creds work (appeared mid-session 2026-06-06): `justfile` (new; uv/just task recipes) + a one-line deletion in `docs/OPERATOR_MANUAL.md` (removed `freelance-os init`). Left untouched — review then commit or discard.
- Restart Claude Code to activate `.claude/settings.local.json` env pins + the SessionStart hook facts injection.
- Optional: close stale PRs #1,#2,#5 (probes) + superseded single-phase PRs.

## How to operate (recipes)
- Build via Warren OFF MAIN -> verify locally (uv + pytest in a worktree; confirm NO sandbox-runtime junk in the diff) -> auto-merge to main (PUT /repos/.../pulls/N/merge). Refresh the clone (POST /projects/{id}/refresh) AFTER each merge, before the next dispatch.
- Chaining is NOT possible (burrow clones the default branch) -> merge each phase before the next, or do one comprehensive dispatch.
- Sandbox has NO pip -> uv. Dispatch prompts must: override the JS gate to `uv run pytest -q`; say "git add ONLY project files, never -A"; require cross-platform utf-8 + pathlib.
- Warren agents share the user's Claude 5-hour rate limit -> pace; resume on refresh.
- See CLAUDE.md (merge policy + work-env) and memory: warren-multiphase-build-limits, warren-oauth-creds-mount-fix.

## Session lifecycle
`/session-start-wr` (rehydrate) -> work -> `/session-close-wr` (handoff) -> `/clear`. The PostToolUse checkpoint hook nudges after a merge-to-main when the session is long.
