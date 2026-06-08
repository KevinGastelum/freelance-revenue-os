"""AI-leverage margin scorer for the pull command.

Scores normalized lead dicts by $/hour margin, reputation value, and
confidence. Does NOT include any tech-stack-match term.
"""

from typing import Any, Dict

# Static currency -> USD rates (approximate, v1).
_CURRENCY_TO_USD: Dict[str, float] = {
    "USD": 1.00,
    "EUR": 1.08,
    "GBP": 1.27,
    "CAD": 0.74,
    "AUD": 0.65,
    "CHF": 1.11,
    "JPY": 0.0065,
    "INR": 0.012,
    "BRL": 0.20,
    "MXN": 0.058,
    "SGD": 0.74,
    "NZD": 0.61,
    "SEK": 0.095,
    "DKK": 0.145,
    "NOK": 0.095,
    "PLN": 0.25,
    "CZK": 0.044,
    "HUF": 0.0028,
    "ZAR": 0.054,
    "HKD": 0.128,
    "TWD": 0.031,
    "KRW": 0.00075,
    "THB": 0.028,
    "MYR": 0.21,
    "TRY": 0.031,
    "SAR": 0.267,
    "AED": 0.272,
}

# Effort-heuristic keyword sets.
_BIG_SCOPE = frozenset({
    "platform", "system", "enterprise", "saas", "migrate", "migration",
    "architecture", "overhaul", "redesign", "rebuild", "rewrite",
    "full-stack", "fullstack", "end-to-end", "greenfield",
})
_MEDIUM_SCOPE = frozenset({
    "integration", "dashboard", "api", "backend", "frontend",
    "feature", "module", "service", "automation", "pipeline", "bot",
    "scraper", "plugin", "extension",
})
_SMALL_SCOPE = frozenset({
    "fix", "bug", "patch", "tweak", "update", "adjust", "review",
    "audit", "consult", "research", "analyze", "script",
    "simple", "quick", "small", "minor", "tiny",
})

# $/hr reference for normalizing margin (a strong margin benchmark).
_MARGIN_REFERENCE = 200.0


def _estimate_effort_hours(description: str, title: str = "") -> float:
    """Return a heuristic effort estimate in hours (no LLM)."""
    text = (title + " " + description).lower()
    words = set(text.split())

    big = bool(words & _BIG_SCOPE)
    small = bool(words & _SMALL_SCOPE)
    medium = bool(words & _MEDIUM_SCOPE)

    if big:
        base = 40.0
    elif small:
        base = 4.0
    elif medium:
        base = 15.0
    else:
        # No strong scope keyword — use word count as a proxy.
        wc = len(text.split())
        if wc > 300:
            base = 20.0
        elif wc < 30:
            base = 8.0
        else:
            base = 10.0

    return base


def _estimate_confidence(lead: Dict[str, Any]) -> float:
    """Return 0..1 confidence from spec clarity, budget presence, client data."""
    score = 0.0
    budget = lead.get("budget") or {}
    client = lead.get("client") or {}
    desc = lead.get("description", "") or ""

    if budget.get("amount") is not None:
        score += 0.35

    wc = len(desc.split())
    if wc > 200:
        score += 0.25
    elif wc > 80:
        score += 0.15
    elif wc > 30:
        score += 0.08

    if client.get("payment_verified"):
        score += 0.20

    rating = client.get("rating")
    if rating is not None:
        if rating >= 4.5:
            score += 0.10
        elif rating >= 4.0:
            score += 0.05

    if lead.get("skills"):
        score += 0.05

    if lead.get("posted_at"):
        score += 0.05

    return min(1.0, score)


def _to_usd(amount: float, currency: str) -> float:
    rate = _CURRENCY_TO_USD.get((currency or "USD").upper(), 1.0)
    return amount * rate


def _compute_budget_usd(lead: Dict[str, Any], assumed_hours: float = 20.0) -> float:
    """Return estimated total budget in USD."""
    budget = lead.get("budget") or {}
    amount = budget.get("amount")
    if amount is None:
        return 0.0
    usd = _to_usd(float(amount), budget.get("currency") or "USD")
    if (budget.get("type") or "fixed") == "hourly":
        return usd * assumed_hours
    return usd


def _reputation_value(lead: Dict[str, Any]) -> float:
    """Return 0..1 reputation score: higher for low-risk, easy-win gigs."""
    score = 0.5
    text = (
        (lead.get("title", "") or "")
        + " "
        + (lead.get("description", "") or "")
    ).lower()
    client = lead.get("client") or {}
    budget = lead.get("budget") or {}

    easy_words = frozenset({"simple", "quick", "small", "straightforward", "easy", "minor", "basic"})
    if any(w in text.split() for w in easy_words):
        score += 0.15

    hires = client.get("hires")
    if hires is not None and hires < 3:
        score += 0.10

    if client.get("payment_verified"):
        score += 0.15

    wc = len((lead.get("description", "") or "").split())
    if wc < 15:
        score -= 0.20

    return max(0.0, min(1.0, score))


def score_lead(
    lead: Dict[str, Any],
    *,
    assumed_hours: float = 20.0,
    w_margin: float = 0.50,
    w_rep: float = 0.30,
    w_conf: float = 0.20,
    reputation_mode: bool = True,
) -> Dict[str, Any]:
    """Score a normalized lead dict; returns a dict of scoring fields.

    Weights are reconfigured when reputation_mode=True to favour cheap
    easy-win gigs without penalising low dollar amounts.
    """
    if reputation_mode:
        w_margin, w_rep, w_conf = 0.40, 0.40, 0.20

    effort_hours = _estimate_effort_hours(
        lead.get("description", "") or "",
        lead.get("title", "") or "",
    )
    confidence = _estimate_confidence(lead)
    budget_usd = _compute_budget_usd(lead, assumed_hours)
    margin = budget_usd / max(effort_hours, 0.25)
    rep_value = _reputation_value(lead)

    norm_margin = min(1.0, margin / _MARGIN_REFERENCE)
    final_score = w_margin * norm_margin + w_rep * rep_value + w_conf * confidence

    conf_label = "L" if confidence < 0.35 else ("M" if confidence < 0.65 else "H")
    rep_label = "rep+" if rep_value >= 0.6 else ("rep~" if rep_value >= 0.4 else "rep-")
    budget_str = f"${budget_usd:.0f}" if budget_usd > 0 else "?"
    verdict = f"quick buck: ~{effort_hours:.0f}h, {budget_str}, conf {conf_label}, {rep_label}"

    return {
        "effort_hours": effort_hours,
        "confidence": round(confidence, 3),
        "budget_usd": round(budget_usd, 2),
        "margin": round(margin, 2),
        "reputation_value": round(rep_value, 3),
        "final_score": round(final_score, 4),
        "verdict": verdict,
    }
