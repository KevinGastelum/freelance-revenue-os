# Architecture — Freelance Revenue OS

Local-first, human-in-the-loop freelance operating system.
CLI name: `freelance-os`. Package: `freelance_os`. Repo: `freelance-revenue-os`.

---

## Module Map (`src/freelance_os/`)

| Module | Purpose |
|---|---|
| `__init__.py` | Package version |
| `cli.py` | Typer CLI entry point; exposes all `freelance-os` commands |
| `config.py` | Loads `config/settings.toml`; enforces safety policy (raises on any prohibited flag) |
| `db.py` | SQLModel engine factory, session helper, `create_tables()` |
| `models.py` | SQLModel TABLE definitions: `Lead`, `ProposalDraft`, `PortfolioItem`, `ClientProject`, `Outcome` |
| `schemas.py` | Enums: `LeadStatus`, `Decision`, `ClientProjectStatus`, `OutcomeResult`; reason-code constants |

### Planned modules (later phases)

```
ingestion/    — manual URL/text/email/CSV lead intake
scoring/      — lead scorer, risk rules, pricing
proposal/     — draft generator, validator, portfolio matcher, templates
client/       — workspace, scope, milestones, delivery
execution/    — worktree, tmux, QA harness
reports/      — dashboard, outcome report
utils/        — text, dates, file helpers
```

---

## Data Flow

```
User input (URL / text / CSV / email export)
    ↓
ingestion layer  →  Lead record (SQLite)
    ↓
scoring engine   →  lead_score, risk_score, decision, reason_codes
    ↓
proposal module  →  ProposalDraft (DRAFT ONLY — human copies & sends)
    ↓
human approves manually on platform
    ↓
ClientProject created  →  workspace dir + scope/milestone/delivery docs
    ↓
outcome tracking →  Outcome record  →  weekly report
```

---

## Storage

- **Database**: SQLite at `data/freelance_os.sqlite` (configurable via `[paths].database_path`)
- **Config**: `config/settings.toml` (TOML; created from `settings.example.toml` on `init`)
- **Portfolio**: `config/portfolio.yaml` (YAML; user-maintained)
- **Banned phrases**: `config/banned_phrases.yaml` (YAML; used by proposal validator)
- **Client workspaces**: `./client-work/<client-name-project>/` (Markdown-first)

---

## Safety Architecture

`config.py:validate_safety()` is called on every config load.
It raises `SafetyConfigError` immediately if any prohibited automation flag is `true`.
The CLI exits with code 1 and prints a clear error message.

See `docs/SAFETY_POLICY.md` for the full policy.

---

## Stack

- Python >=3.11
- [Typer](https://typer.tiangolo.com/) — CLI framework
- [SQLModel](https://sqlmodel.tiangolo.com/) — ORM over SQLAlchemy + SQLite
- [PyYAML](https://pyyaml.org/) — YAML config files
- `tomllib` (stdlib, Python 3.11+) — TOML config loading
- pytest — test suite
