"""Deterministic feasibility estimator — category + keyword heuristics, no LLM."""

import math
import re
from typing import Dict, Tuple

from freelance_os.models import JobCategory, Lead

# Base effort range (hours_low, hours_high) per category
_BASE_EFFORT: Dict[str, Tuple[int, int]] = {
    JobCategory.BUG_FIX.value:        (2, 8),
    JobCategory.SCRAPING_DATA.value:  (4, 16),
    JobCategory.DATA_DASHBOARD.value: (8, 24),
    JobCategory.WORDPRESS.value:      (4, 16),
    JobCategory.AI_AUTOMATION.value:  (8, 32),
    JobCategory.WEB_APP.value:        (16, 60),
    JobCategory.OTHER.value:          (20, 80),
}

# warren_feasible = True when effort_high <= cap AND confidence >= MED
_WARREN_CAP: Dict[str, int] = {
    JobCategory.BUG_FIX.value:        8,
    JobCategory.SCRAPING_DATA.value:  20,
    JobCategory.DATA_DASHBOARD.value: 24,
    JobCategory.WORDPRESS.value:      16,
    JobCategory.AI_AUTOMATION.value:  32,
    JobCategory.WEB_APP.value:        20,
}

# Base confidence level per category (0=LOW, 1=MED, 2=HIGH)
_BASE_CONF: Dict[str, int] = {
    JobCategory.BUG_FIX.value:        2,
    JobCategory.SCRAPING_DATA.value:  2,
    JobCategory.DATA_DASHBOARD.value: 2,
    JobCategory.WORDPRESS.value:      2,
    JobCategory.AI_AUTOMATION.value:  1,
    JobCategory.WEB_APP.value:        1,
    JobCategory.OTHER.value:          0,
}

_CONF_LABEL = {0: "LOW", 1: "MED", 2: "HIGH"}

_SMALL_SCOPE_PATTERNS = [
    r"landing\s+page", r"\bsimple\b", r"one[\s-]page", r"single[\s-]page",
    r"\bsmall\b", r"quick\s+fix", r"\bpatch\b", r"\bbasic\b",
    r"\bprototype\b", r"\bwireframe\b", r"\bminor\b", r"\btweak\b",
    r"add\s+\w+\s+feature", r"small\s+script",
]

_LARGE_SCOPE_PATTERNS = [
    r"\benterprise\b", r"\bcomplex\b", r"from\s+scratch",
    r"full[\s-](stack|platform|application|system)",
    r"\bcomprehensive\b", r"\barchitecture\b", r"\bscalable\b",
    r"multiple\s+(pages?|features?|modules?)", r"\bvarious\b",
    r"end[\s-]to[\s-]end",
]

_CLEAR_SCOPE_PATTERNS = [
    r"\bdeliver\b", r"\boutcome\b", r"\bmilestone\b", r"\brequirement\b",
    r"\bfeature\b", r"\bphase\b", r"\bspecif\b", r"\bapi\s+endpoint",
    r"\btest\s+coverage\b",
]


def estimate_feasibility(lead: Lead, cfg: dict) -> dict:
    """
    Return feasibility estimate dict for a lead.

    Keys: effort_hours_low, effort_hours_high, feasibility_confidence (LOW/MED/HIGH),
          warren_feasible (bool), suggested_price (float), suggested_turnaround_days (int).
    """
    scoring_cfg = cfg.get("scoring", {})
    target_rate = float(scoring_cfg.get("target_hourly_rate", 75))
    min_value = float(scoring_cfg.get("minimum_project_value", 300))
    discount = float(scoring_cfg.get("quick_win_discount", 0.85))

    category = (lead.category or JobCategory.OTHER.value).upper()
    if category not in _BASE_EFFORT:
        category = JobCategory.OTHER.value

    base_low, base_high = _BASE_EFFORT[category]
    text = " ".join(filter(None, [lead.title, lead.description])).lower()

    small_hits = sum(1 for p in _SMALL_SCOPE_PATTERNS if re.search(p, text))
    large_hits = sum(1 for p in _LARGE_SCOPE_PATTERNS if re.search(p, text))
    clear_hits = sum(1 for p in _CLEAR_SCOPE_PATTERNS if re.search(p, text))

    # Scope modifier
    if small_hits >= 1 and large_hits == 0:
        scope_factor = 0.6
    elif large_hits >= 2 or (large_hits >= 1 and small_hits == 0):
        scope_factor = 1.5
    else:
        scope_factor = 1.0

    effort_low = max(1, round(base_low * scope_factor))
    effort_high = max(effort_low + 1, round(base_high * scope_factor))

    # Confidence
    conf = _BASE_CONF.get(category, 0)
    if large_hits >= 2:
        conf = max(0, conf - 1)
    if clear_hits >= 2:
        conf = min(2, conf + 1)
    word_count = len(text.split()) if text.strip() else 0
    if word_count < 30:
        conf = max(0, conf - 1)
    feasibility_confidence = _CONF_LABEL[conf]

    # Warren feasibility
    cap = _WARREN_CAP.get(category)
    if cap is None:
        warren_feasible = False
    else:
        warren_feasible = effort_high <= cap and feasibility_confidence in ("MED", "HIGH")

    # Suggested price: effort_high * rate * quick-win discount, at least min_value
    raw_price = effort_high * target_rate * discount
    suggested_price = round(max(min_value, raw_price), 2)

    # Turnaround: 6 productive hours/day
    suggested_turnaround_days = max(1, math.ceil(effort_high / 6))

    return {
        "effort_hours_low": effort_low,
        "effort_hours_high": effort_high,
        "feasibility_confidence": feasibility_confidence,
        "warren_feasible": warren_feasible,
        "suggested_price": suggested_price,
        "suggested_turnaround_days": suggested_turnaround_days,
    }
