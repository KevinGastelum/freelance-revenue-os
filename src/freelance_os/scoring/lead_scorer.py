"""Lead scoring engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from freelance_os.models import Decision
from freelance_os.scoring.risk_rules import apply_risk_penalties

if TYPE_CHECKING:
    from freelance_os.models import Lead


@dataclass
class ScoreResult:
    lead_score: float
    risk_score: float
    decision: Decision
    reason_codes: list[str] = field(default_factory=list)


def score_lead(lead: "Lead") -> ScoreResult:
    """Score a lead and return a ScoreResult."""
    reasons: list[str] = []
    base_score = 0.0

    # 20% technical fit — inferred from description keywords
    tech_score = _score_technical_fit(lead, reasons)
    base_score += tech_score * 0.20

    # 15% budget fit
    budget_score = _score_budget_fit(lead, reasons)
    base_score += budget_score * 0.15

    # 15% client quality
    client_score = _score_client_quality(lead, reasons)
    base_score += client_score * 0.15

    # 10% clarity of scope
    clarity_score = _score_clarity(lead, reasons)
    base_score += clarity_score * 0.10

    # 10% urgency/timing — default moderate
    base_score += 50 * 0.10
    reasons.append("TIMING_NEUTRAL")

    # 10% portfolio match — heuristic
    portfolio_score = _score_portfolio_match(lead, reasons)
    base_score += portfolio_score * 0.10

    # 10% repeat-work potential
    repeat_score = _score_repeat_potential(lead, reasons)
    base_score += repeat_score * 0.10

    # 10% communication quality
    comm_score = _score_communication(lead, reasons)
    base_score += comm_score * 0.10

    # Apply risk penalties
    risk_score, risk_reasons = apply_risk_penalties(lead)
    reasons.extend(risk_reasons)

    final_score = max(0.0, min(100.0, base_score - risk_score))
    decision = _decide(final_score)

    return ScoreResult(
        lead_score=round(final_score, 1),
        risk_score=round(risk_score, 1),
        decision=decision,
        reason_codes=reasons,
    )


def _decide(score: float) -> Decision:
    if score >= 80:
        return Decision.DRAFT_NOW
    elif score >= 65:
        return Decision.WATCH
    elif score >= 50:
        return Decision.MAYBE
    return Decision.REJECT


# ---------------------------------------------------------------------------
# Dimension scorers — all return 0–100
# ---------------------------------------------------------------------------

_TECH_KEYWORDS = [
    "python", "fastapi", "django", "flask", "next.js", "nextjs", "react",
    "typescript", "postgres", "postgresql", "sqlite", "supabase", "prisma",
    "powerbi", "power bi", "sql", "data", "analytics", "api", "rest",
    "graphql", "docker", "kubernetes", "aws", "gcp", "azure", "ai", "ml",
    "machine learning", "llm", "openai", "anthropic", "claude",
]

_UNSUPPORTED_KEYWORDS = [
    "ios", "swift", "objective-c", "android", "kotlin", "java",
    "c++", "rust", "embedded", "firmware", "blockchain", "solidity",
    "game development", "unity", "unreal",
]


def _score_technical_fit(lead: "Lead", reasons: list[str]) -> float:
    text = ((lead.description or "") + " " + (lead.title or "")).lower()
    matches = sum(1 for kw in _TECH_KEYWORDS if kw in text)
    unsupported = sum(1 for kw in _UNSUPPORTED_KEYWORDS if kw in text)

    if unsupported > 0:
        reasons.append("UNSUPPORTED_STACK")
        return max(0.0, 30.0 - unsupported * 15)
    if matches >= 3:
        reasons.append("TECH_STACK_MATCH")
        return 90.0
    if matches >= 1:
        reasons.append("PARTIAL_TECH_MATCH")
        return 60.0
    reasons.append("TECH_STACK_UNCLEAR")
    return 30.0


def _score_budget_fit(lead: "Lead", reasons: list[str]) -> float:
    budget = lead.budget_max or lead.budget_min or 0
    hourly = lead.hourly_max or lead.hourly_min or 0

    if hourly >= 75:
        reasons.append("HIGH_HOURLY_RATE")
        return 95.0
    if hourly >= 50:
        reasons.append("ADEQUATE_HOURLY_RATE")
        return 70.0
    if budget >= 1000:
        reasons.append("HIGH_BUDGET_FIT")
        return 90.0
    if budget >= 300:
        reasons.append("ADEQUATE_BUDGET")
        return 65.0
    if budget > 0:
        reasons.append("LOW_BUDGET")
        return 25.0
    reasons.append("BUDGET_UNKNOWN")
    return 50.0


def _score_client_quality(lead: "Lead", reasons: list[str]) -> float:
    score = 50.0
    if lead.client_payment_verified:
        reasons.append("PAYMENT_VERIFIED")
        score += 20.0
    if lead.client_rating and lead.client_rating >= 4.5:
        reasons.append("HIGH_CLIENT_RATING")
        score += 20.0
    elif lead.client_rating and lead.client_rating >= 4.0:
        score += 10.0
    elif lead.client_rating and lead.client_rating < 3.5:
        reasons.append("LOW_CLIENT_RATING")
        score -= 20.0
    return min(100.0, max(0.0, score))


def _score_clarity(lead: "Lead", reasons: list[str]) -> float:
    text = (lead.description or "").strip()
    if len(text) >= 300:
        reasons.append("CLEAR_SCOPE")
        return 80.0
    if len(text) >= 100:
        return 55.0
    reasons.append("VAGUE_SCOPE")
    return 20.0


def _score_portfolio_match(lead: "Lead", reasons: list[str]) -> float:
    text = ((lead.description or "") + " " + (lead.title or "")).lower()
    strong_match_kws = ["next.js", "supabase", "power bi", "powerbi", "analytics", "dashboard"]
    matches = sum(1 for kw in strong_match_kws if kw in text)
    if matches >= 2:
        reasons.append("STRONG_PORTFOLIO_MATCH")
        return 90.0
    if matches >= 1:
        reasons.append("PARTIAL_PORTFOLIO_MATCH")
        return 60.0
    return 40.0


def _score_repeat_potential(lead: "Lead", reasons: list[str]) -> float:
    text = (lead.description or "").lower()
    if any(kw in text for kw in ["ongoing", "long-term", "retainer", "monthly"]):
        reasons.append("REPEAT_WORK_POTENTIAL")
        return 80.0
    return 50.0


def _score_communication(lead: "Lead", reasons: list[str]) -> float:
    text = (lead.description or "").strip()
    word_count = len(text.split())
    if word_count >= 100:
        reasons.append("GOOD_COMMUNICATION_QUALITY")
        return 75.0
    if word_count >= 30:
        return 55.0
    reasons.append("POOR_COMMUNICATION_QUALITY")
    return 25.0
