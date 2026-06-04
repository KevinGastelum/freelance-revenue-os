"""Risk penalty rules per PRD section 10.2."""

import re
from typing import Dict, List, Tuple


# (pattern_or_callable, penalty_points, reason_code)
RISK_RULES: List[Tuple] = [
    (r"unpaid\s+test|free\s+sample|test\s+task\s+first", 25, "UNPAID_TEST_REQUEST"),
    (r"bypass\s+platform|outside\s+(?:upwork|fiverr|platform)|off.platform\s+payment", 25, "PAYMENT_RULE_BYPASS"),
    (r"simple\s+fix|quick\s+task|easy\s+job|small\s+task", 10, "VAGUE_EASY_LANGUAGE"),
    (r"unclear|not\s+sure\s+what|figure\s+out\s+later|TBD", 10, "UNCLEAR_DELIVERABLES"),
    (r"24\s*hours?|overnight|asap\s+urgent|by\s+tomorrow", 20, "UNREALISTIC_DEADLINE"),
    (r"scope\s+creep|keep\s+adding|more\s+features\s+later", 15, "SCOPE_CREEP_RISK"),
    (r"many\s+revisions|unlimited\s+revision|until\s+(?:i|we)\s+(?:love|like|am happy)", 10, "REVISION_RISK"),
    (r"free\s+consult|free\s+call\s+first|discovery\s+call\s+before\s+contract", 10, "FREE_CONSULTATION"),
    (r"no\s+budget|budget\s+is\s+(?:low|flexible|tbd|negotiable)\s*\.?\s*$", 15, "PAYMENT_RISK"),
]


def apply_risk_penalties(text: str) -> Tuple[int, List[str]]:
    """Return (total_penalty, list_of_reason_codes)."""
    text_lower = text.lower()
    penalty = 0
    codes: List[str] = []
    for pattern, points, code in RISK_RULES:
        if re.search(pattern, text_lower):
            penalty += points
            codes.append(code)
    return penalty, codes
