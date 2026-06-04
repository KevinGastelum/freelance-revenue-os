"""Phase 2: Lead management tests."""

import pytest
from pathlib import Path
from sqlmodel import Session, create_engine, SQLModel, select


@pytest.fixture
def engine_and_cfg(tmp_path):
    import freelance_os.models  # noqa: F401
    engine = create_engine(f"sqlite:///{tmp_path}/test.sqlite")
    SQLModel.metadata.create_all(engine)
    cfg = {
        "paths": {"database_path": str(tmp_path / "test.sqlite")},
        "scoring": {"target_hourly_rate": 75, "minimum_project_value": 300},
    }
    return engine, cfg


def test_add_lead_url(engine_and_cfg, monkeypatch):
    """add_lead_url creates a lead with source=manual_url."""
    from freelance_os.ingestion.manual import add_lead_url
    from freelance_os.models import Lead, LeadStatus

    engine, cfg = engine_and_cfg
    monkeypatch.setattr("freelance_os.ingestion.manual.get_engine", lambda path: engine)

    lead = add_lead_url(
        url="https://upwork.com/jobs/123",
        description="Build a FastAPI backend. Budget $1500.",
        cfg=cfg,
    )
    assert lead.id is not None
    assert lead.source == "manual_url"
    assert lead.source_url == "https://upwork.com/jobs/123"
    assert lead.status == LeadStatus.NEW


def test_add_lead_text(engine_and_cfg, monkeypatch):
    """add_lead_text creates a lead from pasted text."""
    from freelance_os.ingestion.manual import add_lead_text
    from freelance_os.models import LeadStatus

    engine, cfg = engine_and_cfg
    monkeypatch.setattr("freelance_os.ingestion.manual.get_engine", lambda path: engine)

    text = "Build Next.js dashboard with Supabase authentication. Budget $2000-$4000."
    lead = add_lead_text(source="upwork", text=text, cfg=cfg)

    assert lead.id is not None
    assert lead.source == "upwork"
    assert lead.status == LeadStatus.NEW
    assert lead.description == text


def test_add_lead_extracts_budget(engine_and_cfg, monkeypatch):
    """add_lead_text should parse budget from text."""
    from freelance_os.ingestion.manual import add_lead_text

    engine, cfg = engine_and_cfg
    monkeypatch.setattr("freelance_os.ingestion.manual.get_engine", lambda path: engine)

    text = "Build Python API. Budget range: $1000-$3000 fixed price project."
    lead = add_lead_text(source="direct", text=text, cfg=cfg)
    assert lead.budget_min == 1000.0 or lead.budget_max == 3000.0


def test_add_lead_extracts_title(engine_and_cfg, monkeypatch):
    """add_lead_text should extract title from first line."""
    from freelance_os.ingestion.manual import add_lead_text

    engine, cfg = engine_and_cfg
    monkeypatch.setattr("freelance_os.ingestion.manual.get_engine", lambda path: engine)

    text = "Senior Python Developer Needed\n\nWe need a Python developer with FastAPI experience."
    lead = add_lead_text(source="upwork", text=text, cfg=cfg)
    assert lead.title == "Senior Python Developer Needed"


def test_lead_status_update(engine_and_cfg, monkeypatch):
    """Lead status can be updated to any valid LeadStatus."""
    from freelance_os.ingestion.manual import add_lead_text
    from freelance_os.models import Lead, LeadStatus

    engine, cfg = engine_and_cfg
    monkeypatch.setattr("freelance_os.ingestion.manual.get_engine", lambda path: engine)

    lead = add_lead_text(source="test", text="Test job description", cfg=cfg)

    with Session(engine) as session:
        l = session.get(Lead, lead.id)
        l.status = LeadStatus.REJECTED
        session.add(l)
        session.commit()

        refreshed = session.get(Lead, lead.id)
        assert refreshed.status == LeadStatus.REJECTED


def test_email_parser_extracts_url():
    """Email parser extracts job URL and a title from email text."""
    from freelance_os.ingestion.email_parser import parse_email_text

    email = """\
From: noreply@upwork.com
Subject: New Job Alert: Python Developer Needed

View this job at: https://upwork.com/jobs/~01abc123def456789

Build a Python API backend. Budget $1000-$2000.
"""
    result = parse_email_text(email)
    assert "upwork.com" in (result.get("source_url") or "")
    assert result.get("title") is not None  # title extracted from body or subject


def test_csv_import_normalizes_fields(tmp_path):
    """CSV import normalizes column names to Lead field names."""
    from freelance_os.ingestion.import_csv import import_from_csv

    csv_file = tmp_path / "leads.csv"
    csv_file.write_text(
        "title,url,budget,description\n"
        "Build Dashboard,https://upwork.com/1,2000,Need a dashboard\n",
        encoding="utf-8",
    )
    rows = import_from_csv(str(csv_file))
    assert len(rows) == 1
    assert rows[0]["title"] == "Build Dashboard"
    assert rows[0].get("source_url") == "https://upwork.com/1"


def test_json_import(tmp_path):
    """JSON import reads leads from a JSON file."""
    import json
    from freelance_os.ingestion.import_csv import import_from_json

    json_file = tmp_path / "leads.json"
    json_file.write_text(
        json.dumps([
            {"title": "API Project", "url": "https://example.com", "description": "Build an API"}
        ]),
        encoding="utf-8",
    )
    rows = import_from_json(str(json_file))
    assert len(rows) == 1
    assert rows[0]["title"] == "API Project"
