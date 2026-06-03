"""Client workspace creation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from sqlmodel import Session

from freelance_os.config import load_settings
from freelance_os.models import ClientProject, ClientProjectStatus

if TYPE_CHECKING:
    from freelance_os.models import Lead


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:50].strip("-")


def create_workspace(
    lead: "Lead",
    session: Session,
    repo_url: Optional[str] = None,
    force: bool = False,
) -> ClientProject:
    settings = load_settings()
    client_work_dir = settings.client_work_dir

    client_name = _slugify(lead.client_name or "client")
    project_name = _slugify(lead.title or f"project-{lead.id}")
    workspace_name = f"{client_name}-{project_name}"
    workspace_path = client_work_dir / workspace_name

    if workspace_path.exists() and not force:
        raise FileExistsError(
            f"Workspace already exists: {workspace_path}. Use --force to overwrite."
        )

    _create_directory_tree(workspace_path, lead)

    branch_name = f"client/{lead.source}-{workspace_name}"

    project = ClientProject(
        lead_id=lead.id,
        client_name=lead.client_name or "Client",
        project_name=project_name,
        platform=lead.source,
        status=ClientProjectStatus.INTAKE,
        workspace_path=str(workspace_path),
        scope_path=str(workspace_path / "00_contract" / "scope.md"),
        delivery_path=str(workspace_path / "02_delivery"),
        repo_url=repo_url,
        branch_name=branch_name,
    )
    session.add(project)
    return project


def _create_directory_tree(workspace_path: Path, lead: "Lead") -> None:
    dirs = [
        workspace_path / "00_contract",
        workspace_path / "01_workspace",
        workspace_path / "02_delivery" / "screenshots",
        workspace_path / "03_admin",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    from freelance_os.client.scope import write_scope_files
    from freelance_os.client.milestones import write_milestone_files

    write_scope_files(workspace_path / "00_contract", lead)
    write_milestone_files(workspace_path / "00_contract", lead)
    _write_workspace_readme(workspace_path / "01_workspace", lead)
    _write_admin_files(workspace_path / "03_admin", lead)
    _write_delivery_stubs(workspace_path / "02_delivery", lead)


def _write_workspace_readme(workspace_dir: Path, lead: "Lead") -> None:
    content = f"""# Workspace: {lead.title or 'Project'}

**Source:** {lead.source}
**Status:** Active

## Setup

1. Clone or use existing repo.
2. Install dependencies.
3. Review `../00_contract/scope.md` for acceptance criteria.

## Notes

{lead.notes or '(none)'}
"""
    (workspace_dir / "README.md").write_text(content)


def _write_admin_files(admin_dir: Path, lead: "Lead") -> None:
    (admin_dir / "invoice_notes.md").write_text(
        "# Invoice Notes\n\nRecord billing milestones, invoice numbers, and payment status here.\n"
    )
    (admin_dir / "followups.md").write_text(
        "# Follow-ups\n\nTrack client communications and scheduled follow-ups here.\n"
    )
    (admin_dir / "outcome.md").write_text(
        "# Outcome\n\nRecord final outcome, lessons learned, and retrospective notes here.\n"
    )


def _write_delivery_stubs(delivery_dir: Path, lead: "Lead") -> None:
    (delivery_dir / "changelog.md").write_text(
        "# Changelog\n\n## v1.0.0 — Initial Delivery\n\n- (describe changes here)\n"
    )
    (delivery_dir / "handoff.md").write_text(
        "# Handoff Notes\n\n## What Was Built\n\n(describe)\n\n## How to Run\n\n(describe)\n\n## Known Limitations\n\n(describe)\n"
    )
    (delivery_dir / "install.md").write_text(
        "# Installation\n\n## Prerequisites\n\n(list)\n\n## Steps\n\n(describe)\n"
    )
