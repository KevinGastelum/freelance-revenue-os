"""CSV/JSON import for leads per PRD section 9.4.

Allows importing leads from exported CSV or JSON files (no scraping).
"""

import csv
import json
from pathlib import Path
from typing import Dict, List


FIELD_MAP = {
    "url": "source_url",
    "link": "source_url",
    "job_url": "source_url",
    "title": "title",
    "description": "description",
    "desc": "description",
    "client": "client_name",
    "client_name": "client_name",
    "budget": "budget_max",
    "budget_max": "budget_max",
    "budget_min": "budget_min",
    "rate": "hourly_max",
    "hourly": "hourly_max",
    "country": "country",
    "notes": "notes",
    "source": "source",
}


def _normalize_row(row: Dict) -> Dict:
    """Normalize CSV/JSON row keys to Lead field names."""
    normalized = {}
    for key, value in row.items():
        mapped = FIELD_MAP.get(key.lower().strip())
        if mapped and value:
            normalized[mapped] = value
    return normalized


def import_from_csv(path: str) -> List[Dict]:
    """Read leads from a CSV file. Returns list of dicts for Lead creation."""
    p = Path(path)
    rows = []
    with open(p, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(_normalize_row(dict(row)))
    return rows


def import_from_json(path: str) -> List[Dict]:
    """Read leads from a JSON file (list of objects). Returns list of dicts."""
    p = Path(path)
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("leads", [data])
    return [_normalize_row(row) for row in data if isinstance(row, dict)]
