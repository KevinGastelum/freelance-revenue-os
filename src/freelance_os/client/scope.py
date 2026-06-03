"""Scope document generation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from freelance_os.models import Lead


def write_scope_files(contract_dir: Path, lead: "Lead") -> None:
    _write_brief(contract_dir, lead)
    _write_scope(contract_dir, lead)
    _write_platform_messages(contract_dir)
    _write_risk_log(contract_dir)


def _write_brief(contract_dir: Path, lead: "Lead") -> None:
    content = f"""# Project Brief

**Title:** {lead.title or '(untitled)'}
**Source:** {lead.source}
**URL:** {lead.source_url or '(none)'}
**Client:** {lead.client_name or '(unknown)'}

## Description

{lead.description or '(none)'}

## Budget

- Min: {lead.budget_min or lead.hourly_min or '?'}
- Max: {lead.budget_max or lead.hourly_max or '?'}
"""
    (contract_dir / "brief.md").write_text(content)


def _write_scope(contract_dir: Path, lead: "Lead") -> None:
    content = f"""# Scope of Work

**Project:** {lead.title or '(untitled)'}

## In Scope

- [ ] (define deliverable 1)
- [ ] (define deliverable 2)
- [ ] (define deliverable 3)

## Out of Scope

- (list explicitly excluded items)

## Acceptance Criteria

- [ ] (criterion 1)
- [ ] (criterion 2)

## Revision Policy

Up to 2 rounds of revision included. Additional revisions billed separately.
"""
    (contract_dir / "scope.md").write_text(content)


def _write_platform_messages(contract_dir: Path) -> None:
    content = """# Platform Messages

**IMPORTANT: All messages must be sent manually by the user.**

Record key platform communications here for reference.

## Messages Log

| Date | Direction | Summary |
|------|-----------|---------|
|      |           |         |
"""
    (contract_dir / "platform_messages.md").write_text(content)


def _write_risk_log(contract_dir: Path) -> None:
    content = """# Risk Log

| Date | Risk | Likelihood | Impact | Mitigation |
|------|------|-----------|--------|------------|
|      |      |           |        |            |
"""
    (contract_dir / "risk_log.md").write_text(content)
