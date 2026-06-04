"""Lead scoring engine per PRD section 10."""

import re
from typing import Dict, List

from freelance_os.models import Decision, Lead
from freelance_os.scoring.risk_rules import apply_risk_penalties

SUPPORTED_TECH = [
    "python", "fastapi", "flask", "django",
    "nextjs", "next.js", "react", "typescript", "javascript",
    "supabase", "postgres", "postgresql", "sqlite", "mysql",
    "prisma", "sqlalchemy",
    "power bi", "powerbi", "dax", "sql",
    "claude", "openai", "llm", "ai",
    "docker", "github", "git",
    "pandas", "numpy", "jupyter",
]

UNSUPPORTED_TECH = [
    "ruby on rails", "ruby", "php", "laravel", "wordpress",
    "ios", "swift", "kotlin", "android", "flutter",
    "unity", "unreal", "c++", "c#", "java spring",
    "solidity", "blockchain", "nft",
    "matlab",
]

_DEFAULT_WEIGHTS = {
    "technical_fit": 20,
    "budget_fit": 15,
    "client_quality": 15,
    "clarity_of_scope": 10,
    "urgency_timing": 10,
    "portfolio_match": 10,
    "repeat_work_potential": 10,
    "communication_quality": 10,
}

_DEFAULT_THRESHOLDS = {
    "draft_now_min": 80,
    "watch_min": 65,
    "maybe_min": 50,
}


def _score_tech_fit(text: str) -> tuple[int, List[str]]:
    """Return (0-20 points, reason_codes)."""
    text_lower = text.lower()
    matches = sum(1 for t in SUPPORTED_TECH if t in text_lower)
    unsupported = sum(1 for t in UNSUPPORTED_TECH if t in text_lower)
    score = min(20, matches * 4)
    codes: List[str] = []
    if matches >= 2:
        codes.append("TECH_STACK_MATCH")
    if unsupported:
        score = max(0, score - unsupported * 5)
        codes.append("UNSUPPORTED_STACK")
    return score, codes


def _score_budget_fit(lead: Lead) -> tuple[int, List[str]]:
    """Return (0-15 points, reason_codes)."""
    codes: List[str] = []
    budget = lead.budget_max or lead.budget_min
    hourly = lead.hourly_max or lead.hourly_min
    if budget and budget >= 1000:
        codes.append("HIGH_BUDGET_FIT")
        return 15, codes
    elif budget and budget >= 500:
        codes.append("BUDGET_FIT")
        return 10, codes
    elif budget and budget < 200:
        codes.append("LOW_BUDGET")
        return 0, codes
    elif hourly and hourly >= 60:
        codes.append("HIGH_BUDGET_FIT")
        return 15, codes
    elif hourly and hourly >= 40:
        codes.append("BUDGET_FIT")
        return 8, codes
    elif hourly and hourly < 25:
        codes.append("LOW_BUDGET")
        return 0, codes
    return 7, codes  # unknown budget — neutral


def _score_clarity(text: str) -> tuple[int, List[str]]:
    """Return (0-10 points, reason_codes)."""
    codes: List[str] = []
    word_count = len(text.split())
    has_deliverables = bool(re.search(
        r"deliver|outcome|result|milestone|phase|feature|requirement", text, re.I
    ))
    if word_count > 100 and has_deliverables:
        codes.append("CLEAR_SCOPE")
        return 10, codes
    elif word_count > 50:
        return 6, codes
    return 2, codes


def _score_portfolio_match(text: str) -> tuple[int, List[str]]:
    """Return (0-10 points, reason_codes)."""
    codes: List[str] = []
    text_lower = text.lower()
    matches = sum(1 for t in SUPPORTED_TECH if t in text_lower)
    if matches >= 3:
        codes.append("STRONG_PORTFOLIO_MATCH")
        return 10, codes
    elif matches >= 1:
        codes.append("PORTFOLIO_MATCH")
        return 5, codes
    return 0, codes


def _score_client_quality(lead: Lead) -> tuple[int, List[str]]:
    """Return (0-15 points, reason_codes)."""
    codes: List[str] = []
    score = 0
    if lead.client_payment_verified:
        score += 8
        codes.append("CLIENT_PAYMENT_VERIFIED")
    if lead.client_rating and lead.client_rating >= 4.5:
        score += 7
    elif lead.client_rating and lead.client_rating >= 4.0:
        score += 4
    return min(15, score), codes


def score_lead(lead: Lead, cfg: dict) -> Dict:
    """Score a lead 0-100. Returns dict with lead_score, risk_score, decision, reason_codes.

    cfg may contain a "scoring_rules" key with weights, thresholds, and risk_penalties.
    Falls back to defaults if not present.
    """
    sr = cfg.get("scoring_rules", {})

    weights = {**_DEFAULT_WEIGHTS, **sr.get("weights", {})}
    thresholds = {**_DEFAULT_THRESHOLDS, **sr.get("thresholds", {})}
    penalty_cfg = sr.get("risk_penalties") or None

    text = " ".join(filter(None, [lead.title, lead.description, lead.notes]))

    tech_raw, tech_codes = _score_tech_fit(text)
    budget_raw, budget_codes = _score_budget_fit(lead)
    clarity_raw, clarity_codes = _score_clarity(text)
    portfolio_raw, portfolio_codes = _score_portfolio_match(text)
    client_raw, client_codes = _score_client_quality(lead)

    urgency_raw = 5
    repeat_raw = 5
    if re.search(r"ongoing|long.?term|retainer|monthly|repeat", text, re.I):
        repeat_raw = 10
    comm_raw = 5
    if len(text.split()) > 150:
        comm_raw = 10

    def _scale(raw: float, component: str, default_max: int) -> float:
        w = weights.get(component, default_max)
        return (raw / default_max) * w if default_max > 0 else 0.0

    raw_score = (
        _scale(tech_raw, "technical_fit", 20)
        + _scale(budget_raw, "budget_fit", 15)
        + _scale(client_raw, "client_quality", 15)
        + _scale(clarity_raw, "clarity_of_scope", 10)
        + _scale(urgency_raw, "urgency_timing", 10)
        + _scale(portfolio_raw, "portfolio_match", 10)
        + _scale(repeat_raw, "repeat_work_potential", 10)
        + _scale(comm_raw, "communication_quality", 10)
    )

    penalty, risk_codes = apply_risk_penalties(text, penalty_cfg)
    risk_score = min(100, penalty)
    lead_score = max(0, min(100, round(raw_score - penalty)))

    all_codes = (
        tech_codes + budget_codes + clarity_codes
        + portfolio_codes + client_codes + risk_codes
    )

    draft_min = int(thresholds.get("draft_now_min", 80))
    watch_min = int(thresholds.get("watch_min", 65))
    maybe_min = int(thresholds.get("maybe_min", 50))

    if lead_score >= draft_min:
        decision = Decision.DRAFT_NOW
    elif lead_score >= watch_min:
        decision = Decision.WATCH
    elif lead_score >= maybe_min:
        decision = Decision.MAYBE
    else:
        decision = Decision.REJECT

    if not all_codes:
        all_codes = ["NO_STRONG_SIGNAL"]

    return {
        "lead_score": lead_score,
        "risk_score": risk_score,
        "decision": decision.value,
        "reason_codes": all_codes,
    }
