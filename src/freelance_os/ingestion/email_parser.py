"""Email alert parser for freelance job-alert emails (no LLM, no scraping).

Supports .eml files, .mbox files, and raw pasted/stdin text. Extracts job
leads from Upwork, Fiverr, Freelancer, PeoplePerHour, Workana, Freelancehunt.
No automated login, authenticated scraping, or platform write actions.
"""

import email as _email
import mailbox
import re
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Source detection
# ---------------------------------------------------------------------------

_SOURCE_DOMAIN_MAP: Dict[str, str] = {
    "upwork.com": "upwork",
    "fiverr.com": "fiverr",
    "freelancer.com": "freelancer",
    "peopleperhour.com": "peopleperhour",
    "workana.com": "workana",
    "freelancehunt.com": "freelancehunt",
}


def detect_source(from_header: str, body: str = "") -> str:
    """Detect source platform from email From header; fall back to body URLs."""
    from_lower = from_header.lower()
    for domain, source in _SOURCE_DOMAIN_MAP.items():
        if domain in from_lower:
            return source
    body_lower = body.lower()
    for domain, source in _SOURCE_DOMAIN_MAP.items():
        if domain in body_lower:
            return source
    return "email"


# ---------------------------------------------------------------------------
# Text extraction from email.Message
# ---------------------------------------------------------------------------

def _get_plain_text(msg: _email.message.Message) -> str:
    """Extract plain-text body from an email.Message (handles multipart)."""
    parts: List[str] = []
    if msg.is_multipart():
        for part in msg.walk():
            if (
                part.get_content_type() == "text/plain"
                and part.get_content_disposition() != "attachment"
            ):
                charset = part.get_content_charset() or "utf-8"
                raw = part.get_payload(decode=True)
                if raw:
                    parts.append(raw.decode(charset, errors="replace"))
    else:
        charset = msg.get_content_charset() or "utf-8"
        raw = msg.get_payload(decode=True)
        if raw:
            parts.append(raw.decode(charset, errors="replace"))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Budget extraction
# ---------------------------------------------------------------------------

_HOURLY_RANGE = re.compile(
    r"\$\s*(\d+(?:\.\d+)?)\s*[-–]\s*\$\s*(\d+(?:\.\d+)?)\s*/\s*h(?:r|our)?",
    re.IGNORECASE,
)
_SINGLE_HOURLY = re.compile(r"\$\s*(\d+(?:\.\d+)?)\s*/\s*(?:hr|hour)", re.IGNORECASE)
_FIXED_RANGE = re.compile(
    r"\$\s*(\d[\d,]*)\s*[-–]\s*\$\s*(\d[\d,]*)"
)
_FIXED_SINGLE = re.compile(
    r"(?:budget|fixed)[:\s]+\$\s*(\d[\d,]*)", re.IGNORECASE
)


def _parse_budget(text: str) -> dict:
    m = _HOURLY_RANGE.search(text)
    if m:
        return {"budget_type": "hourly",
                "hourly_min": float(m.group(1)),
                "hourly_max": float(m.group(2))}
    m = _SINGLE_HOURLY.search(text)
    if m:
        return {"budget_type": "hourly", "hourly_min": float(m.group(1))}
    m = _FIXED_RANGE.search(text)
    if m:
        return {"budget_type": "fixed",
                "budget_min": float(m.group(1).replace(",", "")),
                "budget_max": float(m.group(2).replace(",", ""))}
    m = _FIXED_SINGLE.search(text)
    if m:
        return {"budget_type": "fixed",
                "budget_min": float(m.group(1).replace(",", ""))}
    return {}


# ---------------------------------------------------------------------------
# URL extraction
# ---------------------------------------------------------------------------

_JOB_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:"
    r"upwork\.com/jobs/[^\s\"'<>\[\])]+|"
    r"freelancer\.com/projects/[^\s\"'<>\[\])]+|"
    r"fiverr\.com/[^\s\"'<>\[\])]+|"
    r"peopleperhour\.com/[^\s\"'<>\[\])]+|"
    r"workana\.com/[^\s\"'<>\[\])]+|"
    r"freelancehunt\.com/[^\s\"'<>\[\])]+"
    r")",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Section splitter and title heuristic
# ---------------------------------------------------------------------------

def _split_sections(body: str) -> List[str]:
    """Split email body on 2+ blank lines or horizontal rules."""
    parts = re.split(r"\n{3,}|\n[ \t]*[-=_]{3,}[ \t]*\n", body)
    return [p.strip() for p in parts if len(p.strip()) >= 30]


def _is_title_line(line: str) -> bool:
    line = line.strip()
    if len(line) < 8 or len(line) > 200:
        return False
    if "http" in line.lower() or line.startswith(">") or "@" in line:
        return False
    if re.match(r"^[-=_*#|]+$", line):
        return False
    # Lines ending with ":" are section headers (e.g. "New Buyer Request:"), not titles
    if line.endswith(":"):
        return False
    words = line.split()
    return len(words) >= 2 and any(c.isalpha() for c in line)


def _extract_jobs_from_sections(sections: List[str], source: str) -> List[Dict]:
    jobs: List[Dict] = []
    for section in sections:
        lines = [l.strip() for l in section.splitlines() if l.strip()]
        if not lines:
            continue

        urls = _JOB_URL_RE.findall(section)
        job_url: Optional[str] = urls[0] if urls else None

        # Refine source from URL if still generic
        if source == "email" and job_url:
            for domain, src in _SOURCE_DOMAIN_MAP.items():
                if domain in job_url.lower():
                    source = src
                    break

        title: Optional[str] = None
        for line in lines:
            if _is_title_line(line):
                title = line[:200]
                break

        if not title and not job_url:
            continue

        budget = _parse_budget(section)
        desc_lines = [
            l for l in lines
            if not l.startswith("http") and len(l) > 5
        ]
        description = "\n".join(desc_lines[:15])[:2000]

        jobs.append({
            "source": source,
            "title": title,
            "source_url": job_url,
            "description": description,
            **budget,
        })
    return jobs


# ---------------------------------------------------------------------------
# Core message parser
# ---------------------------------------------------------------------------

def _parse_message(
    msg: _email.message.Message,
    source_override: Optional[str] = None,
) -> List[Dict]:
    from_header = msg.get("From", "")
    subject = msg.get("Subject", "")
    body = _get_plain_text(msg)

    source = source_override or detect_source(from_header, body)

    sections = _split_sections(body)
    jobs = _extract_jobs_from_sections(sections, source)

    # Fallback: treat whole body as one job when no sections detected
    if not jobs:
        urls = _JOB_URL_RE.findall(body)
        budget = _parse_budget(body)
        lines = [l.strip() for l in body.splitlines() if l.strip() and len(l.strip()) > 8]
        # Use subject as title when body offers no better candidate
        title = subject[:200] if subject else (lines[0][:200] if lines else None)
        jobs.append({
            "source": source,
            "title": title,
            "source_url": urls[0] if urls else None,
            "description": body[:2000],
            **budget,
        })

    # Fill missing titles with subject as fallback
    for job in jobs:
        if not job.get("title") and subject:
            job["title"] = subject[:200]

    return jobs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_eml_file(
    path: "str | Path",
    source_override: Optional[str] = None,
) -> List[Dict]:
    """Parse a .eml file; return list of job lead dicts."""
    content = Path(path).read_bytes()
    msg = _email.message_from_bytes(content)
    return _parse_message(msg, source_override)


def parse_mbox_file(
    path: "str | Path",
    source_override: Optional[str] = None,
) -> List[Dict]:
    """Parse a .mbox file; return job lead dicts from all messages."""
    jobs: List[Dict] = []
    mbox = mailbox.mbox(str(path))
    try:
        for msg in mbox:
            jobs.extend(_parse_message(msg, source_override))
    finally:
        mbox.close()
    return jobs


def parse_raw_text(
    text: str,
    source_override: Optional[str] = None,
) -> List[Dict]:
    """Parse raw email text (pasted or stdin); return job lead dicts."""
    try:
        msg = _email.message_from_string(text)
        if msg.get("From") or msg.get("Subject"):
            return _parse_message(msg, source_override)
    except Exception:
        pass

    # Plain body text (no headers)
    source = source_override or detect_source("", text)
    sections = _split_sections(text)
    jobs = _extract_jobs_from_sections(sections, source)
    if not jobs:
        urls = _JOB_URL_RE.findall(text)
        budget = _parse_budget(text)
        lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 8]
        title = lines[0][:200] if lines else None
        jobs.append({
            "source": source,
            "title": title,
            "source_url": urls[0] if urls else None,
            "description": text[:2000],
            **budget,
        })
    return jobs


def parse_email_text(text: str) -> Dict:
    """Parse email text; return first lead dict (legacy backward-compat API)."""
    results = parse_raw_text(text)
    if results:
        return results[0]
    return {
        "title": None,
        "description": text[:2000],
        "source_url": None,
        "budget_type": None,
        "budget_min": None,
        "budget_max": None,
    }
