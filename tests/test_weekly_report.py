"""Phase 7: Weekly report and outcome tracking integration tests."""

import pytest
from pathlib import Path
from sqlmodel import Session, create_engine, SQLModel, select


@pytest.fixture
def full_engine_cfg(tmp_path):
    import freelance_os.models  # noqa: F401
    engine = create_engine(f"sqlite:///{tmp_path}/test.sqlite")
    SQLModel.metadata.create_all(engine)
    cfg = {
        "paths": {
            "database_path": str(tmp_path / "test.sqlite"),
            "client_work_dir": str(tmp_path / "client-work"),
            "portfolio_file": str(tmp_path / "portfolio.yaml"),
        },
        "scoring": {"target_hourly_rate": 75, "minimum_project_value": 300},
    }
    return engine, cfg


def populate_db(engine):
    """Insert sample data for reporting."""
    from freelance_os.models import Lead, LeadStatus, Outcome, OutcomeResult, ProposalDraft

    with Session(engine) as session:
        leads = [
            Lead(source="upwork", status=LeadStatus.NEW, lead_score=45),
            Lead(source="upwork", status=LeadStatus.SCORED, lead_score=72),
            Lead(source="fiverr", status=LeadStatus.DRAFTED, lead_score=80),
            Lead(source="direct", status=LeadStatus.APPLIED_MANUALLY, lead_score=85),
            Lead(source="upwork", status=LeadStatus.WON, lead_score=90),
            Lead(source="upwork", status=LeadStatus.LOST, lead_score=60),
            Lead(source="contra", status=LeadStatus.REJECTED, lead_score=35),
        ]
        for lead in leads:
            session.add(lead)
        session.commit()

        # Refresh to get IDs
        for lead in leads:
            session.refresh(lead)

        won_lead = [l for l in leads if l.status == LeadStatus.WON][0]
        draft_lead = [l for l in leads if l.status == LeadStatus.DRAFTED][0]

        session.add(ProposalDraft(lead_id=won_lead.id, draft_text="Test proposal"))
        session.add(ProposalDraft(lead_id=draft_lead.id, draft_text="Another draft"))

        session.add(Outcome(
            lead_id=won_lead.id,
            result=OutcomeResult.WON,
            final_budget=2500.0,
            time_spent_hours=30.0,
            lessons="Clear scope helped a lot.",
        ))
        lost_lead = [l for l in leads if l.status == LeadStatus.LOST][0]
        session.add(Outcome(
            lead_id=lost_lead.id,
            result=OutcomeResult.LOST,
            reason="Budget too low",
        ))
        session.commit()


def test_report_all_sections_present(full_engine_cfg, monkeypatch):
    """Weekly report should contain all required sections."""
    from freelance_os.reports.outcome_report import generate_weekly_report

    engine, cfg = full_engine_cfg
    monkeypatch.setattr("freelance_os.reports.outcome_report.get_engine", lambda path: engine)

    populate_db(engine)
    report = generate_weekly_report(cfg=cfg)

    assert "Pipeline Summary" in report
    assert "Revenue" in report
    assert "Lead Quality" in report
    assert "Lead Sources" in report
    assert "Rejection Reasons" in report or "Rejection" in report


def test_report_lead_counts_accurate(full_engine_cfg, monkeypatch):
    """Report counts should reflect DB state."""
    from freelance_os.reports.outcome_report import generate_weekly_report

    engine, cfg = full_engine_cfg
    monkeypatch.setattr("freelance_os.reports.outcome_report.get_engine", lambda path: engine)

    populate_db(engine)
    report = generate_weekly_report(cfg=cfg)

    # 7 total leads, 1 rejected, 1 won, 1 lost
    assert "7" in report
    assert "1" in report  # won


def test_report_revenue_shown(full_engine_cfg, monkeypatch):
    """Report should show revenue from WON outcomes."""
    from freelance_os.reports.outcome_report import generate_weekly_report

    engine, cfg = full_engine_cfg
    monkeypatch.setattr("freelance_os.reports.outcome_report.get_engine", lambda path: engine)

    populate_db(engine)
    report = generate_weekly_report(cfg=cfg)

    assert "2,500" in report or "2500" in report


def test_report_loss_reasons_shown(full_engine_cfg, monkeypatch):
    """Report should show common rejection reasons."""
    from freelance_os.reports.outcome_report import generate_weekly_report

    engine, cfg = full_engine_cfg
    monkeypatch.setattr("freelance_os.reports.outcome_report.get_engine", lambda path: engine)

    populate_db(engine)
    report = generate_weekly_report(cfg=cfg)

    assert "Budget too low" in report


def test_report_export_utf8(full_engine_cfg, monkeypatch, tmp_path):
    """Exported report should be valid UTF-8 text."""
    from freelance_os.reports.outcome_report import generate_weekly_report

    engine, cfg = full_engine_cfg
    monkeypatch.setattr("freelance_os.reports.outcome_report.get_engine", lambda path: engine)

    export_path = str(tmp_path / "weekly.md")
    generate_weekly_report(cfg=cfg, export_path=export_path)

    content = Path(export_path).read_text(encoding="utf-8")
    assert "Weekly Freelance Report" in content


def test_report_source_breakdown(full_engine_cfg, monkeypatch):
    """Report should show source breakdown."""
    from freelance_os.reports.outcome_report import generate_weekly_report

    engine, cfg = full_engine_cfg
    monkeypatch.setattr("freelance_os.reports.outcome_report.get_engine", lambda path: engine)

    populate_db(engine)
    report = generate_weekly_report(cfg=cfg)

    assert "upwork" in report
    assert "fiverr" in report
    assert "direct" in report


def test_outcome_lessons_stored(full_engine_cfg):
    """Outcome lessons field should be stored and retrieved."""
    from freelance_os.models import Lead, LeadStatus, Outcome, OutcomeResult

    engine, cfg = full_engine_cfg
    with Session(engine) as session:
        lead = Lead(source="test", status=LeadStatus.WON)
        session.add(lead)
        session.commit()
        session.refresh(lead)

        outcome = Outcome(
            lead_id=lead.id,
            result=OutcomeResult.WON,
            lessons="Great client. Clear requirements made delivery smooth.",
            final_budget=1800.0,
            time_spent_hours=22.5,
            profit_estimate=1620.0,
        )
        session.add(outcome)
        session.commit()
        session.refresh(outcome)

    with Session(engine) as session:
        found = session.get(Outcome, outcome.id)
        assert "Great client" in found.lessons
        assert found.final_budget == 1800.0
        assert found.time_spent_hours == 22.5
