"""Proposal validation — checks for banned phrases, unsupported claims, etc."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from freelance_os.config import load_banned_phrases, load_portfolio

if TYPE_CHECKING:
    from freelance_os.models import Lead, ProposalDraft


_DEFAULT_BANNED_PHRASES = [
    "i hope this message finds you well",
    "i am the perfect candidate",
    "i am the ideal candidate",
    "i have extensive experience",
    "i can do this easily",
    "dear hiring manager",
    "kindly",
    "let's connect outside upwork",
    "let's connect outside fiverr",
    "connect outside the platform",
    "move off platform",
    "contact me on whatsapp",
    "contact me on telegram",
]

_OFF_PLATFORM_PHRASES = [
    "outside upwork",
    "outside fiverr",
    "outside the platform",
    "off platform",
    "whatsapp",
    "telegram",
    "email me directly",
    "text me at",
]


@dataclass
class ValidationResult:
    status: str  # PASS, WARN, FAIL
    flags: list[str] = field(default_factory=list)


def validate_draft(draft: "ProposalDraft", lead: "Lead") -> ValidationResult:
    flags: list[str] = []
    is_fail = False
    is_warn = False

    text = (draft.draft_text or "").lower()

    # Load banned phrases from config, fall back to defaults
    banned = load_banned_phrases()
    if not banned:
        banned = _DEFAULT_BANNED_PHRASES

    for phrase in banned:
        if phrase.lower() in text:
            flags.append(f"BANNED_PHRASE: '{phrase}'")
            is_fail = True

    # Check off-platform language
    for phrase in _OFF_PLATFORM_PHRASES:
        if phrase in text:
            flags.append(f"OFF_PLATFORM_LANGUAGE: '{phrase}'")
            is_fail = True

    # Check for clarifying question
    has_question = "?" in (draft.draft_text or "")
    clarifying = draft.clarifying_questions or ""
    if not has_question and not clarifying:
        flags.append("WARN: Missing clarifying question")
        is_warn = True

    # Check for technical diagnosis
    diagnosis = draft.technical_diagnosis or ""
    if len(diagnosis.strip()) < 20:
        flags.append("WARN: Technical diagnosis is missing or too brief")
        is_warn = True

    # Check unsupported portfolio claims
    portfolio = load_portfolio()
    claim_flags = _check_unsupported_claims(draft.draft_text or "", portfolio)
    for cf in claim_flags:
        flags.append(f"UNSUPPORTED_CLAIM: {cf}")
        is_warn = True

    # Guaranteed timeline without scope
    draft_text = draft.draft_text or ""
    if _has_guaranteed_timeline(draft_text):
        flags.append("WARN: Contains guaranteed timeline without scope confirmation")
        is_warn = True

    if is_fail:
        status = "FAIL"
    elif is_warn:
        status = "WARN"
    else:
        status = "PASS"

    return ValidationResult(status=status, flags=flags)


def _check_unsupported_claims(text: str, portfolio: list[dict]) -> list[str]:
    forbidden_flags = []
    text_lower = text.lower()

    for item in portfolio:
        forbidden = item.get("forbidden_claims", [])
        if isinstance(forbidden, list):
            for claim in forbidden:
                if claim.lower() in text_lower:
                    forbidden_flags.append(claim)

    return forbidden_flags


def _has_guaranteed_timeline(text: str) -> bool:
    phrases = [
        "i will deliver in",
        "i can finish in",
        "guaranteed within",
        "done in 24 hours",
        "done in one day",
        "done by tomorrow",
    ]
    lower = text.lower()
    return any(p in lower for p in phrases)
