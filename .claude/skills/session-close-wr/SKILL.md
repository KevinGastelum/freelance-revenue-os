---
name: session-close-wr
description: Close out a Warren-driven Claude Code session — capture a complete, durable handoff (git state, in-flight Warren runs, PRs, tasks, blockers), clean up, and write it to memory + docs/HANDOFF.md so the next session can /clear and resume with zero drift. TRIGGER when wrapping a session, before /clear, or at a milestone.
---

# session-close-wr

Goal: make the session safely DISPOSABLE. Produce a handoff so a fresh session (reading CLAUDE.md + memory + docs/HANDOFF.md + the task list) resumes with no re-discovery. Do ALL of:

1. **Git state** — `git log --oneline -5`, current branch, `git status --porcelain`. Record the `main` HEAD SHA + any uncommitted work.
2. **In-flight Warren runs (CRITICAL)** — for every dispatched run not yet verified+merged, record run IDs + states (GET /runs/{id}). The next session MUST resume polling/verifying these. (Export WARREN_API_TOKEN via sed from the warren .env; never echo it; jq for output.)
3. **PRs** — which merged, which open/pending review.
4. **Tasks** — snapshot TaskList: completed / in_progress / pending / backlog.
5. **Blockers & human-action items** — rate-limit reset time, "delete branch X", "merge PR Y", "rotate Z", anything needing the human or their explicit auth (destructive remote ops, etc.).
6. **Cleanup** — `git worktree prune` + remove stale verify worktrees; stop stray background servers (dashboards/tuners) you launched.
7. **Persist the handoff to BOTH**:
   - the `session-handoff` memory file (update the RESUME POINT + current state), and
   - `docs/HANDOFF.md` (commit it) — a human-readable snapshot: what's done · the single next action · in-flight runs to resume · blockers · key recipes not already in CLAUDE.md.
8. **Emit a restart message** — a ready `/clear` recommendation + a one-line "start here" (or note that `session-start-wr` will rehydrate).

Keep it factual + scannable. Never print secrets.
