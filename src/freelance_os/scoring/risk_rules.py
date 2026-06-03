"""Risk penalty rules for lead scoring."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from freelance_os.models import Lead


_RISK_RULES: list[tuple[str, int, list[str]]] = [
    # (reason_code, penalty, trigger_keywords)
    ("UNPAID_TEST_REQUEST", 25, ["unpaid test", "free test", "do a test first", "test task for free"]),
    ("BYPASS_PAYMENT_RISK", 25, ["outside upwork", "outside fiverr", "outside the platform", "pay via paypal direct"]),
    ("VAGUE_FIXED_PRICE", 20, ["simple fix", "quick fix", "should be easy", "just a small project"]),
    ("UNREALISTIC_DEADLINE", 20, ["asap", "immediately", "today only", "by end of day", "within 24 hours", "in one day"]),
    ("SUSPICIOUS_BEHAVIOR", 15, ["whatsapp me", "telegram me", "email me directly", "move to email", "text me"]),
    ("SCOPE_CREEP_RISK", 15, ["scope creep", "keep adding", "many revisions", "endless changes"]),
    ("EASY_LANGUAGE", 10, ["easy project", "simple project", "quick project", "should be simple", "should be quick", "just a simple"]),
    ("UNCLEAR_DELIVERABLES", 10, ["not sure what i need", "figure it out", "we'll see", "whatever you think"]),
    ("FREE_CONSULTATION", 10, ["free consultation", "free call first", "discovery call for free"]),
]


def apply_risk_penalties(lead: "Lead") -> tuple[float, list[str]]:
    text = ((lead.description or "") + " " + (lead.title or "")).lower()
    total_penalty = 0.0
    triggered: list[str] = []

    for code, penalty, keywords in _RISK_RULES:
        if any(kw in text for kw in keywords):
            total_penalty += penalty
            triggered.append(code)

    return total_penalty, triggered
