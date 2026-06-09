# Architecture — Freelance Revenue OS

## Overview

Freelance Revenue OS is a local-first, <!-- human-in-the-loop --> CLI application for managing freelance work.

```
freelance-os (CLI)
  |
  +-- config/          Config files (TOML/YAML)
  +-- data/            SQLite database (local only)
  +-- src/freelance_os/
  |     +-- cli.py          Typer CLI entry point
  |     +-- config.py       Config loader (with safety enforcement)
  |     +-- db.py           SQLAlchemy/SQLModel engine + session
  |     +-- models.py       ORM models (Lead, ProposalDraft, etc.)
  |     +-- schemas.py      Pydantic input schemas
  |     +-- ingestion/      Lead intake (manual URL, text, CSV)
  |     +-- scoring/        Lead scoring and risk assessment
  |     +-- proposal/       Proposal drafting and validation
  |     +-- client/         Client workspace management
  |     +-- execution/      Tmux scripts and worktree helpers (dry-run)
  |     +-- reports/        Weekly reports and outcome tracking
  |     +-- utils/          Text, date, file utilities
  +-- tests/           pytest test suite
  +-- client-work/     Generated client workspaces (gitignored)
  +-- docs/            Documentation
```

## Data Flow

```
Lead Intake (URL/text)
  -> Lead stored in SQLite (LeadStatus=NEW)
  -> Score lead (LeadStatus=SCORED, score/decision/reason_codes set)
  -> Draft proposal (LeadStatus=DRAFTED, ProposalDraft created)
  -> Validate draft (validator_flags set, PASS/WARN/FAIL)
  <!-- -> Human reviews and submits manually -->
  -> Update status (APPLIED_MANUALLY / WON / LOST)
  -> If WON: init client workspace (ClientProject created)
  <!-- -> Package delivery (DRAFT delivery message for human) -->
  -> Record outcome (Outcome created)
  -> Weekly report (aggregated metrics)
```

## Data Models

### Lead
Central entity. Tracks a job posting from intake to outcome.
Key fields: status, lead_score, risk_score, decision, reason_codes.

### ProposalDraft
Generated proposal text. Linked to Lead. Validated before use.

### PortfolioItem
Loaded from YAML (not stored in DB). Used for proposal matching and claim validation.

### ClientProject
Created when a Lead is WON. Points to workspace directory.

### Outcome
Records the result of a won/lost opportunity for learning loop.


## File Encoding

All file I/O uses explicit `encoding="utf-8"` for Windows compatibility.

## Stack

- **Python 3.9+**
- **Typer** — CLI framework
- **SQLModel** — ORM (SQLAlchemy + Pydantic)
- **SQLite** — local-first database
- **PyYAML** — portfolio and config files
- **Rich** — terminal output
- **pytest** — test suite
