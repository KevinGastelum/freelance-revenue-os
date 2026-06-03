"""Agent instruction file generation (PRD 15.2)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from freelance_os.models import ClientProject


def generate_agent_files(project: "ClientProject", workspace_path: Path) -> dict[str, Path]:
    agent_dir = workspace_path / ".agent"
    agent_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "orchestrator": _write_orchestrator(agent_dir, project),
        "coder": _write_coder(agent_dir, project),
        "qa": _write_qa(agent_dir, project),
        "docs": _write_docs(agent_dir, project),
    }
    return files


def _write_orchestrator(agent_dir: Path, project: "ClientProject") -> Path:
    path = agent_dir / "orchestrator.md"
    content = f"""# Orchestrator Agent Instructions

## Project Summary

**Client:** {project.client_name}
**Project:** {project.project_name}
**Platform:** {project.platform or 'N/A'}

## Scope

Review `../00_contract/scope.md` for full scope and acceptance criteria.

## Current Task

Coordinate coder, QA, and docs agents. Track progress against milestones.

## Acceptance Criteria

See `../00_contract/scope.md`.

## Forbidden Changes

- Do NOT submit anything to the client platform automatically.
- Do NOT push to remote without explicit human approval.
- Do NOT modify scope without human review.

## Handoff Format

When done: update `../02_delivery/handoff.md` and notify human for delivery.
"""
    path.write_text(content)
    return path


def _write_coder(agent_dir: Path, project: "ClientProject") -> Path:
    path = agent_dir / "coder.md"
    content = f"""# Coder Agent Instructions

## Project: {project.project_name}

## Scope

See `../00_contract/scope.md` for deliverables and acceptance criteria.

## Current Task

Implement the features described in the scope. Commit incrementally.

## Branch

Branch: `{project.branch_name or 'client/<platform>-<slug>'}`

## Forbidden Changes

- No changes outside the agreed scope without human approval.
- No auto-push.
- No auto-submit.

## Handoff Format

When implementation is complete, update `../02_delivery/changelog.md` and notify QA.
"""
    path.write_text(content)
    return path


def _write_qa(agent_dir: Path, project: "ClientProject") -> Path:
    path = agent_dir / "qa.md"
    content = f"""# QA Agent Instructions

## Project: {project.project_name}

## Scope

Validate against acceptance criteria in `../00_contract/scope.md`.

## Current Task

Run the QA checklist in `../01_workspace/qa_checklist.md`.

## Acceptance Criteria

All items in the QA checklist must be checked before delivery.

## Forbidden Changes

- Do not bypass failing tests.
- Do not mark QA as passed if issues remain unresolved.

## Handoff Format

Update `../02_delivery/qa_report.md` when QA is complete.
"""
    path.write_text(content)
    return path


def _write_docs(agent_dir: Path, project: "ClientProject") -> Path:
    path = agent_dir / "docs.md"
    content = f"""# Docs & Delivery Agent Instructions

## Project: {project.project_name}

## Scope

Prepare delivery documentation.

## Current Task

- Update `../02_delivery/changelog.md`
- Update `../02_delivery/handoff.md`
- Update `../02_delivery/install.md`
- Draft `../02_delivery/delivery_message_draft.md`

## IMPORTANT

The delivery message is DRAFT ONLY. The human must review and send it manually.
Do not send messages automatically.

## Handoff Format

All delivery files complete → notify orchestrator → human performs final review.
"""
    path.write_text(content)
    return path
