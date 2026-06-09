# CLAUDE.md

## Objectives & Goals (set 2026-06-06)

**Mission:** turn `freelance-os` into an AI-leveraged revenue engine — surface high-margin,
easy-to-deliver gigs and draft winning applications so the operator lands paid work fast.

**Immediate goal:** $100 real profit (operator's personal account) by **2026-06-14** — the
ROI checkpoint for the Claude subscription. Revenue-producing work outranks polish/infra until then.

**Scoring — margin, not stack:** rank leads by **AI-leverage margin** =
(budget ÷ estimated effort-hours) × confidence. Any stack is in scope; breadth (the AI) is the
edge, so an obscure-but-bounded task is a *feature*, not a disqualifier. Never weight by
human-stack match.

**Reputation mode:** while the account has few/no reviews, accept and surface **low-dollar gigs**
that buy reviews, ratings, and good feedback — reputation compounds and unlocks bigger work.
Score reputation-building value alongside compensation; don't reject a gig for being cheap if
it's an easy win that builds standing.

**Division of labor:** the operator sources raw lead data by his own means; Claude builds
everything downstream — ingestion (against the lead schema), the margin scorer, draft generation,
and orchestration — pulling from legitimate public APIs/RSS + the operator's own alert inbox.
See memory `freelance-pivot-and-deadline`.

**Build roadmap:** (1) `freelance-os pull` (public APIs → schema → margin score → ranked
shortlist; spec: `docs/pull-build-spec.md`), (2) schema ingest (CSV/JSON/inbox), (3) per-lead
draft generation, (4) orchestration.

## Work environment (cross-platform — IMPORTANT)

The **Warren sandbox runs Linux**; the **developer host is Windows** (Windows
Terminal + MSYS2, cp1252 default). Code green in the Linux sandbox can still
break when run locally on Windows, so all generated code MUST be cross-platform:

- **Always** pass `encoding="utf-8"` to `open()`/`read_text()`/`write_text()`
  (Windows cp1252 raises `UnicodeEncodeError` on non-ASCII like arrows/bullets).
- Use `pathlib`; never hardcode `/` paths or the sandbox path `/workspace`.
- Guard POSIX-only features (chmod +x, tmux) with `os.name != "nt"` and
  `@pytest.mark.skipif(os.name == "nt")`. tmux/exec scripts are *generated*
  portably but only *run* on Linux/macOS.
- The sandbox has **no pip** — use **uv** (`uv venv`, `uv pip install -e ".[dev]"`,
  `uv run pytest -q`); a dispatch's quality gate must override the agent default
  JS gate to that uv command.
- Always **verify returned branches locally on Windows** (uv + pytest) before merge.

## Commit, PR & merge policy

Agent-authored commits/branches (including Warren output) are attributed to
**Kay / K-Bot-T1**. Human commits are attributed to **KevinGastelum**. Never add
Claude/AI `Co-Authored-By` trailers.

**Merge policy (set 2026-06 by KevinGastelum — supersedes the earlier
"never auto-merge / commit only when asked" rule):** in the autonomous build
pipeline, agents MAY commit, push, and **auto-merge a Warren branch to `main`
once a verifier agent confirms it is green** — tests pass, safety acceptance
(§20.2) holds, no protected files changed, adversarial review finds nothing. The
verifier is the review gate; the hard safety rules above remain non-negotiable;
a merge that breaks `main` must be auto-reverted. Outside the pipeline (ad-hoc
interactive work) commit/push when the human asks. Build phases sequentially with
per-phase commits, or in parallel where files are disjoint, then auto-merge each.

---

# Warren Operating Contract

This repository is configured to interface with **Warren**, a self-hosted control
plane for sandboxed coding agents. Warren runs at `http://localhost:8080`
(Docker + UI) on this machine; the `warren`/`wr` CLI is **not** on PATH, so use
the HTTP API via `scripts/wr-*.sh` (Git Bash) or the Warren UI.

Full operational detail: **docs/warren-runbook.md** and
**docs/warren-project-contract.md**.

## When to use Warren

Use Warren when work should run in an isolated sandbox and return as a branch/PR:

- larger implementation tasks or risky refactors
- scheduled maintenance
- tasks benefiting from live event streaming, steering, or previews
- tasks that should not mutate the local working tree

Prefer **local Claude Code** for: small edits, inspection, quick doc changes,
interactive debugging, and anything needing immediate human back-and-forth.

Use **Overstory** (`ov`, when available) for local Claude Code multi-agent
orchestration; use **Warren** for server/control-plane/sandboxed branch-return.

## Multi-phase work (chaining limits)

Every Warren dispatch's burrow clones the project's **default branch (`main`)** —
`ref`/`continueFromRunId` do NOT repoint the workspace in this build. So you
**cannot stack unmerged phase branches**. Build multi-phase work either as (a) one
comprehensive dispatch with per-phase commits, or (b) phase-by-phase dispatches
where each is **auto-merged to `main` (on green verifier) before the next is
dispatched** — refresh the project clone (`POST /projects/{id}/refresh`) after each
merge so the next dispatch sees it.

## Required checks before a Warren dispatch

1. Read this `CLAUDE.md` and docs/PRD.md.
2. `bash scripts/wr-health.sh`
3. `bash scripts/wr-projects.sh`
4. Confirm the correct project id.
5. Check for `.seeds/`, `.mulch/`, `.plot/`, `.canopy/`. If `.seeds/` appears,
   prefer existing ready seeds; if `.plot/` appears, bind to a Plot; if `.mulch/`
   appears, prime/search memory first.

## Warren dispatch prompt requirements

Every dispatch prompt must include: objective · relevant files/dirs · constraints
· explicit non-goals · validation/test command · branch/PR expectation
(auto-merge to `main` on green verifier) · "do not expose secrets/.env" · "keep
changes minimal and reviewable". For Python builds also require: **use uv (no pip
in the sandbox); override the default JS gate to `uv run pytest -q`; write
cross-platform code (utf-8 + pathlib + guard POSIX features); commit after each
phase.**

## Warren safety rules

- Never print, commit, or paste `WARREN_API_TOKEN`.
- Never paste `.env` contents into prompts or the terminal.
- Never dispatch destructive work without explicit human approval.
- Scheduled triggers require human approval; the autonomous pipeline's
  wake-on-rate-limit-refresh resume is approved (2026-06).
- Auto-merge a Warren branch to `main` ONLY after a verifier agent confirms green
  (tests + §20.2 safety + no protected-file changes); auto-revert if it breaks `main`.
- Treat unverified Warren output as untrusted — the verifier is the review gate.
- Never let a Warren run introduce the prohibited automation listed above.

A local guard (`.claude/hooks/warren-guard.js`, wired via `.claude/settings.json`)
blocks obvious token/`.env` leaks and Warren project deletes from agent shells.
It fails open and is best-effort — not a substitute for the rules above.

## Useful commands

```bash
bash scripts/wr-health.sh
bash scripts/wr-projects.sh
bash scripts/wr-agents.sh
bash scripts/wr-run.sh claude-code <project-id> "Prompt here"
bash scripts/wr-events.sh <run-id>
bash scripts/wr-steer.sh <run-id> "Steering message"
bash scripts/wr-cancel.sh <run-id>
```
