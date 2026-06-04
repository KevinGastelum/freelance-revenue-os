"""Platform source directory loader and filter."""

from pathlib import Path
from typing import List, Optional

import yaml


def load_sources(config_dir: str = "config") -> List[dict]:
    """Load platform sources from sources.yaml, falling back to sources.example.yaml."""
    for name in ("sources.yaml", "sources.example.yaml"):
        path = Path(config_dir) / name
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data.get("sources", []) if isinstance(data, dict) else []
    return []


def filter_sources(
    sources: List[dict],
    category: Optional[str] = None,
    newcomer: bool = False,
    region: Optional[str] = None,
) -> List[dict]:
    """Filter sources list by optional criteria."""
    result = sources
    if category:
        cat_upper = category.upper()
        result = [s for s in result if cat_upper in [c.upper() for c in s.get("categories", [])]]
    if newcomer:
        result = [s for s in result if s.get("newcomer_friendly", False)]
    if region:
        result = [s for s in result if (s.get("region") or "").lower() == region.lower()]
    return result
