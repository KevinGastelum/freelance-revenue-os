"""Scope document templates."""


def brief_template(data: dict) -> str:
    return f"""\
# Project Brief

**Client:** {data['client_name']}
**Project:** {data['project_title']}
**Platform:** {data['platform']}
**Source URL:** {data['source_url'] or 'N/A'}

## Original Job Description

{data['description'] or '(paste job description here)'}

## Key Requirements

(Extract from job description - to be filled during kickoff)

## Stakeholders

| Name | Role | Contact Method |
|------|------|---------------|
| {data['client_name']} | Client | Platform messages |

## Timeline Overview

- Start date: TBD
- Target delivery: TBD
"""


def scope_template(data: dict) -> str:
    return f"""\
# Scope of Work

**Project:** {data['project_title']}
**Client:** {data['client_name']}

## In Scope

1. (Feature / deliverable 1)
2. (Feature / deliverable 2)
3. (Feature / deliverable 3)

## Out of Scope

- (Explicitly out of scope item)
- (Another out of scope item)

## Acceptance Criteria

- [ ] (Criterion 1 - measurable)
- [ ] (Criterion 2)
- [ ] (Criterion 3)

## Assumptions

- (Assumption 1 - to be validated with client)

## Change Request Process

Any scope changes must be agreed in writing on the platform before work begins.
"""
