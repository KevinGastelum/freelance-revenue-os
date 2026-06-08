"""Normalizer for operator-sourced lead data (CSV / JSON) → pull lead-dict schema.

This is intentionally separate from ingestion/import_csv.py, which maps to the
Lead SQLModel for the old `lead import` pipeline. This module targets the margin
lead-dict schema used by `pull` and `ingest`.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from freelance_os.ingestion.pull import _empty_lead, _parse_salary_string, _parse_iso, dedupe_leads

# Field aliases — first match in a row wins (all compared case-insensitively).
_URL_ALIASES = ("url", "link", "job_url", "job_link")
_DESC_ALIASES = ("description", "desc", "body", "details", "summary")
_BUDGET_ALIASES = ("budget", "rate", "salary", "pay", "compensation", "price")
_SKILLS_ALIASES = ("skills", "tags", "keywords", "technologies")
_DATE_ALIASES = ("posted_at", "posted_date", "date", "published_at", "created_at")
_COUNTRY_ALIASES = ("client_country", "country", "client.country")
_RATING_ALIASES = ("client_rating", "rating", "client.rating")
_HIRES_ALIASES = ("hires", "client_hires", "client.hires", "total_hires")
_PV_ALIASES = ("payment_verified", "client_payment_verified", "client.payment_verified", "verified")
_SPEND_ALIASES = ("total_spend", "client_total_spend", "client.total_spend")


def _pick(row: Dict[str, Any], aliases: tuple, default=None):
    """Return the first non-empty value from row matching any alias (case-insensitive)."""
    lower = {k.lower(): v for k, v in row.items()}
    for alias in aliases:
        if alias in lower:
            val = lower[alias]
            if val not in (None, ""):
                return val
    return default


def _parse_skills(raw) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(s).strip() for s in raw if s]
    return [s.strip() for s in str(raw).split(",") if s.strip()]


def _parse_bool(raw) -> bool:
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        return raw.lower() in ("1", "true", "yes", "y", "remote")
    return bool(raw)


def _is_already_normalized(row: Dict[str, Any]) -> bool:
    """True if the row already carries the pull lead-dict structure (budget is a dict)."""
    budget = row.get("budget")
    return (
        isinstance(budget, dict)
        and "amount" in budget
        and "currency" in budget
        and "type" in budget
    )


def _normalize_row(row: Dict[str, Any], default_source: str) -> Optional[Dict[str, Any]]:
    """Normalize a raw row to the pull lead-dict schema.

    Returns None if the row has no title AND no description (nothing to score).
    Rows already in lead-dict shape (budget is a dict) pass through with defaults filled.
    """
    if _is_already_normalized(row):
        lead = dict(row)
        if not lead.get("source"):
            lead["source"] = default_source
        return lead

    title = str(_pick(row, ("title",), "") or "").strip()
    description = str(_pick(row, _DESC_ALIASES, "") or "").strip()

    if not title and not description:
        return None

    url = str(_pick(row, _URL_ALIASES, "") or "").strip()
    source_raw = _pick(row, ("source",))
    source = str(source_raw).strip() if source_raw else default_source

    lead = _empty_lead(source=source, url=url, title=title, description=description)

    # Budget: parse a string or bare number
    budget_raw = _pick(row, _BUDGET_ALIASES)
    if budget_raw is not None:
        if isinstance(budget_raw, (int, float)):
            lead["budget"] = {"amount": float(budget_raw), "currency": "USD", "type": "fixed"}
        else:
            lead["budget"] = _parse_salary_string(str(budget_raw))

    # Skills
    lead["skills"] = _parse_skills(_pick(row, _SKILLS_ALIASES))

    # Posted date
    date_raw = _pick(row, _DATE_ALIASES)
    lead["posted_at"] = _parse_iso(str(date_raw)) if date_raw else None

    # Client sub-fields
    client: Dict[str, Any] = {}
    country = _pick(row, _COUNTRY_ALIASES)
    if country:
        client["country"] = str(country)
    rating = _pick(row, _RATING_ALIASES)
    if rating is not None:
        try:
            client["rating"] = float(rating)
        except (TypeError, ValueError):
            pass
    hires = _pick(row, _HIRES_ALIASES)
    if hires is not None:
        try:
            client["hires"] = int(hires)
        except (TypeError, ValueError):
            pass
    pv = _pick(row, _PV_ALIASES)
    if pv is not None:
        client["payment_verified"] = _parse_bool(pv)
    ts = _pick(row, _SPEND_ALIASES)
    if ts is not None:
        try:
            client["total_spend"] = float(str(ts).replace(",", "").replace("$", ""))
        except (TypeError, ValueError):
            pass
    lead["client"] = client

    location = _pick(row, ("location",))
    if location:
        lead["location"] = str(location)

    remote_raw = _pick(row, ("remote",))
    if remote_raw is not None:
        lead["remote"] = _parse_bool(remote_raw)

    return lead


def _detect_format(path: Path, fmt: str) -> str:
    if fmt != "auto":
        return fmt.lower()
    suffix = path.suffix.lower()
    if suffix in (".json", ".jsonl"):
        return "json"
    return "csv"  # default for .csv or unknown extensions


def _load_csv(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return [dict(row) for row in reader]


def _load_json(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "leads" in data:
        return data["leads"]
    return [data]


def load_leads(path, fmt: str = "auto") -> List[Dict[str, Any]]:
    """Load and normalize leads from a CSV or JSON file.

    Args:
        path: Path to the file (str or pathlib.Path).
        fmt:  "csv", "json", or "auto" (detect by file extension).

    Returns:
        List of lead dicts matching the pull schema, deduped by URL.
    """
    p = Path(path)
    detected = _detect_format(p, fmt)
    default_source = f"ingest:{p.name}"

    raw_rows = _load_json(p) if detected == "json" else _load_csv(p)

    leads = []
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        lead = _normalize_row(row, default_source)
        if lead is not None:
            leads.append(lead)

    return dedupe_leads(leads)
