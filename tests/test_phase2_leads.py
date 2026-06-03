"""Phase 2 tests: lead management — add, list, show, status."""

import pytest
from pathlib import Path

from freelance_os.db import init_db, reset_engine, get_session
from freelance_os.models import Lead, LeadStatus
from freelance_os.ingestion.manual import add_lead_by_url, add_lead_by_text, _parse_budget
from sqlmodel import select


def test_add_lead_by_url(tmp_db):
    lead = add_lead_by_url("https://upwork.com/job/123", db_path=tmp_db)
    assert lead.id is not None
    assert lead.source == "manual_url"
    assert lead.source_url == "https://upwork.com/job/123"
    assert lead.status == LeadStatus.NEW


def test_add_lead_by_url_with_description(tmp_db):
    lead = add_lead_by_url(
        "https://upwork.com/job/456",
        description="Build a React dashboard with real-time data",
        db_path=tmp_db,
    )
    assert lead.title == "Build a React dashboard with real-time data"
    assert lead.description is not None


def test_add_lead_by_text(tmp_db):
    text = "Build a Next.js app with Supabase authentication and a PostgreSQL backend."
    lead = add_lead_by_text(source="upwork", text=text, db_path=tmp_db)
    assert lead.id is not None
    assert lead.source == "upwork"
    assert lead.title == "Build a Next.js app with Supabase authentication and a PostgreSQL backend."
    assert lead.status == LeadStatus.NEW


def test_add_lead_by_text_parses_budget(tmp_db):
    text = "We need a developer. Budget is $500 - $1,000 for this project."
    lead = add_lead_by_text(source="upwork", text=text, db_path=tmp_db)
    assert lead.budget_min == 500.0
    assert lead.budget_max == 1000.0


def test_add_lead_persists_to_db(tmp_db):
    add_lead_by_url("https://example.com/job/1", db_path=tmp_db)
    add_lead_by_url("https://example.com/job/2", db_path=tmp_db)
    with get_session(tmp_db) as session:
        leads = session.exec(select(Lead)).all()
    assert len(leads) == 2


def test_lead_status_update(tmp_db):
    lead = add_lead_by_url("https://example.com/job/1", db_path=tmp_db)
    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        db_lead.status = LeadStatus.REJECTED
        session.add(db_lead)
        session.commit()

    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        assert db_lead.status == LeadStatus.REJECTED


def test_invalid_status_raises():
    with pytest.raises(ValueError):
        LeadStatus("INVALID_STATUS")


def test_parse_budget_range():
    lo, hi = _parse_budget("Budget: $500 - $1,000")
    assert lo == 500.0
    assert hi == 1000.0


def test_parse_budget_single():
    lo, hi = _parse_budget("Project budget: $750")
    assert lo == 750.0
    assert hi == 750.0


def test_parse_budget_none():
    lo, hi = _parse_budget("No budget mentioned here.")
    assert lo is None
    assert hi is None


def test_multiple_leads_different_sources(tmp_db):
    add_lead_by_url("https://upwork.com/j/1", db_path=tmp_db)
    add_lead_by_text(source="fiverr", text="Need logo design", db_path=tmp_db)
    add_lead_by_text(source="contra", text="Full stack developer needed", db_path=tmp_db)

    with get_session(tmp_db) as session:
        leads = session.exec(select(Lead)).all()
    assert len(leads) == 3
    sources = {l.source for l in leads}
    assert "fiverr" in sources
    assert "contra" in sources
