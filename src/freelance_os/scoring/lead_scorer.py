"""Lead scoring engine per PRD section 10."""

import re
from typing import Dict, List

from freelance_os.models import Decision, Lead
from freelance_os.scoring.risk_rules import apply_risk_penalties

# Supported tech stack keywords for tech-fit scoring
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
    # Use fixed budget
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
    # Simple keyword-based match against supported tech
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
    """
    Score a lead 0-100. Returns dict with:
      lead_score, risk_score, decision, reason_codes
    """
    text = " ".join(filter(None, [lead.title, lead.description, lead.notes]))

    tech_score, tech_codes = _score_tech_fit(text)
    budget_score, budget_codes = _score_budget_fit(lead)
    clarity_score, clarity_codes = _score_clarity(text)
    portfolio_score, portfolio_codes = _score_portfolio_match(text)
    client_score, client_codes = _score_client_quality(lead)

    # Urgency/timing: 10 pts flat (no signal available without scraping)
    urgency_score = 5

    # Repeat-work potential: 10 pts
    repeat_score = 5
    if re.search(r"ongoing|long.?term|retainer|monthly|repeat", text, re.I):
        repeat_score = 10

    # Communication quality: 10 pts
    comm_score = 5
    if len(text.split()) > 150:
        comm_score = 10

    raw_score = (
        tech_score        # 20%
        + budget_score    # 15%
        + client_score    # 15%
        + clarity_score   # 10%
        + urgency_score   # 10%
        + portfolio_score # 10%
        + repeat_score    # 10%
        + comm_score      # 10%
    )

    # Apply risk penalties
    penalty, risk_codes = apply_risk_penalties(text)
    risk_score = min(100, penalty)

    lead_score = max(0, min(100, raw_score - penalty))

    all_codes = tech_codes + budget_codes + clarity_codes + portfolio_codes + client_codes + risk_codes

    # Decision thresholds per PRD 10.3
    if lead_score >= 80:
        decision = Decision.DRAFT_NOW
    elif lead_score >= 65:
        decision = Decision.WATCH
    elif lead_score >= 50:
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
