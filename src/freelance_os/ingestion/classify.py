"""Deterministic keyword classifier for job leads (no LLM)."""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from freelance_os.models import JobCategory

_RULES = [
    ("WEB_APP", [
        r"next\.?js", r"next\s+js", r"\breact\b", r"supabase", r"vercel",
        r"\bvue\.?js?\b", r"\bnuxt\b", r"\bsvelte\b", r"tailwind",
        r"typescript\s+frontend", r"\bremix\b", r"\bastro\b",
    ]),
    ("DATA_DASHBOARD", [
        r"power\s?bi", r"\bdax\b", r"\betl\b", r"\bdashboard\b", r"\banalytics\b",
        r"\bkpi\b", r"\btableau\b", r"\blooker\b", r"data\s+visuali",
        r"google\s+data\s+studio", r"\breporting\b",
    ]),
    ("SCRAPING_DATA", [
        r"\bscrape\b", r"\bscraper\b", r"\bscraping\b", r"\bcrawl\b", r"\bcrawler\b",
        r"data\s+pipeline", r"web\s+scraping", r"extract\s+data",
    ]),
    ("AI_AUTOMATION", [
        r"\bai\b", r"\bllm\b", r"\bchatbot\b", r"\bautomation\b",
        r"api\s+integration", r"\bagent\b", r"\bgpt\b", r"\bopenai\b",
        r"\blangchain\b", r"machine\s+learning", r"\bml\b",
    ]),
    ("WORDPRESS", [
        r"\bwordpress\b", r"\bwoocommerce\b", r"\belementor\b", r"\bwp\b",
        r"\bdivi\b", r"\bgutenberg\b",
    ]),
    ("BUG_FIX", [
        r"\bbug\b", r"\bfix\b", r"small\s+change", r"\bhotfix\b", r"\bpatch\b",
        r"not\s+working", r"\bbroken\b",
    ]),
]


def classify_lead(text: str) -> str:
    """Return the JobCategory value string for the given job description text."""
    lowered = text.lower()
    for category_value, patterns in _RULES:
        for pattern in patterns:
            if re.search(pattern, lowered):
                return category_value
    return "OTHER"
