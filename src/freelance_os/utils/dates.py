"""Date utilities."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d") if dt else ""
