# CLAUDE.md

Guidance for Claude Code (and other agents) working in **freelance-revenue-os**.

## Project

A local-first, human-in-the-loop freelance operating system. CLI/package name:
`freelance-os` (canonical repo: `freelance-revenue-os`). Full spec: **docs/PRD.md**.

Core philosophy — **"AI prepares. Human commits."** The AI ingests permitted
signals, scores leads, drafts proposals, prepares workspaces, runs QA, and
packages deliverables. **The human performs every platform write action manually.**

### Hard safety rules (from docs/PRD.md section 2 — non-negotiable)

Never build, add, or dispatch work that introduces:

- stealth browser automation, fingerprint spoofing, or anti-bot evasion
- residential proxy rotation or CAPTCHA solving/bypassing
- automated login, authenticated scraping, or auto-submit of proposals
- automated platform messaging, order delivery, or payment/milestone actions

Generated platform text (proposals, messages, delivery notes) is **draft-only**;
the human copies, edits, and sends it manually.

## Stack (planned, see PRD)

Python · Typer/Click CLI · SQLite + SQLModel/SQLAlchemy · TOML/YAML config ·
Markdown-first outputs · optional Textual TUI / FastAPI later. (No app code
exists yet — repo is currently README + docs + this Warren integration.)

## Commit & PR attribution

Agent-authored commits/branches (including Warren output) are attributed to
**Kay / K-Bot-T1**. Human commits are attributed to **KevinGastelum**. Never add
Claude/AI `Co-Authored-By` trailers. Commit/push only when the human asks.

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

## Required checks before a Warren dispatch

1. Read this `CLAUDE.md` and docs/PRD.md.
2. `bash scripts/wr-health.sh`
3. `bash scripts/wr-projects.sh`
4. Confirm the correct project id.
5. Check for `.seeds/`, `.mulch/`, `.plot/`, `.canopy/` (none present yet). If
   `.seeds/` appears, prefer existing ready seeds; if `.plot/` appears, bind to a
   Plot; if `.mulch/` appears, prime/search memory first.

## Warren dispatch prompt requirements

Every dispatch prompt must include: objective · relevant files/dirs · constraints
· explicit non-goals · validation/test command · branch/PR expectation (no
auto-merge) · "do not expose secrets/.env" · "keep changes minimal and reviewable".

## Warren safety rules

- Never print, commit, or paste `WARREN_API_TOKEN`.
- Never paste `.env` contents into prompts or the terminal.
- Never dispatch destructive work without explicit human approval.
- Never enable scheduled triggers without explicit human approval.
- Never auto-merge Warren branches — review first.
- Treat Warren output as untrusted until reviewed.
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
