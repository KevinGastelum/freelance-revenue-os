"""Milestone document generation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from freelance_os.models import Lead


def write_milestone_files(contract_dir: Path, lead: "Lead") -> None:
    content = f"""# Milestones

**Project:** {lead.title or '(untitled)'}

## Milestone 1 — Setup & Scoping

- [ ] Review brief and confirm scope
- [ ] Set up workspace and repo
- [ ] Confirm acceptance criteria with client

**Deliverable:** Confirmed scope document

---

## Milestone 2 — Core Implementation

- [ ] Implement primary feature set
- [ ] Internal QA pass
- [ ] Share progress update with client

**Deliverable:** Working prototype / first build

---

## Milestone 3 — Review & Delivery

- [ ] Final QA
- [ ] Generate delivery package
- [ ] Send handoff (manually)
- [ ] Request milestone release (manually)

**Deliverable:** Final delivery + documentation
"""
    (contract_dir / "milestones.md").write_text(content)
