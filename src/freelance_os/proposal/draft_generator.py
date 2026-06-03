"""Deterministic proposal draft generator (NO LLM calls per PRD)."""

import re
from typing import Dict, List

from freelance_os.models import Lead
from freelance_os.proposal.portfolio_matcher import (
    get_best_proof_point,
    get_project_reference,
    match_portfolio,
)
from freelance_os.proposal.templates import render_proposal


def _infer_surface_task(text: str) -> str:
    """Infer what the client calls the task."""
    patterns = [
        (r"build\s+(?:a\s+)?(\w+\s+\w+)", 1),
        (r"create\s+(?:a\s+)?(\w+\s+\w+)", 1),
        (r"develop\s+(?:a\s+)?(\w+\s+\w+)", 1),
        (r"fix\s+(?:a\s+)?(\w+\s+\w+)", 1),
        (r"design\s+(?:a\s+)?(\w+\s+\w+)", 1),
    ]
    for pattern, group in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(group).strip()
    return "implementation"


def _infer_bottleneck(text: str) -> str:
    """Infer the real underlying problem."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["slow", "performance", "latency", "speed"]):
        return "performance and scalability"
    if any(w in text_lower for w in ["auth", "login", "security", "access"]):
        return "authentication and authorization"
    if any(w in text_lower for w in ["data", "database", "sync", "pipeline"]):
        return "data architecture and reliability"
    if any(w in text_lower for w in ["api", "integration", "webhook", "connect"]):
        return "systems integration"
    if any(w in text_lower for w in ["dashboard", "report", "analytics", "chart"]):
        return "data visibility and decision-making"
    if any(w in text_lower for w in ["automate", "workflow", "process", "manual"]):
        return "workflow automation and efficiency"
    return "technical architecture"


def _generate_steps(text: str) -> List[str]:
    """Generate three solution steps based on job text."""
    text_lower = text.lower()
    steps = []

    if any(w in text_lower for w in ["api", "backend", "endpoint"]):
        steps.append("Design and implement a clean REST API with proper error handling")
    elif any(w in text_lower for w in ["data", "database", "sql"]):
        steps.append("Audit and optimize the data model for reliability and performance")
    else:
        steps.append("Define clear acceptance criteria and a minimal working implementation plan")

    if any(w in text_lower for w in ["test", "qa", "quality"]):
        steps.append("Write automated tests covering core flows and edge cases")
    elif any(w in text_lower for w in ["deploy", "production", "hosting"]):
        steps.append("Set up deployment pipeline with environment-appropriate configuration")
    else:
        steps.append("Implement core functionality with clean, reviewable code")

    if any(w in text_lower for w in ["doc", "readme", "handoff"]):
        steps.append("Document the system clearly with a README and handoff notes")
    else:
        steps.append("Deliver with clear documentation and a demo or walkthrough")

    while len(steps) < 3:
        steps.append("Review and iterate based on your feedback")

    return steps[:3]


def _generate_clarifying_question(text: str) -> str:
    """Generate a scope-locking clarifying question."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["deadline", "timeline", "urgent", "asap"]):
        return "What is the hard deadline, and are there any milestones we should hit before the final delivery?"
    if any(w in text_lower for w in ["api", "integration", "third-party"]):
        return "Which third-party APIs or services need to be integrated, and do you have existing credentials or documentation for them?"
    if any(w in text_lower for w in ["existing", "current", "legacy", "rewrite"]):
        return "Is this a greenfield project or are there existing systems or codebases I should plan around?"
    if any(w in text_lower for w in ["design", "ui", "frontend"]):
        return "Do you have design mockups or a brand guide, or should I propose a minimal design direction?"
    return "What does 'done' look like to you -- is there a specific metric or user flow that signals success?"


def _estimate_price(lead: Lead, cfg: dict) -> str:
    """Generate a rough price recommendation."""
    target_rate = cfg.get("scoring", {}).get("target_hourly_rate", 75)
    min_value = cfg.get("scoring", {}).get("minimum_project_value", 300)

    text = " ".join(filter(None, [lead.title, lead.description]))
    word_count = len(text.split())

    # Rough complexity proxy
    if word_count < 50:
        estimated_hours = 8
    elif word_count < 150:
        estimated_hours = 20
    else:
        estimated_hours = 40

    base = max(min_value, estimated_hours * target_rate)
    high = base * 1.5

    return f"Estimated range: ${base:.0f} - ${high:.0f} (based on complexity; will refine after scope call)"


def generate_draft(lead: Lead, cfg: dict) -> Dict:
    """Generate a proposal draft dict (no LLM calls)."""
    text = " ".join(filter(None, [lead.title, lead.description, lead.notes]))

    portfolio_matches = match_portfolio(text, cfg)
    project_reference = get_project_reference(portfolio_matches)
    proof_point = get_best_proof_point(portfolio_matches)

    surface_task = _infer_surface_task(text) if text.strip() else "implementation"
    bottleneck = _infer_bottleneck(text) if text.strip() else "technical architecture"
    steps = _generate_steps(text)
    clarifying_question = _generate_clarifying_question(text)
    price_rec = _estimate_price(lead, cfg)

    draft_text = render_proposal(
        core_bottleneck=bottleneck,
        surface_task=surface_task,
        step_1=steps[0],
        step_2=steps[1],
        step_3=steps[2],
        project_reference=project_reference,
        proof_point=proof_point,
        clarifying_question=clarifying_question,
    )

    return {
        "draft_text": draft_text,
        "technical_diagnosis": f"Core problem identified as: {bottleneck}",
        "portfolio_matches": [m.get("name", "") for m in portfolio_matches],
        "clarifying_questions": [clarifying_question],
        "price_recommendation": price_rec,
    }
