import re
from typing import Optional


def extract_title_from_text(text: str) -> Optional[str]:
    """Return the first non-empty line as the job title (up to 200 chars)."""
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:200]
    return None


def extract_budget_from_text(text: str) -> tuple[Optional[float], Optional[float]]:
    """Extract a budget or hourly range from job text using simple regex patterns."""
    range_pattern = re.compile(r'\$(\d[\d,]*)\s*[-–]\s*\$(\d[\d,]*)')
    match = range_pattern.search(text)
    if match:
        lo = float(match.group(1).replace(",", ""))
        hi = float(match.group(2).replace(",", ""))
        return lo, hi

    hourly_pattern = re.compile(r'\$(\d[\d,]*)\s*/\s*hr', re.IGNORECASE)
    match = hourly_pattern.search(text)
    if match:
        rate = float(match.group(1).replace(",", ""))
        return rate, None

    return None, None


def extract_client_from_text(text: str) -> Optional[str]:
    """Try to extract a client or company name from common label patterns."""
    pattern = re.compile(
        r'(?:client|company|posted\s+by|from)[:\s]+([A-Za-z][A-Za-z0-9\s&.,\'-]{1,80})',
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if match:
        return match.group(1).strip()[:100]
    return None
