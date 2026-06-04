"""Risk penalty rules per PRD section 10.2."""

import re
from typing import Dict, List, Optional, Tuple


# (pattern, default_penalty, reason_code, config_key)
RISK_RULES: List[Tuple] = [
    (r"unpaid\s+test|free\s+sample|test\s+task\s+first", 25, "UNPAID_TEST_REQUEST", "unpaid_test_request"),
    (r"bypass\s+platform|outside\s+(?:upwork|fiverr|platform)|off.platform\s+payment", 25, "PAYMENT_RULE_BYPASS", "payment_rule_bypass"),
    (r"simple\s+fix|quick\s+task|easy\s+job|small\s+task", 10, "VAGUE_EASY_LANGUAGE", "easy_language_complex_work"),
    (r"unclear|not\s+sure\s+what|figure\s+out\s+later|TBD", 10, "UNCLEAR_DELIVERABLES", "unclear_deliverables"),
    (r"24\s*hours?|overnight|asap\s+urgent|by\s+tomorrow", 20, "UNREALISTIC_DEADLINE", "unrealistic_deadline"),
    (r"scope\s+creep|keep\s+adding|more\s+features\s+later", 15, "SCOPE_CREEP_RISK", "scope_creep_risk"),
    (r"many\s+revisions|unlimited\s+revision|until\s+(?:i|we)\s+(?:love|like|am happy)", 10, "REVISION_RISK", "unclear_deliverables"),
    (r"free\s+consult|free\s+call\s+first|discovery\s+call\s+before\s+contract", 10, "FREE_CONSULTATION", "free_consultation_request"),
    (r"no\s+budget|budget\s+is\s+(?:low|flexible|tbd|negotiable)\s*\.?\s*$", 15, "PAYMENT_RISK", "suspicious_payment"),
    (
        r"fixed\s+(?:price|budget|rate).*(?:low|cheap|minimal|small\s+budget)|vague.*fixed\s+(?:price|scope)",
        20,
        "VAGUE_FIXED_LOW_BUDGET",
        "vague_fixed_low_budget",
    ),
]


def apply_risk_penalties(
    text: str, penalty_cfg: Optional[Dict[str, int]] = None
) -> Tuple[int, List[str]]:
    """Return (total_penalty, list_of_reason_codes).

    penalty_cfg overrides default penalty values per config key.
    """
    text_lower = text.lower()
    penalty = 0
    codes: List[str] = []
    for pattern, default_points, code, cfg_key in RISK_RULES:
        if re.search(pattern, text_lower):
            points = (
                int(penalty_cfg.get(cfg_key, default_points))
                if penalty_cfg
                else default_points
            )
            penalty += points
            codes.append(code)
    return penalty, codes
