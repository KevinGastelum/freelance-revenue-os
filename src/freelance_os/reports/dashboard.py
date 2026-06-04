"""Dashboard utilities (stub for future TUI/FastAPI use)."""


def get_dashboard_data(cfg: dict) -> dict:
    """Return aggregated dashboard metrics."""
    from sqlmodel import Session, select
    from freelance_os.db import get_engine
    from freelance_os.models import Lead, Outcome

    engine = get_engine(cfg["paths"]["database_path"])
    with Session(engine) as session:
        leads = session.exec(select(Lead)).all()
        outcomes = session.exec(select(Outcome)).all()

    return {
        "total_leads": len(leads),
        "total_outcomes": len(outcomes),
        "status_counts": _count_by(leads, "status"),
        "source_counts": _count_by(leads, "source"),
    }


def _count_by(items: list, attr: str) -> dict:
    result: dict = {}
    for item in items:
        key = str(getattr(item, attr, "unknown"))
        result[key] = result.get(key, 0) + 1
    return result
