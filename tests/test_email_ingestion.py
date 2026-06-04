"""Tests for email job-alert ingestion: parser, dedup, IMAP mock."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_engine(tmp_path):
    import freelance_os.models  # noqa: F401
    engine = create_engine(f"sqlite:///{tmp_path}/test.sqlite")
    SQLModel.metadata.create_all(engine)
    return engine


# ---------------------------------------------------------------------------
# parse_eml_file — Upwork digest alert
# ---------------------------------------------------------------------------

def test_parse_eml_detects_upwork_source():
    from freelance_os.ingestion.email_parser import parse_eml_file
    jobs = parse_eml_file(FIXTURES / "upwork_alert.eml")
    assert len(jobs) >= 1
    assert all(j["source"] == "upwork" for j in jobs)


def test_parse_eml_extracts_multiple_jobs():
    from freelance_os.ingestion.email_parser import parse_eml_file
    jobs = parse_eml_file(FIXTURES / "upwork_alert.eml")
    assert len(jobs) >= 2


def test_parse_eml_extracts_dashboard_title():
    from freelance_os.ingestion.email_parser import parse_eml_file
    jobs = parse_eml_file(FIXTURES / "upwork_alert.eml")
    titles = [j.get("title") or "" for j in jobs]
    assert any("Dashboard" in t or "Python" in t for t in titles)


def test_parse_eml_extracts_fixed_budget():
    from freelance_os.ingestion.email_parser import parse_eml_file
    jobs = parse_eml_file(FIXTURES / "upwork_alert.eml")
    fixed = [j for j in jobs if j.get("budget_type") == "fixed"]
    assert len(fixed) >= 1
    assert fixed[0]["budget_min"] == 500.0
    assert fixed[0]["budget_max"] == 1500.0


def test_parse_eml_extracts_hourly_budget():
    from freelance_os.ingestion.email_parser import parse_eml_file
    jobs = parse_eml_file(FIXTURES / "upwork_alert.eml")
    hourly = [j for j in jobs if j.get("budget_type") == "hourly"]
    assert len(hourly) >= 1
    assert hourly[0]["hourly_min"] == 50.0
    assert hourly[0]["hourly_max"] == 80.0


def test_parse_eml_extracts_upwork_urls():
    from freelance_os.ingestion.email_parser import parse_eml_file
    jobs = parse_eml_file(FIXTURES / "upwork_alert.eml")
    urls = [j.get("source_url") or "" for j in jobs]
    assert any("upwork.com" in u for u in urls)


def test_parse_eml_source_override():
    from freelance_os.ingestion.email_parser import parse_eml_file
    jobs = parse_eml_file(FIXTURES / "upwork_alert.eml", source_override="manual")
    assert all(j["source"] == "manual" for j in jobs)


# ---------------------------------------------------------------------------
# parse_mbox_file — Fiverr alert
# ---------------------------------------------------------------------------

def test_parse_mbox_detects_fiverr_source():
    from freelance_os.ingestion.email_parser import parse_mbox_file
    jobs = parse_mbox_file(FIXTURES / "mixed_alert.mbox")
    assert len(jobs) >= 1
    assert any(j["source"] == "fiverr" for j in jobs)


def test_parse_mbox_extracts_wordpress_title():
    from freelance_os.ingestion.email_parser import parse_mbox_file
    jobs = parse_mbox_file(FIXTURES / "mixed_alert.mbox")
    titles = [j.get("title") or "" for j in jobs]
    assert any("WordPress" in t or "Bug" in t or "Fix" in t for t in titles)


def test_parse_mbox_extracts_budget():
    from freelance_os.ingestion.email_parser import parse_mbox_file
    jobs = parse_mbox_file(FIXTURES / "mixed_alert.mbox")
    budgeted = [j for j in jobs if j.get("budget_type")]
    assert len(budgeted) >= 1


def test_parse_mbox_classifier_integration():
    from freelance_os.ingestion.email_parser import parse_mbox_file
    from freelance_os.ingestion.classify import classify_lead
    valid_cats = {"WORDPRESS", "BUG_FIX", "WEB_APP", "AI_AUTOMATION",
                  "SCRAPING_DATA", "DATA_DASHBOARD", "OTHER"}
    jobs = parse_mbox_file(FIXTURES / "mixed_alert.mbox")
    for job in jobs:
        text = " ".join(filter(None, [job.get("title"), job.get("description")]))
        assert classify_lead(text) in valid_cats


# ---------------------------------------------------------------------------
# parse_raw_text — inline text
# ---------------------------------------------------------------------------

def test_parse_raw_detects_freelancer_source():
    from freelance_os.ingestion.email_parser import parse_raw_text
    text = (
        "From: alerts@freelancer.com\n"
        "Subject: New project matching your skills\n\n"
        "Build a Python data scraper\n"
        "Budget: $200 - $500\n"
        "https://www.freelancer.com/projects/12345/build-python-scraper\n"
    )
    jobs = parse_raw_text(text)
    assert len(jobs) >= 1
    assert jobs[0]["source"] == "freelancer"


def test_parse_raw_extracts_url():
    from freelance_os.ingestion.email_parser import parse_raw_text
    text = (
        "From: alerts@freelancer.com\n\n"
        "Build a React dashboard\n"
        "https://www.freelancer.com/projects/99999/react-dashboard\n"
    )
    jobs = parse_raw_text(text)
    assert any("freelancer.com" in (j.get("source_url") or "") for j in jobs)


def test_parse_raw_source_override():
    from freelance_os.ingestion.email_parser import parse_raw_text
    jobs = parse_raw_text("Some job posting text", source_override="workana")
    assert jobs[0]["source"] == "workana"


def test_detect_source_from_body_url():
    from freelance_os.ingestion.email_parser import detect_source
    body = "Apply here: https://www.upwork.com/jobs/~abc"
    assert detect_source("", body) == "upwork"


def test_detect_source_from_header():
    from freelance_os.ingestion.email_parser import detect_source
    assert detect_source("alerts@peopleperhour.com") == "peopleperhour"
    assert detect_source("noreply@workana.com") == "workana"
    assert detect_source("info@freelancehunt.com") == "freelancehunt"


def test_detect_source_unknown_returns_email():
    from freelance_os.ingestion.email_parser import detect_source
    assert detect_source("newsletter@unknown.org") == "email"


# ---------------------------------------------------------------------------
# Dedup checks (DB-level)
# ---------------------------------------------------------------------------

def test_dedup_url_already_exists(db_engine):
    """A lead with the same source_url is detected as a duplicate."""
    from freelance_os.models import Lead
    from sqlmodel import select

    url = "https://www.upwork.com/jobs/~dedup_url_001"
    with Session(db_engine) as session:
        session.add(Lead(source="upwork", source_url=url))
        session.commit()

    with Session(db_engine) as session:
        existing = session.exec(select(Lead).where(Lead.source_url == url)).first()
        assert existing is not None


def test_dedup_source_plus_title(db_engine):
    """A lead with the same source+title (no URL) is detected as a duplicate."""
    from freelance_os.models import Lead
    from sqlmodel import select

    with Session(db_engine) as session:
        session.add(Lead(source="fiverr", title="Build a React App"))
        session.commit()

    with Session(db_engine) as session:
        existing = session.exec(
            select(Lead)
            .where(Lead.source == "fiverr")
            .where(Lead.title == "Build a React App")
        ).first()
        assert existing is not None


def test_new_lead_inserted_when_no_dup(db_engine):
    """A lead with a unique URL is inserted, not skipped."""
    from freelance_os.models import Lead, LeadStatus
    from freelance_os.ingestion.classify import classify_lead
    from sqlmodel import select

    job = {
        "source": "upwork",
        "title": "Unique AI project",
        "source_url": "https://www.upwork.com/jobs/~unique_001",
        "description": "Build an AI chatbot with LLM",
        "budget_type": "hourly",
        "hourly_min": 60.0,
        "hourly_max": 90.0,
    }

    with Session(db_engine) as session:
        existing = session.exec(
            select(Lead).where(Lead.source_url == job["source_url"])
        ).first()
        assert existing is None

        text = " ".join(filter(None, [job.get("title"), job.get("description")]))
        lead = Lead(
            source=job["source"],
            source_url=job["source_url"],
            title=job["title"],
            description=job["description"],
            budget_type=job.get("budget_type"),
            hourly_min=job.get("hourly_min"),
            hourly_max=job.get("hourly_max"),
            status=LeadStatus.NEW,
            category=classify_lead(text),
        )
        session.add(lead)
        session.commit()
        session.refresh(lead)
        assert lead.id is not None
        assert lead.category == "AI_AUTOMATION"


# ---------------------------------------------------------------------------
# IMAP mock tests
# ---------------------------------------------------------------------------

def _make_raw_email(from_addr: str, subject: str, body: str) -> bytes:
    msg = (
        f"From: {from_addr}\r\n"
        f"Subject: {subject}\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n"
        f"\r\n"
        f"{body}"
    )
    return msg.encode("utf-8")


def _build_mock_imap(raw_email: bytes) -> MagicMock:
    mock = MagicMock()
    mock.login.return_value = ("OK", [b"Logged in"])
    mock.select.return_value = ("OK", [b"1"])
    mock.search.return_value = ("OK", [b"1"])
    mock.fetch.return_value = ("OK", [(b"1 (RFC822 {%d})" % len(raw_email), raw_email)])
    mock.logout.return_value = ("BYE", [b"Logging out"])
    return mock


def test_imap_mock_fetches_and_parses_upwork():
    from freelance_os.ingestion.imap_fetch import fetch_job_alert_emails

    raw = _make_raw_email(
        from_addr="alerts@upwork.com",
        subject="New Upwork Job Alert",
        body=(
            "Build an AI chatbot using LLM and API integration\n"
            "Hourly: $60 - $90/hr\n"
            "https://www.upwork.com/jobs/~imap_test_001\n"
        ),
    )
    mock_conn = _build_mock_imap(raw)
    cfg = {"imap": {"host": "imap.example.com", "user": "user@example.com", "mailbox": "INBOX"}}

    with patch("freelance_os.ingestion.imap_fetch.imaplib.IMAP4_SSL", return_value=mock_conn):
        with patch.dict(os.environ, {"FREELANCE_OS_IMAP_PASSWORD": "app_password"}):
            jobs = fetch_job_alert_emails(cfg, max_emails=10)

    assert len(jobs) >= 1
    assert jobs[0]["source"] == "upwork"
    assert "upwork.com" in (jobs[0].get("source_url") or "")


def test_imap_mock_hourly_budget_parsed():
    from freelance_os.ingestion.imap_fetch import fetch_job_alert_emails

    raw = _make_raw_email(
        from_addr="alerts@upwork.com",
        subject="Upwork Alert",
        body=(
            "Python data pipeline project\n"
            "Hourly: $75 - $100/hr\n"
            "https://www.upwork.com/jobs/~budget_test\n"
        ),
    )
    mock_conn = _build_mock_imap(raw)
    cfg = {"imap": {"host": "imap.example.com", "user": "u@e.com"}}

    with patch("freelance_os.ingestion.imap_fetch.imaplib.IMAP4_SSL", return_value=mock_conn):
        with patch.dict(os.environ, {"FREELANCE_OS_IMAP_PASSWORD": "pw"}):
            jobs = fetch_job_alert_emails(cfg)

    hourly = [j for j in jobs if j.get("budget_type") == "hourly"]
    assert len(hourly) >= 1
    assert hourly[0]["hourly_min"] == 75.0
    assert hourly[0]["hourly_max"] == 100.0


def test_imap_filters_non_alert_senders():
    from freelance_os.ingestion.imap_fetch import fetch_job_alert_emails

    raw = _make_raw_email(
        from_addr="newsletter@unrelated.com",
        subject="Buy our product",
        body="Special offer just for you!",
    )
    mock_conn = _build_mock_imap(raw)
    cfg = {"imap": {"host": "imap.example.com", "user": "u@e.com"}}

    with patch("freelance_os.ingestion.imap_fetch.imaplib.IMAP4_SSL", return_value=mock_conn):
        with patch.dict(os.environ, {"FREELANCE_OS_IMAP_PASSWORD": "pw"}):
            jobs = fetch_job_alert_emails(cfg)

    assert jobs == []


def test_imap_no_password_raises():
    from freelance_os.ingestion.imap_fetch import fetch_job_alert_emails, IMAP_PASSWORD_ENV

    cfg = {"imap": {"host": "imap.example.com", "user": "u@e.com"}}
    clean_env = {k: v for k, v in os.environ.items() if k != IMAP_PASSWORD_ENV}
    with patch.dict(os.environ, clean_env, clear=True):
        with pytest.raises(RuntimeError, match=IMAP_PASSWORD_ENV):
            fetch_job_alert_emails(cfg)


def test_imap_no_host_raises():
    from freelance_os.ingestion.imap_fetch import fetch_job_alert_emails

    cfg = {}
    with patch.dict(os.environ, {"FREELANCE_OS_IMAP_PASSWORD": "pw"}):
        with pytest.raises(RuntimeError, match="IMAP config missing"):
            fetch_job_alert_emails(cfg)


def test_imap_source_override():
    from freelance_os.ingestion.imap_fetch import fetch_job_alert_emails

    raw = _make_raw_email(
        from_addr="alerts@upwork.com",
        subject="Upwork Alert",
        body=(
            "React frontend project\n"
            "Budget: $800 - $1200\n"
            "https://www.upwork.com/jobs/~override_test\n"
        ),
    )
    mock_conn = _build_mock_imap(raw)
    cfg = {"imap": {"host": "imap.example.com", "user": "u@e.com"}}

    with patch("freelance_os.ingestion.imap_fetch.imaplib.IMAP4_SSL", return_value=mock_conn):
        with patch.dict(os.environ, {"FREELANCE_OS_IMAP_PASSWORD": "pw"}):
            jobs = fetch_job_alert_emails(cfg, source_override="manual")

    assert all(j["source"] == "manual" for j in jobs)
