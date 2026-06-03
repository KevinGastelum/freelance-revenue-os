"""Deterministic proposal draft generator — no LLM calls."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlmodel import Session

from freelance_os.models import ProposalDraft
from freelance_os.proposal.portfolio_matcher import find_matches
from freelance_os.proposal.templates import render_proposal

if TYPE_CHECKING:
    from freelance_os.models import Lead


def generate_draft(lead: "Lead", session: Session) -> ProposalDraft:
    """Generate a deterministic proposal draft from lead data."""

    description = lead.description or ""
    title = lead.title or "this project"

    # Identify core problem from lead text
    core_bottleneck = _extract_core_problem(description, title)
    surface_task = _extract_surface_task(description, title)

    # Build technical steps from lead context
    steps = _build_technical_steps(description, title)

    # Find portfolio matches
    portfolio_matches = find_matches(lead)
    portfolio_ref, proof_point = _pick_portfolio_ref(portfolio_matches, description)

    # Build clarifying question
    clarifying_question = _build_clarifying_question(description, title)

    # Render draft
    draft_text = render_proposal(
        core_bottleneck=core_bottleneck,
        surface_task=surface_task,
        step_1=steps[0],
        step_2=steps[1],
        step_3=steps[2],
        portfolio_ref=portfolio_ref,
        proof_point=proof_point,
        clarifying_question=clarifying_question,
    )

    # Technical diagnosis section
    technical_diagnosis = (
        f"The lead describes: {title}. "
        f"Core challenge identified: {core_bottleneck}. "
        f"Suggested approach: implement in phases, validate early."
    )

    # Build existing version count
    from sqlmodel import select
    existing = session.exec(
        select(ProposalDraft).where(ProposalDraft.lead_id == lead.id)
    ).all()
    version = len(existing) + 1

    draft = ProposalDraft(
        lead_id=lead.id,
        version=version,
        draft_text=draft_text,
        technical_diagnosis=technical_diagnosis,
        portfolio_matches=json.dumps([m.get("name", "") for m in portfolio_matches]),
        clarifying_questions=clarifying_question,
        price_recommendation=_estimate_price(lead),
    )
    session.add(draft)
    return draft


def _extract_core_problem(description: str, title: str) -> str:
    text = (description + " " + title).lower()
    if "automation" in text or "workflow" in text:
        return "workflow automation"
    if "dashboard" in text or "reporting" in text or "analytics" in text:
        return "data visibility"
    if "api" in text or "integration" in text:
        return "systems integration"
    if "database" in text or "backend" in text:
        return "data architecture"
    if "frontend" in text or "ui" in text or "ux" in text:
        return "user experience"
    return "technical execution"


def _extract_surface_task(description: str, title: str) -> str:
    text = (description + " " + title).lower()
    if "fix" in text or "bug" in text:
        return "bug fix"
    if "build" in text:
        return "build task"
    if "migrate" in text or "migration" in text:
        return "migration"
    if "redesign" in text:
        return "redesign"
    return "implementation"


def _build_technical_steps(description: str, title: str) -> list[str]:
    text = (description + " " + title).lower()
    steps = []

    if "api" in text or "integration" in text:
        steps.append("Audit the existing data flow and integration points")
    else:
        steps.append("Map the current architecture and identify failure points")

    if "database" in text or "sql" in text or "postgres" in text:
        steps.append("Design the schema with proper indexing and constraints")
    elif "dashboard" in text or "analytics" in text:
        steps.append("Define the metrics layer and data pipeline requirements")
    else:
        steps.append("Break scope into atomic deliverables with clear acceptance criteria")

    if "test" in text or "qa" in text:
        steps.append("Implement with tests and a QA checklist before delivery")
    else:
        steps.append("Deliver with documentation and a handoff checklist")

    return steps[:3]


def _pick_portfolio_ref(
    matches: list[dict], description: str
) -> tuple[str, str]:
    if matches:
        item = matches[0]
        name = item.get("name", "a relevant project")
        proof_points = item.get("proof_points", [])
        proof = proof_points[0] if proof_points else "end-to-end delivery"
        return name, proof
    return "full-stack applications", "end-to-end delivery from scoping to deployment"


def _build_clarifying_question(description: str, title: str) -> str:
    text = (description + " " + title).lower()
    if "timeline" in text or "deadline" in text or "asap" in text:
        return "What is the hard deadline, and are there any fixed milestones we need to hit first?"
    if "existing" in text or "codebase" in text or "legacy" in text:
        return "What does the existing codebase look like, and are there tests I can run against it?"
    if "budget" in text or "price" in text or "cost" in text:
        return "Is this a fixed-price engagement or are you open to a time-and-materials arrangement?"
    return "What does success look like at the end of week one — what would make you confident we're on the right track?"


def _estimate_price(lead: "Lead") -> str:
    budget = lead.budget_max or lead.budget_min
    hourly = lead.hourly_max or lead.hourly_min or 75

    if budget:
        return f"Budget aligns: ${budget:,.0f}. Recommend confirming scope before final quote."
    return f"Rate: ${hourly}/hr. Estimate based on scope clarification."
