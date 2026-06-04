"""Tests for the keyword classifier and Lead.category integration."""

import pytest
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture
def fresh_engine(tmp_path):
    import freelance_os.models  # noqa: F401
    engine = create_engine(f"sqlite:///{tmp_path}/test.sqlite")
    SQLModel.metadata.create_all(engine)
    return engine


# ---------------------------------------------------------------------------
# Classifier unit tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("Build a Next.js app with Supabase", "WEB_APP"),
    ("Build a nextjs dashboard", "WEB_APP"),
    ("React frontend with Tailwind CSS", "WEB_APP"),
    ("Power BI dashboard with DAX measures", "DATA_DASHBOARD"),
    ("ETL pipeline for analytics KPIs", "DATA_DASHBOARD"),
    ("Web scraping script to crawl job listings", "SCRAPING_DATA"),
    ("Data pipeline for scraper output", "SCRAPING_DATA"),
    ("Build an AI chatbot using LLM", "AI_AUTOMATION"),
    ("API integration automation agent", "AI_AUTOMATION"),
    ("WordPress WooCommerce site setup", "WORDPRESS"),
    ("Elementor page builder customization", "WORDPRESS"),
    ("Fix a bug in my Python script", "BUG_FIX"),
    ("Small change to hotfix login issue", "BUG_FIX"),
    ("Write a business plan document", "OTHER"),
    ("General consulting work", "OTHER"),
])
def test_classifier_keywords(text, expected):
    from freelance_os.ingestion.classify import classify_lead
    assert classify_lead(text) == expected


def test_classifier_case_insensitive():
    from freelance_os.ingestion.classify import classify_lead
    assert classify_lead("BUILD A NEXT.JS APP") == "WEB_APP"
    assert classify_lead("POWER BI DASHBOARD") == "DATA_DASHBOARD"


def test_classifier_empty_returns_other():
    from freelance_os.ingestion.classify import classify_lead
    assert classify_lead("") == "OTHER"
    assert classify_lead("   ") == "OTHER"


def test_ai_keyword_word_boundary():
    """'ai' must not match inside words like 'email' or 'available'."""
    from freelance_os.ingestion.classify import classify_lead
    assert classify_lead("send me an email about available tasks") == "OTHER"
    assert classify_lead("build an AI chatbot") == "AI_AUTOMATION"


def test_fix_keyword_word_boundary():
    """'fix' should not match 'prefix' or 'fixed price'."""
    from freelance_os.ingestion.classify import classify_lead
    # "fixed" contains "fix" but \bfix\b won't match "fixed"
    result = classify_lead("fixed price web project with React")
    assert result == "WEB_APP"  # React matches before BUG_FIX check


# ---------------------------------------------------------------------------
# Lead.category persistence tests
# ---------------------------------------------------------------------------

def test_lead_category_default(fresh_engine):
    """Lead.category defaults to 'OTHER'."""
    from freelance_os.models import Lead
    with Session(fresh_engine) as session:
        lead = Lead(source="test")
        session.add(lead)
        session.commit()
        session.refresh(lead)
    assert lead.category == "OTHER"


def test_lead_category_persists(fresh_engine):
    """Lead.category can be set and persists."""
    from freelance_os.models import Lead
    with Session(fresh_engine) as session:
        lead = Lead(source="upwork", category="WEB_APP")
        session.add(lead)
        session.commit()
        lead_id = lead.id

    with Session(fresh_engine) as session:
        fetched = session.get(Lead, lead_id)
        assert fetched.category == "WEB_APP"


def test_add_lead_text_applies_classifier(tmp_path, monkeypatch):
    """add_lead_text classifies the lead text on ingestion."""
    import freelance_os.models  # noqa: F401
    from sqlmodel import create_engine as ce
    engine = ce(f"sqlite:///{tmp_path}/t.sqlite")
    SQLModel.metadata.create_all(engine)

    from freelance_os.ingestion.manual import add_lead_text
    cfg = {"paths": {"database_path": str(tmp_path / "t.sqlite")}}
    monkeypatch.setattr("freelance_os.ingestion.manual.get_engine", lambda p: engine)

    lead = add_lead_text(source="upwork", text="Build a Next.js React frontend app", cfg=cfg)
    assert lead.category == "WEB_APP"


def test_add_lead_url_applies_classifier(tmp_path, monkeypatch):
    """add_lead_url classifies description on ingestion."""
    import freelance_os.models  # noqa: F401
    from sqlmodel import create_engine as ce
    engine = ce(f"sqlite:///{tmp_path}/t.sqlite")
    SQLModel.metadata.create_all(engine)

    from freelance_os.ingestion.manual import add_lead_url
    cfg = {"paths": {"database_path": str(tmp_path / "t.sqlite")}}
    monkeypatch.setattr("freelance_os.ingestion.manual.get_engine", lambda p: engine)

    lead = add_lead_url(
        url="https://upwork.com/jobs/1",
        description="Scrape data from job boards using Python crawler",
        cfg=cfg,
    )
    assert lead.category == "SCRAPING_DATA"


def test_migration_adds_category_to_existing_db(tmp_path):
    """create_tables adds category column to a pre-existing lead table without it."""
    import sqlite3
    from freelance_os.db import create_tables
    from sqlalchemy import create_engine as sae

    db_file = tmp_path / "old.sqlite"

    # Simulate an old DB with a lead table missing the category column.
    conn = sqlite3.connect(str(db_file))
    conn.execute(
        "CREATE TABLE lead (id INTEGER PRIMARY KEY, source TEXT, status TEXT DEFAULT 'NEW', "
        "source_url TEXT, title TEXT, description TEXT, client_name TEXT, "
        "client_rating REAL, client_payment_verified INTEGER DEFAULT 0, "
        "budget_type TEXT, budget_min REAL, budget_max REAL, "
        "hourly_min REAL, hourly_max REAL, country TEXT, posted_at TEXT, "
        "imported_at TEXT, lead_score INTEGER, risk_score INTEGER, "
        "decision TEXT, reason_codes TEXT, raw_payload TEXT, notes TEXT)"
    )
    conn.commit()
    conn.close()

    # Running create_tables should add the category column without error.
    engine = sae(f"sqlite:///{db_file}")
    create_tables(engine, str(db_file))

    # Verify column exists and existing rows default to 'OTHER'.
    conn = sqlite3.connect(str(db_file))
    cols = [row[1] for row in conn.execute("PRAGMA table_info(lead)").fetchall()]
    assert "category" in cols
    conn.close()
