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
(§20.2) holds, no protected files changed (see path guard below), adversarial
review finds nothing. The verifier is the review gate; the hard safety rules
above remain non-negotiable; a merge that breaks `main` must be auto-reverted.
Outside the pipeline (ad-hoc interactive work) commit/push when the human asks.
Build phases sequentially with per-phase commits, or in parallel where files are
disjoint, then auto-merge each.

**Path guard — auto-merge is SKIPPED (manual human review required) when the
branch/PR touches any protected path:**

- `.github/workflows/**` (CI/CD definitions)
- `Dockerfile*`, `docker-compose*` (container/runtime config)
- deploy/release config (`deploy/**`, `release*.yml`/`*.yaml`/`*.json`,
  `Procfile`, `fly.toml`, `render.yaml`, or equivalent)
- any path matching `*secret*`, `*credential*`, or `.env*`

A verifier must treat a diff touching these as NOT green for auto-merge,
regardless of test results.

---

# Warren Operating Contract

This repository is run against **Warren**, a self-hosted control plane for
sandboxed coding agents. The rules below are what matters when working inside
a Warren sandbox. Steering-side detail (dispatch checklists, prompt
requirements, multi-phase chaining, `wr-*.sh` commands) lives in
**docs/warren-runbook.md** and **docs/warren-project-contract.md**.

## Quality gate

`uv run pytest -q` — injected into every sandbox as `$WARREN_QUALITY_GATE`
(source: `.warren/config.yaml`). The sandbox has **no pip**; use uv. The gate
must pass before you commit.

## Branch & commit expectations

- Work on the branch the sandbox gives you (`warren/...`); never switch to `main`.
- **Always commit at least once** — uncommitted work is lost when the run ends.
- **Never push manually** — warren reaps and pushes the workspace branch itself.
- Keep changes minimal and reviewable; commit per logical phase.
- Merging is governed by the verifier-gated, path-guarded policy in
  "Commit, PR & merge policy" above.

## Secrets

Never print, commit, or paste `WARREN_API_TOKEN`, `ANTHROPIC_API_KEY`,
`GITHUB_TOKEN`, or `.env` contents. A local guard
(`.claude/hooks/warren-guard.js`, wired via `.claude/settings.json`) blocks the
obvious leaks; it fails open and is best-effort — not a substitute for care.

## Issue tracking & memory

If `.seeds/` is present, use `sd` (prime at session start, close finished
seeds, `sd sync` before finishing). If `.mulch/` is present, use `ml` (prime at
start, record insights, `ml sync`).
