"""Phase 7: Report generation tests."""

import pytest
from sqlmodel import Session, create_engine, SQLModel


@pytest.fixture
def report_engine(tmp_path):
    import freelance_os.models  # noqa: F401
    engine = create_engine(f"sqlite:///{tmp_path}/test.sqlite")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def report_cfg(tmp_path, report_engine):
    return {
        "paths": {
            "database_path": str(tmp_path / "test.sqlite"),
            "client_work_dir": str(tmp_path / "client-work"),
            "portfolio_file": str(tmp_path / "portfolio.yaml"),
        },
        "scoring": {"target_hourly_rate": 75, "minimum_project_value": 300},
    }


def test_weekly_report_empty_db(report_cfg, monkeypatch, report_engine):
    """Weekly report on empty DB should not crash."""
    from freelance_os.reports.outcome_report import generate_weekly_report
    from freelance_os.db import get_engine

    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: report_engine)
    monkeypatch.setattr("freelance_os.reports.outcome_report.get_engine", lambda path: report_engine)

    report = generate_weekly_report(cfg=report_cfg)
    assert "Weekly Freelance Report" in report
    assert "Pipeline Summary" in report


def test_weekly_report_with_leads(report_cfg, monkeypatch, report_engine):
    """Weekly report should aggregate lead counts correctly."""
    from freelance_os.models import Lead, LeadStatus, Outcome, OutcomeResult
    from freelance_os.reports.outcome_report import generate_weekly_report

    monkeypatch.setattr("freelance_os.reports.outcome_report.get_engine", lambda path: report_engine)

    with Session(report_engine) as session:
        session.add(Lead(source="upwork", status=LeadStatus.NEW))
        session.add(Lead(source="fiverr", status=LeadStatus.SCORED, lead_score=75))
        session.add(Lead(source="upwork", status=LeadStatus.WON, lead_score=85))
        session.add(Lead(source="upwork", status=LeadStatus.REJECTED))
        session.commit()

        leads = session.exec(__import__("sqlmodel").select(Lead)).all()
        won_lead = [l for l in leads if l.status == LeadStatus.WON][0]

        outcome = Outcome(
            lead_id=won_lead.id,
            result=OutcomeResult.WON,
            final_budget=1500.0,
        )
        session.add(outcome)
        session.commit()

    report = generate_weekly_report(cfg=report_cfg)
    assert "4" in report  # total leads
    assert "1,500" in report or "1500" in report  # revenue (comma-formatted or plain)


def test_weekly_report_markdown_export(report_cfg, monkeypatch, report_engine, tmp_path):
    """Weekly report should export to markdown file."""
    from freelance_os.reports.outcome_report import generate_weekly_report

    monkeypatch.setattr("freelance_os.reports.outcome_report.get_engine", lambda path: report_engine)

    export_path = str(tmp_path / "report.md")
    generate_weekly_report(cfg=report_cfg, export_path=export_path)

    content = open(export_path, encoding="utf-8").read()
    assert "Weekly Freelance Report" in content


def test_lead_ingestion_and_retrieval(tmp_path, monkeypatch):
    """Can add a lead and retrieve it."""
    import freelance_os.models  # noqa: F401
    from freelance_os.ingestion.manual import add_lead_text
    from freelance_os.models import Lead, LeadStatus
    from sqlmodel import create_engine, SQLModel, Session, select

    engine = create_engine(f"sqlite:///{tmp_path}/test.sqlite")
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr("freelance_os.ingestion.manual.get_engine", lambda path: engine)

    cfg = {
        "paths": {"database_path": str(tmp_path / "test.sqlite")},
        "scoring": {"target_hourly_rate": 75, "minimum_project_value": 300},
    }

    lead = add_lead_text(source="upwork", text="Build Python FastAPI backend. Budget $2000.", cfg=cfg)
    assert lead.id is not None
    assert lead.source == "upwork"
    assert lead.status == LeadStatus.NEW

    with Session(engine) as session:
        found = session.get(Lead, lead.id)
        assert found is not None
        assert found.description is not None


def test_outcome_recording(tmp_path, monkeypatch):
    """Can add an outcome for a lead."""
    import freelance_os.models  # noqa: F401
    from freelance_os.models import Lead, LeadStatus, Outcome, OutcomeResult
    from sqlmodel import create_engine, SQLModel, Session, select

    engine = create_engine(f"sqlite:///{tmp_path}/test.sqlite")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        lead = Lead(source="test", status=LeadStatus.WON)
        session.add(lead)
        session.commit()
        session.refresh(lead)

        outcome = Outcome(
            lead_id=lead.id,
            result=OutcomeResult.WON,
            final_budget=2000.0,
            time_spent_hours=25.0,
            lessons="Good client, clear scope.",
        )
        session.add(outcome)
        session.commit()
        session.refresh(outcome)

        assert outcome.id is not None
        assert outcome.result == OutcomeResult.WON
        assert outcome.final_budget == 2000.0
