# Freelance Revenue OS 🧠💼

[![Tests](https://img.shields.io/badge/tests-455%20passed-success?style=flat-square)](tests)
[![Orchestration Swarm](https://img.shields.io/badge/swarm-parallel%20agents%20active-blueviolet?style=flat-square)](docs/HANDOFF.md)
[![Safety Philosophy](https://img.shields.io/badge/safety-AI%20Prepares%2C%20Human%20Commits-red?style=flat-square)](docs/SAFETY_POLICY.md)
[![Platform Compatibility](https://img.shields.io/badge/cross--platform-Windows%20%7C%20Linux%20Sandbox-blue?style=flat-square)](docs/ARCHITECTURE.md)

Freelance Revenue OS (`freelance-os`) is a local-first CLI pipeline that surfaces high-margin gigs, matches them against real portfolio claims, generates customized proposals, and sets up isolated project workspaces.

More importantly, **this codebase is a case study in modern Agentic Engineering.** It was built using a spec-first approach, orchestrated across a team of sandboxed AI coding agents working in parallel, and guarded by an automated cross-platform verification pipeline.

---

## 🛠️ The Agentic Workflow (How This Was Built)

Instead of writing code line-by-line, the human operator acts as a **Systems Architect & Swarm Director**. The entire codebase was built, tuned, and verified by coordinating a team of sandboxed agents using the **Warren Control Plane**.

```
                           ┌────────────────────────┐
                           │   Human Operator       │
                           │  (Specs & Contracts)   │
                           └───────────┬────────────┘
                                       │
                ┌──────────────────────┼──────────────────────┐
                │ Dispatches Parallel  │ Runs in Sandbox      │
                ▼                      ▼                      ▼
      ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
      │   Agent: Kay     │   │  Agent: K-Bot    │   │ Agent: lucratitan│
      │   (CLI Core)     │   │ (Scoring/Tuner)  │   │  (QA/Workspace)  │
      └─────────┬────────┘   └─────────┬────────┘   └─────────┬────────┘
                │                      │                      │
                └──────────────────────┼──────────────────────┘
                                       │ (Pushes Branches)
                                       ▼
                           ┌────────────────────────┐
                           │   Verifier Agent       │
                           │  (Tests & Path-Guards) │
                           └───────────┬────────────┘
                                       │ (Auto-Merges if Green)
                                       ▼
                           ┌────────────────────────┐
                           │   Production main      │
                           │  (455+ Tests Green)    │
                           └────────────────────────┘
```

### 1. Spec-First Decomposition
Before a single line of code was written, the architecture was split into modular, isolated components ([docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)). Because each system module—`ingestion`, `scoring`, `proposal`, `client`, and `execution`—was decoupled, multiple development tasks could be delegated to separate agents at the same time.

### 2. Parallel Agent Dispatches
Using ASCII specifications and prompt templates, the operator dispatched concurrent runs (`run_cx9j5xyq4xf7`, `run_y906vw15k652`, etc.) in isolated Linux sandboxes:
- **Agent 1 (Kay / K-Bot-T1)** built out the core Typer CLI and database models.
- **Agent 2 (K-Bot-T2 & T3)** tuned the margin-scoring equations and implemented annual-to-hourly salary normalizations.
- **Agent 3 (lucratitan)** engineered the local workspace and `tmux` generation scripts.

### 3. Automated Verification Gates
To maintain a high-velocity development workflow, a **Verifier Agent** managed the integration queue:
- **Sandbox Checks:** When an agent pushed a branch, the Verifier spun up a clean environment to run the test suite (`uv run pytest -q`).
- **Cross-Platform Enforcement:** The Verifier ensured compatibility between the Windows host (default encoding cp1252) and the Linux sandboxes by checking that all file operations enforced `encoding="utf-8"` and utilized `pathlib` for file paths.
- **Path Guards:** If a branch touched deployment configurations, workflows, or credentials, the Verifier automatically bypassed auto-merge and requested manual review.

---

## 💡 System Features & Pipeline

The CLI implements a clean, step-by-step pipeline to take the friction out of freelance project acquisition:

1. **Ingestion (`freelance-os lead import-json`):** Parses gig details from manual URLs, alert emails, RSS feeds, or CSVs, and stores them in a local SQLite database.
2. **Margin Scoring (`freelance-os lead score`):** Evaluates jobs using an AI-leverage formula: $( \text{Budget} \div \text{Effort Hours} ) \times \text{Confidence}$. It automatically applies penalty scores for high-risk postings (such as unpaid test requests) and handles margin caps to ignore unrealistic outliers.
3. **Proposal Drafting (`freelance-os lead draft`):** Generates bespoke, high-quality pitches by pulling verifiable achievements from [portfolio.yaml](config/portfolio.yaml).
4. **Draft Validation (`freelance-os lead validate-draft`):** Runs non-AI heuristic checks to catch generic copy-paste phrases (e.g., *"Dear hiring manager"*) and verifies that a scope-locking clarifying question is present.
5. **Workspace Bootstrapping (`freelance-os client init`):** Automates the creation of local directories, sets up client-specific Git worktrees, and generates a launcher script for a multi-window `tmux` session tailored for task execution.

---

## 🛡️ "AI Prepares, Human Commits" (Safety & Compliance)

To eliminate the risk of account bans or platform terms-of-service violations, safety is hardcoded at the core of the Freelance Revenue OS.

- **Refusal to Launch:** The configuration loader ([src/freelance_os/config.py](src/freelance_os/config.py)) raises a fatal error and refuses to start the application if options like browser automation, authenticated scraping, or auto-submission are enabled.
- **Human Review Enforced:** The OS never connects directly to freelance platforms to apply or send messages. It outputs markdown-formatted drafts to the local workspace for the operator to review, polish, and submit manually.

For more details on the safety design, see [docs/SAFETY_POLICY.md](docs/SAFETY_POLICY.md).
