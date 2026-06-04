"""Manual lead intake: add-url and add-text."""

import re
from typing import Optional

from sqlmodel import Session

from freelance_os.db import get_engine
from freelance_os.ingestion.classify import classify_lead
from freelance_os.models import Lead, LeadStatus


def _extract_title(text: str) -> Optional[str]:
    """Heuristically extract a title from raw job text."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines:
        return lines[0][:200]
    return None


def _extract_budget(text: str) -> dict:
    """Parse budget hints from raw text."""
    result = {}
    # Hourly rate pattern: $50-$100/hr or $75/hour
    hourly = re.search(r"\$(\d+)\s*[-–]\s*\$(\d+)\s*/\s*h", text, re.IGNORECASE)
    if hourly:
        result["budget_type"] = "hourly"
        result["hourly_min"] = float(hourly.group(1))
        result["hourly_max"] = float(hourly.group(2))
    else:
        single_hourly = re.search(r"\$(\d+)\s*/\s*(?:hr|hour)", text, re.IGNORECASE)
        if single_hourly:
            result["budget_type"] = "hourly"
            result["hourly_min"] = float(single_hourly.group(1))

    # Fixed budget: $500 - $2000 or Budget: $1500
    fixed = re.search(r"\$(\d+)\s*[-–]\s*\$(\d+)", text)
    if fixed and "budget_type" not in result:
        result["budget_type"] = "fixed"
        result["budget_min"] = float(fixed.group(1))
        result["budget_max"] = float(fixed.group(2))

    return result


def add_lead_url(url: str, description: Optional[str], cfg: dict) -> Lead:
    """Create a lead from a URL, optionally with a pasted description."""
    budget_hints = _extract_budget(description or "")
    title = _extract_title(description or "") if description else None
    category = classify_lead(description or "")

    lead = Lead(
        source="manual_url",
        source_url=url,
        title=title,
        description=description,
        status=LeadStatus.NEW,
        category=category,
        **budget_hints,
    )
    engine = get_engine(cfg["paths"]["database_path"])
    with Session(engine) as session:
        session.add(lead)
        session.commit()
        session.refresh(lead)
    return lead


def add_lead_text(source: str, text: str, cfg: dict) -> Lead:
    """Create a lead from pasted text."""
    budget_hints = _extract_budget(text)
    title = _extract_title(text)
    category = classify_lead(text)

    lead = Lead(
        source=source,
        description=text,
        title=title,
        status=LeadStatus.NEW,
        category=category,
        **budget_hints,
    )
    engine = get_engine(cfg["paths"]["database_path"])
    with Session(engine) as session:
        session.add(lead)
        session.commit()
        session.refresh(lead)
    return lead
