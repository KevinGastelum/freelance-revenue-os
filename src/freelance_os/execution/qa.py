"""QA checklist generation."""

from __future__ import annotations

from pathlib import Path


def generate_qa_checklist(workspace_path: Path) -> Path:
    checklist_path = workspace_path / "01_workspace" / "qa_checklist.md"
    content = """# QA Checklist

## Functionality

- [ ] All acceptance criteria from scope.md are met
- [ ] Happy path works end-to-end
- [ ] Edge cases identified and handled
- [ ] Error handling is in place

## Code Quality

- [ ] No debug/print statements left in
- [ ] Linting passes
- [ ] Tests pass

## Documentation

- [ ] README updated
- [ ] Changelog updated
- [ ] Install instructions verified

## Delivery

- [ ] Delivery package generated
- [ ] delivery_message_draft.md reviewed by user
- [ ] User sends delivery message manually
"""
    checklist_path.parent.mkdir(parents=True, exist_ok=True)
    checklist_path.write_text(content)
    return checklist_path
