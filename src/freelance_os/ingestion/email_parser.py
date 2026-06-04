"""Email alert parser stub per PRD section 9.3.

MVP: reads exported .eml or pasted email text (no automated login).
"""

import re
from pathlib import Path
from typing import Dict, Optional


def parse_email_text(text: str) -> Dict[str, Optional[str]]:
    """
    Extract lead fields from pasted or exported email alert text.
    Returns a dict suitable for Lead creation.
    """
    result: Dict[str, Optional[str]] = {
        "title": None,
        "description": None,
        "source_url": None,
        "budget_type": None,
        "budget_min": None,
        "budget_max": None,
    }

    # Extract subject/title from email headers
    subject_match = re.search(r"^Subject:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    if subject_match:
        result["title"] = subject_match.group(1).strip()[:200]

    # Extract URLs that look like job postings
    urls = re.findall(r"https?://(?:www\.)?(?:upwork\.com|fiverr\.com|contra\.com)[^\s\"'<>]+", text)
    if urls:
        result["source_url"] = urls[0]

    # Extract budget hints
    hourly = re.search(r"\$(\d+)\s*[-–]\s*\$(\d+)\s*/\s*h", text, re.IGNORECASE)
    if hourly:
        result["budget_type"] = "hourly"
        result["budget_min"] = float(hourly.group(1))
        result["budget_max"] = float(hourly.group(2))

    # Use the body as description (strip headers)
    body_start = text.find("\n\n")
    if body_start > 0:
        result["description"] = text[body_start:].strip()[:2000]
    else:
        result["description"] = text[:2000]

    return result


def parse_eml_file(path: str) -> Dict[str, Optional[str]]:
    """Parse a .eml file and extract lead fields."""
    content = Path(path).read_text(encoding="utf-8", errors="replace")
    return parse_email_text(content)
