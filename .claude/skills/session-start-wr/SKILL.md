---
name: session-start-wr
description: Bootstrap a fresh Warren-driven Claude Code session — rehydrate from CLAUDE.md, memory, docs/HANDOFF.md, the task list, and git; run the Warren pre-flight; resume any in-flight runs; and present where-we-are + next + blockers. TRIGGER at the start of a session continuing prior Warren work.
---

# session-start-wr

Rehydrate from durable artifacts (do NOT rely on recalling a prior conversation). Do ALL of:

1. **Read** — CLAUDE.md, the `session-handoff` memory (+ linked Warren memories), `docs/HANDOFF.md`, and the TaskList.
2. **Git** — `git fetch origin`; `git log --oneline -5`; fast-forward local `main` to `origin/main` if behind; `git status`.
3. **Warren pre-flight** — `bash scripts/wr-health.sh`; `bash scripts/wr-projects.sh`; confirm the project id. **The token auto-loads:** every `wr-*.sh` sources `scripts/wr-env.sh`, which reads `WARREN_API_TOKEN` from the Warren server `.env` (default `~/Documents/Coding/warren-kay/warren/.env`; override with `WARREN_ENV_FILE`). You do NOT need to `export` it by hand. If a script still says "WARREN_API_TOKEN is required", the `.env` moved — set `WARREN_ENV_FILE=/abs/path/to/.env` (point it at the Warren checkout's `.env`) and re-run; never echo the token. See [[warren-token-source]].
4. **Resume in-flight runs** — for any run IDs in the handoff not yet verified+merged, poll GET /runs/{id}; when terminal, verify locally (uv + pytest in a worktree, confirm NO sandbox-runtime junk in the diff) and auto-merge per the CLAUDE.md merge policy.
5. **Surface** — a crisp summary: what's done · the immediate next task · blockers/human-action items · backlog.
6. Proceed with the next task (or ask the human if a decision is pending).
