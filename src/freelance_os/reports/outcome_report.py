"""Weekly outcome report generator."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select, create_engine

from freelance_os.models import Lead, LeadStatus, Outcome, ProposalDraft


def generate_weekly_report(db_path: Optional[Path] = None) -> str:
    if db_path is None:
        db_path = Path("data/freelance_os.sqlite")

    if not db_path.exists():
        return "# Weekly Report\n\nNo database found. Run `freelance-os init` first.\n"

    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    with Session(engine) as session:
        leads = session.exec(select(Lead)).all()
        outcomes = session.exec(select(Outcome)).all()
        drafts = session.exec(select(ProposalDraft)).all()

    total_leads = len(leads)
    rejected = sum(1 for l in leads if l.status == LeadStatus.REJECTED)
    drafted = sum(1 for l in leads if l.status in (LeadStatus.DRAFTED, LeadStatus.APPROVED_TO_APPLY, LeadStatus.APPLIED_MANUALLY))
    applied = sum(1 for l in leads if l.status == LeadStatus.APPLIED_MANUALLY)
    interviews = sum(1 for l in leads if l.status == LeadStatus.INTERVIEW)
    won = sum(1 for l in leads if l.status == LeadStatus.WON)
    lost = sum(1 for l in leads if l.status == LeadStatus.LOST)

    won_outcomes = [o for o in outcomes if o.result.value == "WON"]
    revenue = sum(o.final_budget or 0 for o in won_outcomes)

    proposals_drafted = len(drafts)

    lines = [
        f"# Weekly Freelance Report",
        f"",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"",
        f"## Lead Pipeline",
        f"",
        f"| Metric                  | Count |",
        f"|-------------------------|-------|",
        f"| Leads imported          | {total_leads} |",
        f"| Leads rejected          | {rejected} |",
        f"| Proposals drafted       | {proposals_drafted} |",
        f"| Proposals submitted     | {applied} |",
        f"| Interviews              | {interviews} |",
        f"| Won contracts           | {won} |",
        f"| Lost opportunities      | {lost} |",
        f"",
        f"## Revenue",
        f"",
        f"| Metric                  | Value |",
        f"|-------------------------|-------|",
        f"| Estimated revenue (won) | ${revenue:,.0f} |",
        f"",
    ]

    if outcomes:
        lines.append("## Outcomes")
        lines.append("")
        for o in outcomes:
            lines.append(f"- Lead #{o.lead_id}: {o.result.value}" + (f" — {o.reason}" if o.reason else ""))
        lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append("- Review won/lost patterns to refine scoring rules.")
    lines.append("- All platform actions were performed manually by the user.")
    lines.append("")

    return "\n".join(lines)
