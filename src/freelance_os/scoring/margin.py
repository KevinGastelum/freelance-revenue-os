"""AI-leverage margin scorer for the pull command.

Scores normalized lead dicts by $/hour margin, reputation value, and
confidence. Does NOT include any tech-stack-match term.
"""

import math
import re
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

# Log-curve margin normalization bounds ($/hr).
_LOG_MARGIN_FLOOR = 40.0   # below this scores 0
_LOG_MARGIN_CAP = 1000.0   # above this saturates to 1

# Quantity cues that signal multi-deliverable scope.
_QUANTITY_CUES = frozenset({
    "pages", "endpoints", "screens", "routes", "components", "modules",
    "services", "tables", "reports", "dashboards", "integrations", "features",
    "workflows", "steps", "phases", "requirements",
})


def _estimate_effort_hours(description: str, title: str = "") -> float:
    """Return a heuristic effort estimate in hours (no LLM)."""
    text = (title + " " + description).lower()
    all_words = text.split()
    words = set(all_words)

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
        wc = len(all_words)
        if wc > 300:
            base = 20.0
        elif wc < 30:
            base = 8.0
        else:
            base = 10.0

    # Blend: quantity cues and deliverable bullet lists add signal.
    qty_hits = sum(1 for w in all_words if w in _QUANTITY_CUES)
    deliverable_lines = len(re.findall(r"(?m)^\s*(?:[-*•]|\d+\.)\s", description))
    extra_signal = qty_hits + deliverable_lines
    if extra_signal >= 5:
        base = max(base, 25.0)
    elif extra_signal >= 3:
        base = max(base, base * 1.5)
    elif extra_signal >= 1 and not small:
        base = max(base, base * 1.2)

    return base


def _norm_margin(margin: float) -> float:
    """Log-curve normalize $/hr margin between FLOOR and CAP to [0, 1]."""
    _ln_floor = math.log(_LOG_MARGIN_FLOOR)
    _ln_cap = math.log(_LOG_MARGIN_CAP)
    raw = (math.log(max(margin, _LOG_MARGIN_FLOOR)) - _ln_floor) / (_ln_cap - _ln_floor)
    return max(0.0, min(1.0, raw))


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
    budget_type = (lead.get("budget") or {}).get("type") or "fixed"
    rep_value = _reputation_value(lead)

    if budget_type == "annual":
        # Treat as effective hourly; do not divide by effort_hours.
        margin = budget_usd / 2080.0
    else:
        margin = budget_usd / max(effort_hours, 0.25)

    norm_margin_val = _norm_margin(margin)
    final_score = w_margin * norm_margin_val + w_rep * rep_value + w_conf * confidence

    if budget_type == "annual":
        final_score = final_score * 0.6
        eff_hr = budget_usd / 2080.0
        verdict = f"salaried ~${budget_usd:.0f}/yr, eff ${eff_hr:.0f}/hr, conf {'L' if confidence < 0.35 else ('M' if confidence < 0.65 else 'H')}, {'rep+' if rep_value >= 0.6 else ('rep~' if rep_value >= 0.4 else 'rep-')}"
    else:
        conf_label = "L" if confidence < 0.35 else ("M" if confidence < 0.65 else "H")
        rep_label = "rep+" if rep_value >= 0.6 else ("rep~" if rep_value >= 0.4 else "rep-")
        budget_str = f"${budget_usd:.0f}" if budget_usd > 0 else "?"
        verdict = f"quick buck: ~{effort_hours:.0f}h, {budget_str}, conf {conf_label}, {rep_label}"
        if margin > 500 and confidence <= 0.35:
            verdict += " [suspicious margin]"

    return {
        "effort_hours": effort_hours,
        "confidence": round(confidence, 3),
        "budget_usd": round(budget_usd, 2),
        "margin": round(margin, 2),
        "reputation_value": round(rep_value, 3),
        "final_score": round(final_score, 4),
        "verdict": verdict,
    }
