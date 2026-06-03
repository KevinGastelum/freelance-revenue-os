"""Tmux session script generator per PRD section 15.1.

Generates a shell script that the user runs manually — never auto-launches tmux.
"""

from pathlib import Path
import re


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text)[:40]


def generate_tmux_script(project_name: str, cfg: dict) -> str:
    """Generate a tmux session launch script and return its path."""
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)

    session_name = _slugify(project_name)
    script_path = scripts_dir / f"start_client_session.sh"

    base_dir = cfg["paths"].get("client_work_dir", "./client-work")
    workspace_path = f"{base_dir}/{project_name}"

    script_content = f"""\
#!/usr/bin/env bash
# Auto-generated tmux session script for: {project_name}
# Run manually: bash {script_path}
# NEVER auto-execute this from the application.
set -euo pipefail

SESSION="{session_name}"
WORKSPACE="{workspace_path}"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session '$SESSION' already exists. Attaching..."
    tmux attach-session -t "$SESSION"
    exit 0
fi

tmux new-session -d -s "$SESSION" -n orchestrator -c "$WORKSPACE"
tmux new-window -t "$SESSION" -n coder -c "$WORKSPACE/01_workspace"
tmux new-window -t "$SESSION" -n qa -c "$WORKSPACE"
tmux new-window -t "$SESSION" -n docs-delivery -c "$WORKSPACE/02_delivery"
tmux new-window -t "$SESSION" -n git-logs -c "$WORKSPACE"

# Select first window
tmux select-window -t "$SESSION:0"

echo "Session '$SESSION' created."
echo "Attach with: tmux attach-session -t $SESSION"
# tmux attach-session -t "$SESSION"  # Uncomment to auto-attach
"""

    script_path.write_text(script_content, encoding="utf-8")
    script_path.chmod(0o755)

    # Also generate .agent/ instruction files
    _generate_agent_files(project_name, cfg)

    return str(script_path)


def _generate_agent_files(project_name: str, cfg: dict) -> None:
    """Generate .agent/ instruction files per PRD section 15.2."""
    agent_dir = Path(".agent")
    agent_dir.mkdir(exist_ok=True)

    base_dir = cfg["paths"].get("client_work_dir", "./client-work")
    workspace_path = f"{base_dir}/{project_name}"

    agents = {
        "orchestrator.md": _orchestrator_md(project_name, workspace_path),
        "coder.md": _coder_md(project_name, workspace_path),
        "qa.md": _qa_md(project_name, workspace_path),
        "docs.md": _docs_md(project_name, workspace_path),
    }

    for filename, content in agents.items():
        (agent_dir / filename).write_text(content, encoding="utf-8")


def _orchestrator_md(project_name: str, workspace_path: str) -> str:
    return f"""\
# Orchestrator Agent Instructions

**Project:** {project_name}
**Workspace:** {workspace_path}

## Role

You coordinate the overall project flow, track progress, and delegate tasks.

## Scope

- Keep track of milestone status.
- Delegate implementation tasks to the coder agent.
- Delegate testing tasks to the QA agent.
- Delegate documentation to the docs agent.

## Acceptance Criteria

- All milestones in `00_contract/milestones.md` marked complete.
- Delivery package in `02_delivery/` is ready for human review.

## Forbidden Changes

- Do not submit anything to the client platform.
- Do not send messages on the platform.
- Do not modify contract terms without human review.

## Current Task

Review scope and assign first milestone tasks.

## Handoff Format

When a task is complete, update milestones.md and notify the human for review.
"""


def _coder_md(project_name: str, workspace_path: str) -> str:
    return f"""\
# Coder Agent Instructions

**Project:** {project_name}
**Workspace:** {workspace_path}/01_workspace

## Role

Implement the features described in scope.md.

## Scope

See `{workspace_path}/00_contract/scope.md` for in-scope items.

## Acceptance Criteria

- All in-scope features implemented.
- Code passes QA review.
- No regressions.

## Forbidden Changes

- Do not modify files outside `01_workspace/`.
- Do not push to remote without orchestrator approval.
- Do not communicate with the client.

## Current Task

Review scope.md and implement milestone 1 deliverables.

## Handoff Format

When ready for review, notify orchestrator with a summary of changes.
"""


def _qa_md(project_name: str, workspace_path: str) -> str:
    return f"""\
# QA Agent Instructions

**Project:** {project_name}
**Workspace:** {workspace_path}

## Role

Test the implementation and document results in qa_report.md.

## Scope

- Test all acceptance criteria in scope.md.
- Test edge cases and error paths.
- Document results in `02_delivery/qa_report.md`.

## Forbidden Changes

- Do not modify production code.
- Do not submit test results to the client directly.

## Current Task

Review scope.md acceptance criteria and write test plan.

## Handoff Format

Complete `02_delivery/qa_report.md` and notify orchestrator.
"""


def _docs_md(project_name: str, workspace_path: str) -> str:
    return f"""\
# Docs Agent Instructions

**Project:** {project_name}
**Workspace:** {workspace_path}

## Role

Maintain documentation and prepare the delivery package.

## Scope

- Keep `02_delivery/changelog.md` up to date.
- Prepare `02_delivery/handoff.md` for client delivery.
- Prepare `02_delivery/install.md`.
- Prepare `02_delivery/delivery_message_draft.md` (DRAFT ONLY).

## Forbidden Changes

- Do not send the delivery message automatically.
- The delivery message is a DRAFT — the human sends it manually.

## Current Task

Draft initial changelog and handoff notes based on scope.md.

## Handoff Format

When delivery package is ready, notify orchestrator for human review.
"""
