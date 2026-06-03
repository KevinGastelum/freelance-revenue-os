"""Text utilities."""

import re


def slugify(text: str, max_len: int = 40) -> str:
    """Convert text to a lowercase URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:max_len]


def truncate(text: str, length: int = 80, suffix: str = "...") -> str:
    if len(text) <= length:
        return text
    return text[: length - len(suffix)] + suffix
