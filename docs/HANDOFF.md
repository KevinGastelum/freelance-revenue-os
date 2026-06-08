# HANDOFF — freelance-os
_Updated 2026-06-07 (session 4). For the next human + Claude Code + Warren session. Run `/session-start-wr` to rehydrate._

## START HERE
- **Status:** the revenue-pivot build pipeline is SHIPPED. `freelance-os pull` (PR #16) and
  `freelance-os ingest` (PR #17) are both built, verified, and merged. `main` @ **57eea9e**, **431 tests green**.
- **HARD DEADLINE (Kevin):** $100 real profit by **2026-06-14** (Claude subscription ROI). Revenue outranks polish.
- **Single next action:** dispatch **BUILD #3 — scoring tuning** (spec below) via Warren — OR Kevin starts
  feeding real gig leads to `freelance-os ingest <leads.csv>` (ranking is already sound enough to triage).
- **Division of labor:** Kevin sources raw lead data; Claude builds downstream (scorer/ingest/drafts/
  orchestration). No proxy/burner/anti-bot scraping. Memory: `freelance-pivot-and-deadline`.

## What shipped this session (2026-06-07)
- **`freelance-os pull`** (PR #16 + UA fix `9b4a1f1`): public no-auth APIs (Remotive, RemoteOK, Jobicy, HN)
  -> lead schema -> AI-leverage margin score (reputation-mode ON, no stack-match) -> ranked table / `--json`
  -> top-K drafts -> optional `--persist`. All 4 sources live (Remotive+Jobicy were 403ing the bare urllib UA).
- **`freelance-os ingest PATH`** (PR #17): operator CSV/JSON -> SAME margin schema -> SAME pipeline. The
  score/rank/render logic now lives in `scoring/pipeline.py` (refactored out of `pull`; both call it, DRY).
- New files: `ingestion/pull.py`, `scoring/margin.py`, `ingestion/ingest.py`, `scoring/pipeline.py`,
  `tests/fixtures/sample_leads.csv`, `scripts/wr-refresh.sh`. All commits Kay / K-Bot-T1.

## BUILD #3 — scoring tuning (the next build; via Warren)
Live demos showed the output is not yet decision-useful on PUBLIC sources:
1. **Margin saturation** — `score_lead` uses `norm_margin = min(1, margin / 200)`; every lead above $200/hr
   maxes out, so a $90k and a $180k lead score identically (~0.80). Raise/curve the reference (or log-scale).
2. **Salary vs project budget** — public boards return SALARIED roles; `$90,000/yr` is treated as a fixed gig
   budget. Detect/flag annual comp; don't compute $/hr from a salary.
3. **Effort heuristic too flat** — most descriptions resolve to 40h; add signal.
4. **Draft grammar (#21)** — `draft_generator` emits "a authentication", "a in small task".
- Sanity: `ingest` on REAL project budgets already ranks correctly (a $50 logo tweak lands last) — so this is
  tuning, not a rebuild. Files: `scoring/margin.py`, `scoring/pipeline.py`, `proposal/draft_generator.py`.

## In-flight Warren runs: NONE (run_cx9j5xyq4xf7 -> PR#16 merged; run_zg4wczbz5ye7 -> PR#17 merged).

## Blockers / human-action items
- **Kevin's 4 uncommitted edits** (untouched all session — his decision): `.claude/hooks/warren-guard.js`
  (security hook; live-verified intact), `CLAUDE.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`. Commit or discard.
- **Stale merged remote branches** (needs Kevin's OK): `git push origin --delete warren/run_cx9j5xyq4xf7
  warren/run_zg4wczbz5ye7`.
- Optional: scope the ECC fact-gate hook to code-only (it fired on every doc/scratch write again).

## Carried-over backlog (not addressed this session)
- Autonomous build-orchestration plan (hands-off Warren pipeline) — task #19.
- Durable tracking: a checked-in backlog/PRD-checkoff doc (no new MCP/plugin).
- GH identity->role enforcement (KevinGastelum=human, Kay/K-Bot-T1=agent, 0xkay=? — need the mapping).
- Global hook: detect a concurrent CC session in the same dir -> launch the new one in a fresh worktree.
- Mirror session learnings + bypass-mode default into the os-warren scaffold.
- Polish: #23 client-name parse, #24 datetime.utcnow() deprecation (the 406 test warnings), #25 price-vs-budget
  (overlaps #3), #33 scoring tuning (= #3).

## Recipes (Warren build loop — not already in CLAUDE.md)
- **Refresh the clone before EVERY dispatch:** `bash scripts/wr-refresh.sh <project-id>` (new; the burrow
  clones origin/main, so refresh after each push/merge).
- **ASCII-only dispatch prompts** — non-ASCII mangles through MSYS2 `cat | jq` in wr-run.sh.
- **Dispatch:** write the prompt to `.warren/tmp/<name>.md` (gitignored), then
  `bash scripts/wr-run.sh claude-code <project-id> "$(cat .warren/tmp/<name>.md)"`.
- **Verify+merge:** `git worktree add --detach <wt> origin/<branch>` -> `uv venv && uv pip install -e ".[dev]"
  && uv run pytest -q` + live CLI check -> `git merge --no-ff -c user.name="Kay / K-Bot-T1"
  -c user.email="k-bot-t1@freelance-revenue-os" origin/<branch>` -> `git push origin main` -> remove worktree.
- Build env: sandbox has NO pip -> uv; override the JS gate to `uv run pytest -q`; cross-platform utf-8 + pathlib.

## Session lifecycle
`/session-start-wr` (rehydrate) -> work -> `/session-close-wr` (this handoff) -> `/clear`.
