"""Milestone document templates."""


def milestones_template(data: dict) -> str:
    return f"""\
# Milestones — {data['project_title']}

**Client:** {data['client_name']}

## Milestone Plan

| # | Milestone | Deliverables | Due Date | Status |
|---|-----------|-------------|----------|--------|
| 1 | Kickoff & Setup | Brief confirmed, workspace ready | TBD | Pending |
| 2 | Core Implementation | Main feature(s) delivered | TBD | Pending |
| 3 | Review & QA | Testing complete, feedback incorporated | TBD | Pending |
| 4 | Final Delivery | Packaged and submitted | TBD | Pending |

## Notes

- Milestones will be updated as scope is clarified.
- Each milestone should be confirmed with client before marking complete.
- No milestone payment is requested automatically — client initiates release.
"""
