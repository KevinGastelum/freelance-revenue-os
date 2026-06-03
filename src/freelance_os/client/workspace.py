"""Client workspace initialization per PRD section 14."""

import re
from pathlib import Path
from typing import Optional

from sqlmodel import Session

from freelance_os.client import scope, milestones
from freelance_os.db import get_engine
from freelance_os.models import ClientProject, ClientProjectStatus, Lead, LeadStatus


def _slugify(text: str) -> str:
    """Convert text to a safe directory slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:40]


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def init_workspace(
    lead_id: int,
    cfg: dict,
    repo_url: Optional[str] = None,
    force: bool = False,
) -> ClientProject:
    """Create a client project workspace from a WON lead."""
    engine = get_engine(cfg["paths"]["database_path"])

    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        if lead is None:
            raise ValueError(f"Lead #{lead_id} not found")
        if lead.status != LeadStatus.WON:
            raise ValueError(
                f"Lead #{lead_id} is not WON (status={lead.status}). "
                "Use 'lead status {id} WON' first."
            )

        client_name = _slugify(lead.client_name or f"client-{lead_id}")
        project_title = lead.title or f"project-{lead_id}"
        project_slug = _slugify(project_title)
        folder_name = f"{client_name}-{project_slug}"

        base_dir = Path(cfg["paths"].get("client_work_dir", "./client-work"))
        workspace = base_dir / folder_name

        if workspace.exists() and not force:
            raise FileExistsError(
                f"Workspace already exists: {workspace}\n"
                "Use --force to overwrite."
            )

        # Create directory tree per PRD 14
        for subdir in [
            "00_contract",
            "01_workspace",
            "02_delivery/screenshots",
            "03_admin",
        ]:
            (workspace / subdir).mkdir(parents=True, exist_ok=True)

        # Gather lead data for templates
        lead_data = {
            "client_name": lead.client_name or "Unknown Client",
            "project_title": project_title,
            "source": lead.source,
            "source_url": lead.source_url or "",
            "description": lead.description or "",
            "budget_type": lead.budget_type or "fixed",
            "budget_min": lead.budget_min,
            "budget_max": lead.budget_max,
            "folder_name": folder_name,
            "platform": lead.source,
        }

        # 00_contract files
        _write_file(workspace / "00_contract" / "brief.md", scope.brief_template(lead_data))
        _write_file(workspace / "00_contract" / "scope.md", scope.scope_template(lead_data))
        _write_file(workspace / "00_contract" / "milestones.md", milestones.milestones_template(lead_data))
        _write_file(workspace / "00_contract" / "platform_messages.md", _platform_messages_template())
        _write_file(workspace / "00_contract" / "risk_log.md", _risk_log_template())

        # 01_workspace README
        _write_file(workspace / "01_workspace" / "README.md", _workspace_readme_template(lead_data))

        # 02_delivery stubs
        _write_file(workspace / "02_delivery" / "changelog.md", _changelog_template(lead_data))
        _write_file(workspace / "02_delivery" / "handoff.md", _handoff_template(lead_data))
        _write_file(workspace / "02_delivery" / "install.md", _install_template())

        # 03_admin stubs
        _write_file(workspace / "03_admin" / "invoice_notes.md", _invoice_notes_template(lead_data))
        _write_file(workspace / "03_admin" / "followups.md", _followups_template())
        _write_file(workspace / "03_admin" / "outcome.md", _outcome_template())

        # Persist ClientProject record
        project = ClientProject(
            lead_id=lead_id,
            client_name=lead_data["client_name"],
            project_name=project_slug,
            platform=lead.source,
            status=ClientProjectStatus.INTAKE,
            workspace_path=str(workspace),
            repo_url=repo_url,
        )
        session.add(project)
        lead.status = LeadStatus.WON  # ensure status stays WON
        session.add(lead)
        session.commit()
        session.refresh(project)

    return project


# ---- Template helpers -------------------------------------------------------

def _platform_messages_template() -> str:
    return """\
# Platform Messages

> This file is for tracking important messages on the platform.
> Do NOT paste off-platform contact info here.

## Messages Log

| Date | Direction | Summary |
|------|-----------|---------|
|      | Received  |         |

## Notes

- All communication should remain on-platform unless client initiates email.
"""


def _risk_log_template() -> str:
    return """\
# Risk Log

| Date | Risk | Likelihood | Impact | Mitigation |
|------|------|------------|--------|------------|
|      |      | Low/Med/High | Low/Med/High |       |

## Notes

- Review risks at each milestone.
- Escalate scope changes immediately.
"""


def _workspace_readme_template(data: dict) -> str:
    return f"""\
# {data['project_title']}

**Client:** {data['client_name']}
**Platform:** {data['platform']}
**Status:** Active

## Overview

{data['description'][:500] if data['description'] else 'See 00_contract/brief.md for details.'}

## Quick Start

1. Review scope in `00_contract/scope.md`
2. Check milestones in `00_contract/milestones.md`
3. Work in this `01_workspace/` directory
4. Deliver via `02_delivery/`

## Key Files

- `00_contract/brief.md` - Project brief
- `00_contract/scope.md` - Scope of work
- `00_contract/milestones.md` - Milestones and timeline
- `02_delivery/handoff.md` - Delivery handoff notes
"""


def _changelog_template(data: dict) -> str:
    return f"""\
# Changelog — {data['project_title']}

All notable changes to this project will be documented here.

## [Unreleased]

### Added
- (Initial setup)

## Notes

- Keep entries concise and client-readable.
"""


def _handoff_template(data: dict) -> str:
    return f"""\
# Delivery Handoff — {data['project_title']}

**Client:** {data['client_name']}

## Summary of Completed Work

(Describe what was built and delivered.)

## Files Changed

(List key files or link to diff/PR.)

## How to Run / Test

(Instructions for the client to verify the work.)

## Known Limitations

(Any known issues, edge cases, or deferred items.)

## Suggested Next Steps

(Optional follow-on work or recommendations.)

## Review Note

Please review everything carefully. Reply on the platform if you have questions or requests.
"""


def _install_template() -> str:
    return """\
# Installation and Setup

## Requirements

- (List dependencies)

## Installation Steps

1. (Step 1)
2. (Step 2)
3. (Step 3)

## Configuration

(Describe any required environment variables or config files.)

## Running Tests

```bash
# Example
pytest
```
"""


def _invoice_notes_template(data: dict) -> str:
    return f"""\
# Invoice Notes — {data['project_title']}

**Client:** {data['client_name']}

## Contract Details

- Budget type: {data['budget_type']}
- Budget min: {data.get('budget_min') or 'TBD'}
- Budget max: {data.get('budget_max') or 'TBD'}

## Hours Logged

| Date | Hours | Description |
|------|-------|-------------|
|      |       |             |

## Payment Notes

(Notes on platform payment, milestone releases, etc.)
"""


def _followups_template() -> str:
    return """\
# Follow-ups

## Scheduled Check-ins

| Date | Topic | Status |
|------|-------|--------|
|      |       |        |

## Open Questions

- (Question 1)

## Action Items

- [ ] (Action item)
"""


def _outcome_template() -> str:
    return """\
# Outcome Record

## Result

- [ ] Won
- [ ] Lost
- [ ] Cancelled
- [ ] Incomplete

## Lessons Learned

(What worked? What would you do differently?)

## Client Quality Rating

(1-5 stars, notes on communication, scope clarity, payment speed.)
"""
