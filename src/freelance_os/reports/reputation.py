"""Reputation aggregation: track win/loss rates, ratings, on-time delivery, earnings."""

from collections import defaultdict
from typing import Optional

from sqlmodel import Session, select

from freelance_os.db import get_engine
from freelance_os.models import Lead, LeadStatus, Outcome, OutcomeResult


def aggregate_reputation(cfg: dict) -> dict:
    """Return overall + per-platform + momentum reputation metrics."""
    engine = get_engine(cfg["paths"]["database_path"])

    with Session(engine) as session:
        leads = session.exec(select(Lead)).all()
        outcomes = session.exec(select(Outcome)).all()

    lead_map = {lead.id: lead for lead in leads}

    # ---- overall ----
    applied_statuses = {
        LeadStatus.APPLIED_MANUALLY,
        LeadStatus.INTERVIEW,
        LeadStatus.WON,
        LeadStatus.LOST,
    }
    total_applications = sum(1 for l in leads if l.status in applied_statuses)
    interviews = sum(
        1 for l in leads if l.status in (LeadStatus.INTERVIEW, LeadStatus.WON)
    )
    wins = sum(1 for o in outcomes if o.result == OutcomeResult.WON)
    losses = sum(1 for o in outcomes if o.result == OutcomeResult.LOST)
    decided = wins + losses
    win_rate: Optional[float] = wins / decided if decided > 0 else None

    rated = [o for o in outcomes if o.rating is not None]
    avg_rating: Optional[float] = (
        sum(o.rating for o in rated) / len(rated) if rated else None  # type: ignore[arg-type]
    )

    timed = [o for o in outcomes if o.on_time is not None]
    on_time_pct: Optional[float] = (
        sum(1 for o in timed if o.on_time) / len(timed) if timed else None
    )

    repeat_client_count = sum(1 for o in outcomes if o.is_repeat_client)

    won_outcomes = [o for o in outcomes if o.result == OutcomeResult.WON]
    total_earnings = sum(o.final_budget or 0.0 for o in won_outcomes)
    avg_project_value: Optional[float] = (
        total_earnings / len(won_outcomes) if won_outcomes else None
    )

    # ---- per-platform ----
    # Bucket outcomes by platform field or fall back to lead.source
    plat_data: dict = defaultdict(lambda: {
        "applications": 0,
        "wins": 0,
        "losses": 0,
        "ratings": [],
        "on_time_count": 0,
        "timed_count": 0,
        "repeat_clients": 0,
        "earnings": 0.0,
    })

    for o in outcomes:
        lead = lead_map.get(o.lead_id)
        plat = o.platform or (lead.source if lead else None) or "unknown"
        d = plat_data[plat]
        if o.result == OutcomeResult.WON:
            d["wins"] += 1
            d["earnings"] += o.final_budget or 0.0
        elif o.result == OutcomeResult.LOST:
            d["losses"] += 1
        if o.rating is not None:
            d["ratings"].append(o.rating)
        if o.on_time is not None:
            d["timed_count"] += 1
            if o.on_time:
                d["on_time_count"] += 1
        if o.is_repeat_client:
            d["repeat_clients"] += 1

    # Count applications from leads per source (only applied+ statuses)
    for lead in leads:
        if lead.status in applied_statuses:
            src = lead.source or "unknown"
            plat_data[src]["applications"] += 1

    per_platform = []
    for plat, d in sorted(plat_data.items()):
        total = d["wins"] + d["losses"]
        wr: Optional[float] = d["wins"] / total if total > 0 else None
        avg_r: Optional[float] = (
            sum(d["ratings"]) / len(d["ratings"]) if d["ratings"] else None
        )
        otp: Optional[float] = (
            d["on_time_count"] / d["timed_count"] if d["timed_count"] > 0 else None
        )
        per_platform.append({
            "platform": plat,
            "applications": d["applications"],
            "wins": d["wins"],
            "losses": d["losses"],
            "win_rate": wr,
            "avg_rating": avg_r,
            "on_time_pct": otp,
            "repeat_clients": d["repeat_clients"],
            "earnings": d["earnings"],
        })

    # ---- momentum (by month) ----
    monthly: dict = defaultdict(lambda: {
        "wins": 0,
        "losses": 0,
        "earnings": 0.0,
        "ratings": [],
    })
    for o in outcomes:
        key = o.created_at.strftime("%Y-%m") if o.created_at else "unknown"
        m = monthly[key]
        if o.result == OutcomeResult.WON:
            m["wins"] += 1
            m["earnings"] += o.final_budget or 0.0
        elif o.result == OutcomeResult.LOST:
            m["losses"] += 1
        if o.rating is not None:
            m["ratings"].append(o.rating)

    momentum = []
    for period in sorted(monthly.keys()):
        m = monthly[period]
        total_m = m["wins"] + m["losses"]
        momentum.append({
            "period": period,
            "wins": m["wins"],
            "losses": m["losses"],
            "win_rate": m["wins"] / total_m if total_m > 0 else None,
            "earnings": m["earnings"],
            "avg_rating": (
                sum(m["ratings"]) / len(m["ratings"]) if m["ratings"] else None
            ),
        })

    return {
        "total_applications": total_applications,
        "interviews": interviews,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "avg_rating": avg_rating,
        "on_time_pct": on_time_pct,
        "repeat_client_count": repeat_client_count,
        "total_earnings": total_earnings,
        "avg_project_value": avg_project_value,
        "per_platform": per_platform,
        "momentum": momentum,
    }
