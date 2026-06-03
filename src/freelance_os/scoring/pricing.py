"""Pricing recommendation module per PRD section 12."""

from freelance_os.models import Lead


def estimate_price(lead: Lead, cfg: dict) -> dict:
    """
    Estimate project price using the PRD section 12 formula.

    Returns:
        {
          "estimated_hours": int,
          "base_estimate": float,
          "risk_adjusted": float,
          "rush_adjusted": float,
          "recommended_quote": float,
          "risk_level": str,
          "summary": str,
        }
    """
    scoring_cfg = cfg.get("scoring", {})
    target_rate = float(scoring_cfg.get("target_hourly_rate", 75))
    min_value = float(scoring_cfg.get("minimum_project_value", 300))
    risk_low = float(scoring_cfg.get("risk_multiplier_low", 1.0))
    risk_med = float(scoring_cfg.get("risk_multiplier_medium", 1.25))
    risk_high = float(scoring_cfg.get("risk_multiplier_high", 1.5))
    rush_mult = float(scoring_cfg.get("rush_multiplier", 1.25))

    # Complexity proxy from description length
    text = " ".join(filter(None, [lead.title, lead.description]))
    words = len(text.split())
    if words < 50:
        estimated_hours = 8
        risk_level = "low"
    elif words < 150:
        estimated_hours = 20
        risk_level = "medium"
    else:
        estimated_hours = 40
        risk_level = "medium"

    # Use risk_score if available
    if lead.risk_score and lead.risk_score >= 30:
        risk_level = "high"

    risk_multiplier = {"low": risk_low, "medium": risk_med, "high": risk_high}[risk_level]

    # Check for rush keywords
    text_lower = text.lower()
    is_rush = any(w in text_lower for w in ["urgent", "asap", "rush", "24 hours", "immediately"])
    effective_rush = rush_mult if is_rush else 1.0

    base_estimate = max(min_value, estimated_hours * target_rate)
    risk_adjusted = base_estimate * risk_multiplier
    rush_adjusted = risk_adjusted * effective_rush
    platform_fee_buffer = rush_adjusted * 0.1  # 10% platform fee buffer
    recommended_quote = rush_adjusted + platform_fee_buffer

    summary = (
        f"~{estimated_hours}h x ${target_rate}/h = ${base_estimate:.0f} base | "
        f"{risk_level} risk ({risk_multiplier}x) | "
        f"{'rush ' if is_rush else ''}quote: ${recommended_quote:.0f}"
    )

    return {
        "estimated_hours": estimated_hours,
        "base_estimate": base_estimate,
        "risk_adjusted": risk_adjusted,
        "rush_adjusted": rush_adjusted,
        "recommended_quote": recommended_quote,
        "risk_level": risk_level,
        "is_rush": is_rush,
        "summary": summary,
    }
