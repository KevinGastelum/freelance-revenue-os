"""Portfolio matching — finds best portfolio items for a lead."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from freelance_os.config import load_portfolio

if TYPE_CHECKING:
    from freelance_os.models import Lead


def find_matches(lead: "Lead", portfolio: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if portfolio is None:
        portfolio = load_portfolio()

    if not portfolio:
        return []

    text = ((lead.description or "") + " " + (lead.title or "")).lower()
    scored: list[tuple[int, dict[str, Any]]] = []

    for item in portfolio:
        tags = item.get("tags", [])
        if isinstance(tags, list):
            match_count = sum(1 for tag in tags if tag.lower() in text)
        else:
            match_count = 0
        scored.append((match_count, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored if score > 0]
