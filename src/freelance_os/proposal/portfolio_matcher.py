"""Match job descriptions against portfolio items."""

import yaml
from pathlib import Path
from typing import Dict, List, Optional


def load_portfolio(cfg: dict) -> List[Dict]:
    """Load portfolio items from YAML file."""
    portfolio_path = Path(cfg["paths"].get("portfolio_file", "config/portfolio.yaml"))
    if not portfolio_path.exists():
        return []
    with open(portfolio_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("items", [])


def match_portfolio(text: str, cfg: dict) -> List[Dict]:
    """Return portfolio items relevant to the given text."""
    items = load_portfolio(cfg)
    text_lower = text.lower()
    matched = []
    for item in items:
        tags = item.get("tags", []) or []
        name = (item.get("name") or "").lower()
        desc = (item.get("description") or "").lower()
        if any(tag.lower() in text_lower for tag in tags):
            matched.append(item)
        elif name in text_lower or any(word in text_lower for word in desc.split() if len(word) > 4):
            matched.append(item)
    return matched


def get_best_proof_point(matches: List[Dict]) -> str:
    """Return a representative proof point from matched portfolio items."""
    for item in matches:
        proof_points = item.get("proof_points") or []
        if proof_points:
            return proof_points[0]
    return "full-stack applications with backend APIs and database integration"


def get_project_reference(matches: List[Dict]) -> str:
    """Return a project reference string."""
    if matches:
        return matches[0].get("name", "relevant projects")
    return "relevant projects in this domain"
