# Architecture — Freelance Revenue OS

## Overview

A local-first Python CLI application. No cloud dependencies for core features.

## Stack

- **Language:** Python 3.11+
- **CLI:** Typer (with Rich for output formatting)
- **Database:** SQLite (via SQLModel / SQLAlchemy)
- **Config:** TOML (settings) + YAML (portfolio, banned phrases)
- **Outputs:** Markdown files

## Project Layout

```
src/freelance_os/
  __init__.py          — package version
  cli.py               — Typer CLI entry point
  config.py            — config loader with safety enforcement
  db.py                — SQLite engine and session management
  models.py            — SQLModel data models
  schemas.py           — Pydantic schemas for CLI I/O

  ingestion/           — Lead intake modules
    manual.py          — URL and text intake

  scoring/             — Lead scoring engine
    lead_scorer.py     — base scoring (0–100)
    risk_rules.py      — risk penalty rules

  proposal/            — Proposal drafting
    templates.py       — proposal template
    portfolio_matcher.py — matches portfolio items to leads
    draft_generator.py — deterministic draft generation (no LLM)
    proposal_validator.py — validates draft against safety rules

  client/              — Client project workspace
    workspace.py       — directory tree creation
    scope.py           — scope document generation
    milestones.py      — milestone document generation
    delivery.py        — delivery package generation

  execution/           — Execution harness (generate scripts only)
    tmux.py            — tmux session script generator
    worktree.py        — git worktree dry-run helper
    qa.py              — QA checklist generation

  reports/             — Reporting
    outcome_report.py  — weekly performance report
    dashboard.py       — dashboard stub
```

## Data Flow

```
Lead Intake → Lead Scoring → Proposal Draft → Human Review
                                                    ↓
                                          Lead Status: WON
                                                    ↓
                                        Client Workspace Init
                                                    ↓
                                        Execution & Delivery
                                                    ↓
                                          Outcome Tracking
                                                    ↓
                                          Weekly Report
```

## Safety Architecture

Config safety is enforced in `config.py:Settings._validate_safety()`.
Any config with unsafe flags raises `UnsafeConfigError` before the CLI runs.

See `docs/SAFETY_POLICY.md` for the full safety policy.
