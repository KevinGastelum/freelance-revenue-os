"""Delivery package generation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from freelance_os.models import ClientProject


def create_delivery_package(project: "ClientProject", force: bool = False) -> None:
    if not project.workspace_path:
        raise ValueError("Project has no workspace_path set.")

    delivery_dir = Path(project.workspace_path) / "02_delivery"
    delivery_dir.mkdir(parents=True, exist_ok=True)

    _write_qa_report(delivery_dir, project, force)
    _write_delivery_message(delivery_dir, project, force)
    _ensure_delivery_stubs(delivery_dir, force)


def _write_qa_report(delivery_dir: Path, project: "ClientProject", force: bool) -> None:
    path = delivery_dir / "qa_report.md"
    if path.exists() and not force:
        return
    content = f"""# QA Report

**Project:** {project.project_name}
**Client:** {project.client_name}

## Test Results

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual walkthrough complete

## Known Issues

- (none)

## QA Sign-off

- [ ] Reviewed by developer
- [ ] Ready for delivery
"""
    path.write_text(content)


def _write_delivery_message(delivery_dir: Path, project: "ClientProject", force: bool) -> None:
    path = delivery_dir / "delivery_message_draft.md"
    if path.exists() and not force:
        return
    content = f"""DRAFT ONLY — USER MUST REVIEW AND SEND MANUALLY

---

Hi,

I'm happy to share that the work on **{project.project_name}** is complete and ready for your review.

## Summary of Completed Work

- (describe what was built)
- (describe key decisions made)
- (note any scope adjustments)

## Files Changed

- (list key files or link to repo)

## How to Run / Test

Please refer to `install.md` for setup instructions.

## Known Limitations

- (note any known gaps or deferred items)

## Suggested Next Steps

- (optional future improvements)

Please review and let me know if you have any questions or would like any revisions.

Thank you for the opportunity to work on this project.

---

*This is a draft. The user must review and send this message manually through the platform.*
*Do not send this message automatically.*
"""
    path.write_text(content)


def _ensure_delivery_stubs(delivery_dir: Path, force: bool) -> None:
    stubs = {
        "changelog.md": "# Changelog\n\n## v1.0.0 — Initial Delivery\n\n- (describe changes)\n",
        "handoff.md": "# Handoff Notes\n\n## What Was Built\n\n(describe)\n\n## How to Run\n\n(describe)\n\n## Known Limitations\n\n(describe)\n",
        "install.md": "# Installation\n\n## Prerequisites\n\n(list)\n\n## Steps\n\n1. (step)\n",
    }
    for filename, content in stubs.items():
        path = delivery_dir / filename
        if not path.exists() or force:
            path.write_text(content)
