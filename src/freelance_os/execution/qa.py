"""QA checklist generator."""

from pathlib import Path


def generate_qa_checklist(project_name: str, cfg: dict) -> str:
    """Generate a QA checklist and write to 02_delivery/qa_report.md."""
    base_dir = Path(cfg["paths"].get("client_work_dir", "./client-work"))
    delivery_dir = base_dir / project_name / "02_delivery"
    delivery_dir.mkdir(parents=True, exist_ok=True)
    qa_path = delivery_dir / "qa_report.md"

    content = f"""\
# QA Report — {project_name}

## Pre-Delivery Checklist

- [ ] All acceptance criteria met (see scope.md)
- [ ] No broken imports or runtime errors
- [ ] Tests pass (if test suite exists)
- [ ] No hardcoded secrets or credentials
- [ ] README updated
- [ ] Changelog updated
- [ ] Install instructions verified
- [ ] Handoff document complete
- [ ] Delivery message draft reviewed

## Test Results

| Test | Status | Notes |
|------|--------|-------|
|      | Pass   |       |

## Sign-off

Developer: ___________________  Date: ___________
"""
    qa_path.write_text(content, encoding="utf-8")
    return str(qa_path)
