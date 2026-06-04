"""Proposal validator per PRD section 11.3."""

import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from freelance_os.models import ProposalDraft
from freelance_os.proposal.portfolio_matcher import load_portfolio


def _load_banned_phrases(cfg: dict) -> List[str]:
    """Load banned phrases from config/banned_phrases.yaml."""
    p = Path("config/banned_phrases.yaml")
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("phrases", [])
    # Fallback defaults per PRD 11.2
    return [
        "I hope this message finds you well",
        "I am the perfect candidate",
        "I am the ideal candidate",
        "I have extensive experience",
        "I can do this easily",
        "Dear hiring manager",
        "Kindly",
        "Let's connect outside Upwork",
        "Let's connect outside Fiverr",
        "connect outside the platform",
        "communicate outside",
    ]


OFF_PLATFORM_PATTERNS = [
    r"(?:connect|talk|chat|communicate)\s+(?:outside|off)\s+(?:the\s+)?(?:platform|upwork|fiverr|contra)",
    r"(?:email|text|whatsapp|telegram|slack)\s+me\s+(?:directly|instead)",
    r"let.s\s+move\s+(?:this\s+)?(?:off|outside)",
    r"my\s+(?:email|whatsapp|telegram)\s+is",
]

GUARANTEED_OUTCOME_PATTERNS = [
    r"guaranteed?\s+(?:result|outcome|delivery|success)",
    r"100%\s+(?:satisfaction|success|guaranteed)",
    r"will\s+definitely\s+(?:complete|finish|deliver)\s+by",
    r"promise\s+(?:to\s+)?(?:complete|deliver|finish)",
]


def validate_draft(draft: ProposalDraft, cfg: dict) -> Dict:
    """
    Validate proposal draft per PRD 11.3.
    Returns: {"status": "PASS"|"WARN"|"FAIL", "reasons": [...]}
    """
    text = draft.draft_text or ""
    text_lower = text.lower()
    reasons: List[str] = []
    fail = False
    warn = False

    # 1. Banned phrases
    banned = _load_banned_phrases(cfg)
    for phrase in banned:
        if phrase.lower() in text_lower:
            reasons.append(f"FAIL: banned phrase detected: '{phrase}'")
            fail = True

    # 2. Off-platform communication
    for pattern in OFF_PLATFORM_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            reasons.append("FAIL: off-platform communication suggestion detected")
            fail = True
            break

    # 3. Guaranteed outcomes without scope
    for pattern in GUARANTEED_OUTCOME_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            reasons.append("WARN: guaranteed outcome language detected (risky without defined scope)")
            warn = True
            break

    # 4. Missing clarifying question
    has_question = "?" in text
    if not has_question:
        reasons.append("WARN: no clarifying question found (at least one is required)")
        warn = True

    # 5. Check technical diagnosis
    has_diagnosis = bool(draft.technical_diagnosis and len(draft.technical_diagnosis) > 10)
    if not has_diagnosis:
        reasons.append("WARN: no technical diagnosis recorded")
        warn = True

    # 6. Forbidden claims from portfolio
    portfolio = load_portfolio(cfg)
    for item in portfolio:
        forbidden = item.get("forbidden_claims") or []
        for claim in forbidden:
            if claim.lower() in text_lower:
                reasons.append(f"FAIL: unsupported claim: '{claim}'")
                fail = True

    # 7. Minimum length check
    if len(text.split()) < 30:
        reasons.append("WARN: draft is very short (less than 30 words)")
        warn = True

    if fail:
        status = "FAIL"
    elif warn:
        status = "WARN"
    else:
        status = "PASS"

    return {"status": status, "reasons": reasons}
