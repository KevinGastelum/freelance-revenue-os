"""Delivery package generation per PRD section 16."""

from pathlib import Path
from typing import Optional


def generate_delivery_package(
    project_name: str,
    cfg: dict,
    force: bool = False,
) -> str:
    """Generate delivery package files in the project's 02_delivery/ folder."""
    base_dir = Path(cfg["paths"].get("client_work_dir", "./client-work"))

    # Find project folder by name (exact match or prefix match)
    workspace: Optional[Path] = None
    if base_dir.exists():
        for folder in base_dir.iterdir():
            if folder.is_dir() and (
                folder.name == project_name or folder.name.endswith(f"-{project_name}")
                or folder.name.startswith(f"{project_name}-") or project_name in folder.name
            ):
                workspace = folder
                break

    if workspace is None:
        # Fall back to creating in base_dir / project_name
        workspace = base_dir / project_name
        workspace.mkdir(parents=True, exist_ok=True)

    delivery_dir = workspace / "02_delivery"
    delivery_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "changelog.md": _changelog_content(project_name),
        "handoff.md": _handoff_content(project_name),
        "install.md": _install_content(),
        "qa_report.md": _qa_report_content(project_name),
        "delivery_message_draft.md": _delivery_message_draft(project_name),
    }

    for filename, content in files.items():
        target = delivery_dir / filename
        if target.exists() and not force:
            continue  # skip existing without --force
        target.write_text(content, encoding="utf-8")

    return str(delivery_dir)


def _changelog_content(project_name: str) -> str:
    return f"""\
# Changelog - {project_name}

## [Delivered]

### Added
- (List completed features)

### Changed
- (List changes from original scope)

### Fixed
- (List bug fixes)

## Notes

- Review with client during delivery call.
"""


def _handoff_content(project_name: str) -> str:
    return f"""\
# Delivery Handoff - {project_name}

## Summary of Completed Work

(Describe what was built, key decisions made, and final state.)

## Files Changed

(List key files or reference the PR/diff.)

## How to Run / Test

1. (Step 1)
2. (Step 2)

## Known Limitations

(Any known issues, edge cases, or deferred items.)

## Suggested Next Steps

(Optional follow-on work if the client wants to continue.)

## Polite Closing

Thank you for the opportunity to work on this project.
Please review the deliverables and let me know on the platform if you have any questions.
"""


def _install_content() -> str:
    return """\
# Installation and Setup

## Requirements

- (List runtime dependencies)
- (Operating system requirements)

## Installation

```bash
# Example installation steps
pip install -r requirements.txt
```

## Configuration

- (Describe config files or environment variables)

## Running

```bash
# Example run command
python main.py
```

## Running Tests

```bash
pytest
```
"""


def _qa_report_content(project_name: str) -> str:
    return f"""\
# QA Report - {project_name}

## Test Coverage

| Area | Status | Notes |
|------|--------|-------|
| Core functionality | Pass | |
| Edge cases | Pass | |
| Error handling | Pass | |

## Manual Test Results

| Scenario | Expected | Actual | Status |
|----------|----------|--------|--------|
| Happy path | Works | Works | Pass |

## Outstanding Issues

- None at time of delivery (or list known issues)

## QA Sign-off

Reviewed and verified by developer before delivery.
"""


def _delivery_message_draft(project_name: str) -> str:
    return f"""\
DRAFT ONLY - USER MUST REVIEW AND SEND MANUALLY
================================================
Do NOT send this automatically. Copy, edit, and submit via the platform manually.

---

Hi [Client Name],

I'm happy to let you know that the work on {project_name} is complete and ready for your review.

Here's a summary of what was delivered:
- [Key deliverable 1]
- [Key deliverable 2]
- [Key deliverable 3]

You can find the full details in the handoff document and changelog included with this delivery.

Please review everything at your convenience. If you have any questions or would like any adjustments,
feel free to reach out through the platform.

Looking forward to your feedback!

Best,
[Your Name]

---

REMINDER: Review and edit this draft before sending. Send manually through the platform.
Do not use automated messaging tools.
"""
