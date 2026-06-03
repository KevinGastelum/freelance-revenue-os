"""Manual lead ingestion — URL and text intake."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from sqlmodel import Session

from freelance_os.db import get_engine, init_db
from freelance_os.models import Lead, LeadStatus


def _extract_title(text: str) -> Optional[str]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return lines[0][:200] if lines else None


def add_lead_by_url(
    url: str,
    description: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> Lead:
    init_db(db_path)
    engine = get_engine(db_path)

    with Session(engine) as session:
        lead = Lead(
            source="manual_url",
            source_url=url,
            title=_extract_title(description) if description else url[:200],
            description=description,
            status=LeadStatus.NEW,
        )
        session.add(lead)
        session.commit()
        session.refresh(lead)
        return lead


def add_lead_by_text(
    source: str,
    text: str,
    db_path: Optional[Path] = None,
) -> Lead:
    init_db(db_path)
    engine = get_engine(db_path)

    budget_min, budget_max = _parse_budget(text)

    with Session(engine) as session:
        lead = Lead(
            source=source,
            title=_extract_title(text),
            description=text,
            budget_min=budget_min,
            budget_max=budget_max,
            status=LeadStatus.NEW,
        )
        session.add(lead)
        session.commit()
        session.refresh(lead)
        return lead


def _parse_budget(text: str) -> tuple[Optional[float], Optional[float]]:
    pattern = r"\$(\d[\d,]*)\s*[-–]\s*\$(\d[\d,]*)"
    match = re.search(pattern, text)
    if match:
        lo = float(match.group(1).replace(",", ""))
        hi = float(match.group(2).replace(",", ""))
        return lo, hi
    single = re.search(r"\$(\d[\d,]+)", text)
    if single:
        val = float(single.group(1).replace(",", ""))
        return val, val
    return None, None
