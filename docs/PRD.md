# PRD: Freelance Revenue OS | Jun 2, 2026 115pm Tuesday

> **Repo note:** The canonical repository for this project is `freelance-revenue-os`.
The PRD below refers to the project/CLI as `freelance-os` (the original internal name).
Treat `freelance-os` as the CLI/package name unless a rename is explicitly decided.
>

## 0. Mission

Build a local-first, human-in-the-loop freelance operating system that helps the user find, evaluate, draft, execute, package, and deliver freelance work across platforms such as Upwork, Fiverr, Contra, LinkedIn, Arc, Toptal, and direct client channels.

<!--
The system must **reduce manual workload without risking platform bans**. It must not perform stealth scraping, CAPTCHA bypassing, proxy evasion, automated proposal submission, automated messaging, or any trust-sensitive account action.

The core philosophy:

> AI prepares. Human commits.
>

The AI may ingest permitted signals, summarize opportunities, score leads, draft proposals, prepare project workspaces, assist with execution, run QA, package deliverables, and draft client communications. The human manually reviews and performs all platform write actions.
-->

---

# 1. Product Name

**Freelance Revenue OS**

Alternative internal names:

- `freelance-os`
- `clientflow`
- `revops-agent`
- `proposal-harness`
- `freelance-copilot`

Use `freelance-os` as the initial repository/project name unless a better existing project name is already present.

---

<!--# 2. Non-Negotiable Safety and Compliance Rules

## 2.1 Prohibited Automation

Do **not** build or add support for:

- Stealth browser automation
- Residential proxy rotation
- CAPTCHA solving or CAPTCHA bypassing
- Browser fingerprint spoofing
- Automated login to freelance platforms
- Automated authenticated scraping
- Automated proposal submission
- Automated platform messaging
- Automated order delivery
- Automated milestone/payment actions
- Any feature designed to bypass anti-bot systems
- Any feature that simulates human browsing, typing cadence, mouse movement, or session behavior to evade detection
-->

## 2.2 Allowed Automation

The system may support:

- Manual URL intake
- Email alert parsing
- API integration 
- User-exported CSV/JSON imports
- Public RSS/API ingestion where permitted
- Lead scoring
- Lead deduplication
- Proposal drafting
- Portfolio matching
- Risk detection
- Manual approval queues
- Local client workspace creation
- Git worktree setup
- Status update drafting
- Delivery package generation
- README/changelog generation
- QA checklist generation
- Reminder/task generation

<!--
## 2.3 Human Approval Rule

All platform write actions must be manual.

The system may generate text and show it to the user, but the user must copy, edit, and submit manually.

Manual actions include:

- Submit proposal
- Send message
- Accept contract
- Decline invitation
- Deliver order
- Request milestone release
- Send invoice
- Move communication off-platform
- Modify platform account settings
-->

---

# 3. Problem Statement

Freelancing platforms produce too much noise. The user needs a system that can:

1. Collect opportunities safely.
2. Filter out low-quality, scammy, low-margin, or high-risk leads.
3. Draft highly tailored proposals quickly.
4. Reuse real portfolio/project context without hallucinating claims.
5. Track opportunities and active clients.
6. Spin up local execution workspaces once work is secured.
7. Help package and deliver professional client handoffs.
8. Improve over time by tracking win/loss outcomes.

The user already works with AI coding tools, tmux, git worktrees, Claude Code, Codex CLI, and local terminal workflows. This project should integrate with that style instead of becoming a bloated SaaS clone.

---

# 4. Target User

Primary user:

- Independent developer/data analyst/AI workflow builder.
- Uses Linux, tmux, Neovim, Claude Code, Codex CLI, Git, and local-first workflows.
- Wants to monetize skills through freelance projects.
- Wants more automation but does not want account bans or platform violations.
- Prefers terminal/TUI/local dashboards over heavy web apps when possible.

---

# 5. Product Goals

## 5.1 MVP Goals

The MVP should allow the user to:

1. Add a lead manually by URL or pasted job description.
2. Import leads from email alerts.
3. Store leads in a local database.
4. Score leads using configurable rules.
5. Generate a proposal draft.
6. Validate the proposal against user portfolio and banned phrases.
7. Mark lead status manually.
8. Convert an accepted lead into a client project workspace.
9. Generate scope, milestone, README, changelog, and delivery templates.
10. Track outcomes for feedback loops.

## 5.2 Long-Term Goals

Eventually support:

- Official Upwork API adapter if approved.
- Gmail/IMAP ingestion for job alerts.
- Fiverr inbox/manual export support.
- Contra/direct lead tracking.
- LinkedIn manual CRM pipeline.
- Portfolio memory layer.
- Proposal A/B tracking.
- Win/loss analytics.
- Pricing recommendation engine.
- Multi-agent execution harness integration.
- Tmux session generation for active contracts.
- GitHub repo/worktree automation.
- Local dashboard or TUI.

---

<!--# 6. Out of Scope for MVP

Do not implement in MVP:

- Browser automation
- Platform login automation
- Proposal auto-submit
- DM auto-send
- Payment automation
- Web scraping of authenticated dashboards
- Large multi-user SaaS auth system
- Complex CRM pipeline
- Full web dashboard unless simple CLI/TUI is already done
- AI agent autonomy beyond local drafting and project preparation
-->
---

# 7. Core Architecture

The system should be local-first and modular.

Recommended stack:

- Language: Python
- CLI: Typer or Click
- Database: SQLite for MVP
- ORM: SQLModel or SQLAlchemy
- Config: TOML or YAML
- Optional TUI: Textual
- Optional API: FastAPI later
- LLM calls: provider-agnostic interface
- File outputs: Markdown-first
- Git integration: shell commands with safe dry-run mode

Initial structure:

```
freelance-os/
  README.md
  pyproject.toml
  .env.example
  config/
    settings.example.toml
    scoring_rules.example.toml
    portfolio.example.yaml
    banned_phrases.yaml
  data/
    freelance_os.sqlite
  docs/
    PRD.md
    ARCHITECTURE.md
    SAFETY_POLICY.md
    OPERATOR_MANUAL.md
  src/
    freelance_os/
      __init__.py
      cli.py
      config.py
      db.py
      models.py
      schemas.py

      ingestion/
        __init__.py
        manual.py
        email_parser.py
        import_csv.py

      scoring/
        __init__.py
        lead_scorer.py
        risk_rules.py
        pricing.py

      proposal/
        __init__.py
        draft_generator.py
        proposal_validator.py
        portfolio_matcher.py
        templates.py

      client/
        __init__.py
        workspace.py
        scope.py
        milestones.py
        delivery.py

      execution/
        __init__.py
        worktree.py
        tmux.py
        qa.py

      reports/
        __init__.py
        dashboard.py
        outcome_report.py

      utils/
        __init__.py
        text.py
        dates.py
        files.py
  tests/
    test_lead_scoring.py
    test_proposal_validator.py
    test_workspace_creation.py
```

---

# 8. Data Model

## 8.1 Lead

Fields:

- `id`
- `source`
- `source_url`
- `title`
- `description`
- `client_name`
- `client_rating`
- `client_payment_verified`
- `budget_type`
- `budget_min`
- `budget_max`
- `hourly_min`
- `hourly_max`
- `country`
- `posted_at`
- `imported_at`
- `status`
- `lead_score`
- `risk_score`
- `decision`
- `reason_codes`
- `raw_payload`
- `notes`

Valid statuses:

- `NEW`
- `SCORED`
- `DRAFTED`
- `APPROVED_TO_APPLY`
- `APPLIED_MANUALLY`
- `INTERVIEW`
- `WON`
- `LOST`
- `REJECTED`
- `ARCHIVED`

Valid decisions:

- `DRAFT_NOW`
- `WATCH`
- `MAYBE`
- `REJECT`

## 8.2 ProposalDraft

Fields:

- `id`
- `lead_id`
- `version`
- `draft_text`
- `technical_diagnosis`
- `portfolio_matches`
- `clarifying_questions`
- `price_recommendation`
- `validator_flags`
- `created_at`
- `approved_by_user`

## 8.3 PortfolioItem

Fields:

- `id`
- `name`
- `type`
- `description`
- `tech_stack`
- `proof_points`
- `links`
- `allowed_claims`
- `forbidden_claims`
- `tags`

## 8.4 ClientProject

Fields:

- `id`
- `lead_id`
- `client_name`
- `project_name`
- `platform`
- `contract_url`
- `status`
- `start_date`
- `deadline`
- `scope_path`
- `workspace_path`
- `repo_url`
- `branch_name`
- `delivery_path`

Valid statuses:

- `INTAKE`
- `ACTIVE`
- `WAITING_ON_CLIENT`
- `READY_FOR_DELIVERY`
- `DELIVERED`
- `REVISION`
- `COMPLETE`
- `CANCELLED`

## 8.5 Outcome

Fields:

- `id`
- `lead_id`
- `result`
- `reason`
- `final_rate`
- `final_budget`
- `time_spent_hours`
- `profit_estimate`
- `lessons`
- `created_at`

---

# 9. Lead Ingestion

## 9.1 Manual URL Intake

Command:

```bash
freelance-os lead add-url "https://example.com/job/123"
```

Behavior:

- Store URL.
- Ask user to paste job description if no official parser exists.
- Create `Lead` record.
- Mark source as `manual_url`.

## 9.2 Manual Text Intake

Command:

```bash
freelance-os lead add-text --source upwork
```

Behavior:

- User pastes job post text into editor or stdin.
- System extracts title, budget, client data if present.
- Creates lead.

## 9.3 Email Alert Intake

Command:

```bash
freelance-os lead ingest-email --source upwork --input ./alerts.mbox
```

MVP may parse exported `.eml`, `.mbox`, or pasted email text.

Later integration may support Gmail API after explicit user authorization.

## 9.4 CSV/JSON Import

Command:

```bash
freelance-os lead import-csv ./leads.csv
freelance-os lead import-json ./leads.json
```

---

# 10. Lead Scoring

## 10.1 Base Scoring Formula

Lead score is 0–100.

Recommended default:

```
20% technical fit
15% budget fit
15% client quality
10% clarity of scope
10% urgency/timing
10% portfolio match
10% repeat-work potential
10% communication quality
minus risk penalties
```

## 10.2 Risk Penalties

Default penalties:

```
-25: unpaid test request
-25: asks to bypass platform payment rules
-20: vague fixed-price project with low budget
-20: unrealistic deadline
-15: suspicious payment/client behavior
-15: many negative reviews mentioning scope creep
-10: "simple/easy/quick" language for complex work
-10: unclear deliverables
-10: requires unsupported tech stack
-10: client asks for free consultation before contract
```

## 10.3 Decision Thresholds

```
80–100: DRAFT_NOW
65–79: WATCH
50–64: MAYBE
0–49: REJECT
```

## 10.4 Reason Codes

Each score must include reason codes.

Examples:

```
TECH_STACK_MATCH
HIGH_BUDGET_FIT
CLEAR_SCOPE
STRONG_PORTFOLIO_MATCH
LOW_BUDGET
SCOPE_CREEP_RISK
UNREALISTIC_DEADLINE
UNSUPPORTED_STACK
PAYMENT_RISK
```

---

# 11. Proposal Drafting

## 11.1 Proposal Structure

Each proposal must include:

1. One-line recognition of the actual problem.
2. Three-bullet technical solution.
3. One relevant proof point from portfolio.
4. One clarifying question.
5. Simple CTA.

Template:

```
I’d approach this as a [core bottleneck] problem, not just a [surface task] task.

Here’s how I’d handle it:
- [Technical step 1]
- [Technical step 2]
- [Technical step 3]

Relevant background: I’ve built [real project / stack match], including [specific proof].

One question before estimating precisely: [scope-locking question]

If useful, I can start by mapping the current flow and giving you a short implementation plan before touching the codebase.
```

## 11.2 Banned Phrases

Default banned phrases:

```
I hope this message finds you well
I am the perfect candidate
I am the ideal candidate
I have extensive experience
I can do this easily
Dear hiring manager
Kindly
Let's connect outside Upwork
Let's connect outside Fiverr
```

## 11.3 Proposal Validator

Before marking a draft ready, validate:

- No banned phrases.
- No unsupported claims.
- No fake portfolio references.
- No off-platform communication suggestion.
- No guaranteed timeline without scope.
- No guaranteed outcome.
- No excessive generic filler.
- Includes at least one clarifying question.
- Includes technical diagnosis.
- Includes direct relevance to job description.

Output:

```
PASS
WARN
FAIL
```

With reasons.

---

# 12. Pricing Recommendation

MVP pricing module should estimate:

- Minimum acceptable hourly rate.
- Estimated hours.
- Risk multiplier.
- Platform fee adjustment.
- Rush fee adjustment.
- Fixed-price quote range.

Formula example:

```
base_estimate = estimated_hours * target_hourly_rate
risk_adjusted = base_estimate * risk_multiplier
rush_adjusted = risk_adjusted * rush_multiplier
recommended_quote = rush_adjusted + platform_fee_buffer
```

Configurable values:

```toml
target_hourly_rate = 75
minimum_project_value = 300
risk_multiplier_low = 1.0
risk_multiplier_medium = 1.25
risk_multiplier_high = 1.5
rush_multiplier = 1.25
```

---

# 13. Human Approval Console

MVP can be CLI-based.

Command:

```bash
freelance-os lead review
```

Display:

```
Lead #42
Source: Upwork
Title: Build Next.js dashboard with Supabase
Score: 86
Decision: DRAFT_NOW

Why:
- TECH_STACK_MATCH
- CLEAR_SCOPE
- STRONG_PORTFOLIO_MATCH
- BUDGET_FIT

Risks:
- Deadline unclear

Recommended action:
- Review proposal draft manually.
- Ask one scope-locking question before final pricing.

Options:
[a] approve to apply manually
[e] edit draft
[r] reject
[w] watch
[o] open source URL
[q] quit
```

No platform actions should be automated.

---

# 14. Client Project Workspace

When a lead is won:

```bash
freelance-os client init --lead 42
```

Create:

```
client-work/
  client-name-project-name/
    00_contract/
      brief.md
      scope.md
      milestones.md
      platform_messages.md
      risk_log.md

    01_workspace/
      README.md

    02_delivery/
      changelog.md
      handoff.md
      install.md
      screenshots/

    03_admin/
      invoice_notes.md
      followups.md
      outcome.md
```

If a Git repo exists:

```bash
freelance-os client init --lead 42 --repo git@github.com:client/project.git
```

Expected behavior:

- Clone or create worktree.
- Create branch.
- Generate scope docs.
- Generate task checklist.
- Generate delivery checklist.
- Do not push changes unless user explicitly runs a command.

---

# 15. Execution Harness Integration

This system should integrate with the user’s existing Claude Code / Codex / tmux workflow.

## 15.1 Tmux Session Generation

Command:

```bash
freelance-os client tmux --project client-name-project-name
```

Create session layout:

```
Window 0: orchestrator
Window 1: coder
Window 2: qa
Window 3: docs-delivery
Window 4: git/logs
```

The command may generate a shell script first instead of directly launching tmux.

Example output:

```bash
./scripts/start_client_session.sh client-name-project-name
```

## 15.2 Agent Instructions

Generate local instruction files:

```
.agent/
  orchestrator.md
  coder.md
  qa.md
  docs.md
```

Each file should include:

- Project summary
- Scope
- Acceptance criteria
- Forbidden changes
- Current task
- Handoff format

## 15.3 Worktree Rules

Branch naming:

```
client/<platform>-<client>-<task-slug>
```

Example:

```
client/upwork-acme-dashboard-auth-fix
```

---

# 16. Delivery Package

Command:

```bash
freelance-os client package --project client-name-project-name
```

Generate:

```
02_delivery/
  changelog.md
  handoff.md
  install.md
  qa_report.md
  delivery_message_draft.md
```

<!--
Delivery message draft must be clearly marked:

```
DRAFT ONLY — USER MUST REVIEW AND SEND MANUALLY
```
-->

Delivery package should include:

- Summary of completed work.
- Files changed.
- How to run/test.
- Known limitations.
- Suggested next steps.
- Polite review/revision note.
- No off-platform payment suggestion.

---

# 17. Reports and Learning Loop

Track outcomes:

```bash
freelance-os outcome add --lead 42
```

Fields:

- Applied manually?
- Interview received?
- Won/lost?
- Reason lost?
- Final price?
- Estimated hours?
- Actual hours?
- Client quality?
- Lessons learned?

Generate report:

```bash
freelance-os report weekly
```

Report should include:

- Leads imported.
- Leads rejected.
- Proposals drafted.
- Proposals manually submitted.
- Interviews.
- Won contracts.
- Lost opportunities.
- Estimated revenue.
- Actual revenue.
- Best-performing proposal patterns.
- Common rejection reasons.

---

# 18. Configuration

## 18.1 `settings.toml`

```toml
[user]
name = "Kevin Alexis"
default_timezone = "America/Mazatlan"
target_hourly_rate = 75
minimum_project_value = 300

[paths]
client_work_dir = "./client-work"
portfolio_file = "./config/portfolio.yaml"
database_path = "./data/freelance_os.sqlite"

<!--
[safety]
allow_browser_automation = false
allow_auto_submit = false
allow_auto_message = false
allow_scraping = false
require_human_approval = true
-->
```

## 18.2 `portfolio.yaml`

```yaml
items:
-name:"Next.js + Supabase Platform"
type:"web_app"
tags:["nextjs","supabase","prisma","postgres","auth","dashboard"]
description:"Built full-stack web applications using Next.js, Prisma, and Supabase."
proof_points:
-"Implemented database-backed ticketing/payment-style workflows."
-"Worked with Prisma schema design and Supabase Postgres."
-"Deployed Next.js apps to Vercel."
allowed_claims:
-"I have built Next.js/Supabase applications."
-"I can work with Prisma and Postgres-backed workflows."
forbidden_claims:
-"I have scaled this to millions of users."
-"I am an official Supabase partner."

-name:"Power BI / Data Analytics Background"
type:"data_analytics"
tags:["powerbi","dax","sql","dashboards","kpi","analytics"]
description:"Data analytics and dashboarding experience across business reporting workflows."
proof_points:
-"Built KPI reporting workflows."
-"Worked with DAX and Power BI measures."
-"Handled reporting for business stakeholders."
```

---

# 19. CLI Command Specification

Required MVP commands:

```bash
freelance-os init
freelance-os lead add-url URL
freelance-os lead add-text --source SOURCE
freelance-os lead list
freelance-os lead show LEAD_ID
freelance-os lead score LEAD_ID
freelance-os lead score --all-new
freelance-os lead draft LEAD_ID
freelance-os lead validate-draft LEAD_ID
freelance-os lead review
freelance-os lead status LEAD_ID STATUS

freelance-os client init --lead LEAD_ID
freelance-os client list
freelance-os client show CLIENT_ID
freelance-os client package --project PROJECT_NAME

freelance-os outcome add --lead LEAD_ID
freelance-os report weekly
```

Nice-to-have commands:

```bash
freelance-os lead import-csv PATH
freelance-os lead import-json PATH
freelance-os lead ingest-email --input PATH
freelance-os client tmux --project PROJECT_NAME
freelance-os client worktree --project PROJECT_NAME --repo REPO_URL
```

---

# 20. Acceptance Criteria

## 20.1 MVP Acceptance

The project is acceptable when:

1. User can initialize the local project.
2. SQLite database is created.
3. User can manually add a lead.
4. User can score a lead.
5. Score includes reason codes.
6. User can generate a proposal draft.
7. Proposal validator catches banned phrases.
8. Proposal validator warns on unsupported claims.
9. User can mark lead status manually.
10. User can convert a won lead into a client workspace.
11. Client workspace generates contract, scope, milestone, delivery, and admin markdown files.
12. User can generate a delivery package draft.
<!--
13. No platform write action is automated.
14. Safety policy exists in docs and is enforced in config.
-->
15. Tests exist for scoring, proposal validation, and workspace generation.

<!--
## 20.2 Safety Acceptance

The build fails or tests fail if:

- `allow_auto_submit` defaults to true.
- `allow_browser_automation` defaults to true.
- Code contains stealth/proxy/CAPTCHA bypass modules.
- Any command claims to submit proposals automatically.
- Any delivery command sends messages automatically.
- Proposal drafts include banned off-platform communication language.
-->

---

# 21. Testing Plan

Implement tests for:

## 21.1 Lead Scoring

- High-quality lead gets high score.
- Low-budget vague lead gets rejected.
- Unsupported tech stack reduces score.
- Unpaid test request triggers severe penalty.
- Score always includes reason codes.

## 21.2 Proposal Validation

- Banned phrases are detected.
- Unsupported portfolio claims are detected.
- Missing clarifying question produces warning.
- Off-platform communication phrase fails.
- Draft with technical diagnosis passes.

## 21.3 Workspace Creation

- Client directory is created.
- Required subdirectories are created.
- Required markdown files are created.
- Existing project names do not overwrite without confirmation.
- Branch names are sanitized.

<!--
## 21.4 Safety

- Config defaults are safe.
- No automated platform-action command exists.
- Delivery messages are generated as drafts only.
-->

---

# 22. Implementation Plan for Claude Code

## Phase 1: Project Skeleton

Tasks:

1. Create repository structure.
2. Add `pyproject.toml`.
3. Add Typer CLI.
4. Add SQLite database setup.
5. Add models.
6. Add config loader.
7. Add safety policy docs.

Deliverables:

- Working `freelance-os init`.
- Empty database can be created.
- Tests run.

## Phase 2: Lead Management

Tasks:

1. Implement manual URL intake.
2. Implement manual text intake.
3. Implement lead list/show/status commands.
4. Add basic parsing helpers.
5. Add tests.

Deliverables:

- User can add and view leads.

## Phase 3: Scoring Engine

Tasks:

1. Implement scoring config.
2. Implement risk rules.
3. Implement decision thresholds.
4. Add reason codes.
5. Add tests.

Deliverables:

- User can score leads and understand why.

## Phase 4: Proposal Drafting

Tasks:

1. Add proposal template engine.
2. Add portfolio matcher.
3. Add proposal validator.
4. Add banned phrase checks.
5. Add unsupported claim checks.
6. Add tests.

Deliverables:

- User can generate safe proposal drafts.

## Phase 5: Client Workspace

Tasks:

1. Convert won lead to client project.
2. Generate workspace directory.
3. Generate scope/milestone/delivery/admin files.
4. Add package command.
5. Add tests.

Deliverables:

- User can initialize client project and create delivery package.

## Phase 6: Execution Harness Integration

Tasks:

1. Generate agent instruction files.
2. Generate tmux session script.
3. Add git branch/worktree helper.
4. Add dry-run mode.
5. Add docs.

Deliverables:

- User can launch a structured local execution workflow.

## Phase 7: Reporting and Feedback Loop

Tasks:

1. Add outcome tracking.
2. Add weekly report.
3. Track win/loss stats.
4. Track proposal conversion.
5. Add markdown export.

Deliverables:

- User can learn what works and refine strategy.

---

# 23. Claude Code Operating Instructions

When implementing this project:

<!--
1. Do not build stealth automation.
2. Do not add browser automation.
3. Do not add platform auto-submit.
-->
4. Prefer simple, local-first implementation.
5. Write tests before or alongside core logic.
6. Keep modules small and composable.
7. Use Markdown outputs liberally.
<!--
8. Make every risky action explicit and manual.
-->
9. Default to dry-run for filesystem/git operations.
10. Add clear operator docs.

Do not overbuild a SaaS app. Build a practical local command-line operating system first.

---

# 24. Definition of Done

The MVP is done when the user can run:

```bash
freelance-os init
freelance-os lead add-text --source upwork
freelance-os lead score --all-new
freelance-os lead draft 1
freelance-os lead review
freelance-os lead status 1 WON
freelance-os client init --lead 1
freelance-os client package --project example-project
freelance-os report weekly
```

And receive:

- A scored lead.
- A proposal draft.
- A proposal validation report.
- A client workspace.
- A delivery package.
- A weekly performance report.

<!--
All without any automated platform submission, browser automation, or anti-bot evasion.
-->
