"""Phase 1 tests: skeleton, init, config safety, models."""

import pytest
from pathlib import Path

from freelance_os.models import (
    Lead, ProposalDraft, PortfolioItem, ClientProject, Outcome,
    LeadStatus, Decision, ClientProjectStatus, OutcomeResult,
)
from freelance_os.config import Settings, UnsafeConfigError, load_settings
from freelance_os.db import init_db, reset_engine, get_session


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

def test_lead_status_values():
    assert LeadStatus.NEW == "NEW"
    assert LeadStatus.WON == "WON"
    assert LeadStatus.REJECTED == "REJECTED"


def test_decision_values():
    assert Decision.DRAFT_NOW == "DRAFT_NOW"
    assert Decision.REJECT == "REJECT"


def test_client_project_status_values():
    assert ClientProjectStatus.INTAKE == "INTAKE"
    assert ClientProjectStatus.COMPLETE == "COMPLETE"


def test_outcome_result_values():
    assert OutcomeResult.WON == "WON"
    assert OutcomeResult.LOST == "LOST"


def test_lead_reason_codes_roundtrip():
    lead = Lead(source="test", status=LeadStatus.NEW)
    lead.set_reason_codes(["TECH_STACK_MATCH", "HIGH_BUDGET_FIT"])
    assert lead.get_reason_codes() == ["TECH_STACK_MATCH", "HIGH_BUDGET_FIT"]


def test_lead_reason_codes_empty():
    lead = Lead(source="test", status=LeadStatus.NEW)
    assert lead.get_reason_codes() == []


# ---------------------------------------------------------------------------
# Config safety tests
# ---------------------------------------------------------------------------

def test_safe_defaults_pass():
    settings = Settings({})
    assert settings.require_human_approval is True


def test_safe_config_explicit_pass():
    data = {
        "safety": {
            "allow_browser_automation": False,
            "allow_auto_submit": False,
            "allow_auto_message": False,
            "allow_scraping": False,
            "require_human_approval": True,
        }
    }
    settings = Settings(data)
    assert settings.require_human_approval is True


def test_unsafe_auto_submit_raises():
    with pytest.raises(UnsafeConfigError):
        Settings({"safety": {"allow_auto_submit": True}})


def test_unsafe_browser_automation_raises():
    with pytest.raises(UnsafeConfigError):
        Settings({"safety": {"allow_browser_automation": True}})


def test_unsafe_auto_message_raises():
    with pytest.raises(UnsafeConfigError):
        Settings({"safety": {"allow_auto_message": True}})


def test_unsafe_scraping_raises():
    with pytest.raises(UnsafeConfigError):
        Settings({"safety": {"allow_scraping": True}})


# ---------------------------------------------------------------------------
# Database / init tests
# ---------------------------------------------------------------------------

def test_init_creates_db(tmp_path):
    db_path = tmp_path / "test.sqlite"
    reset_engine()
    init_db(db_path)
    assert db_path.exists()
    reset_engine()


def test_init_idempotent(tmp_path):
    db_path = tmp_path / "test.sqlite"
    reset_engine()
    init_db(db_path)
    reset_engine()
    init_db(db_path)  # second call should not raise
    assert db_path.exists()
    reset_engine()


def test_init_creates_all_tables(tmp_path):
    db_path = tmp_path / "test.sqlite"
    reset_engine()
    init_db(db_path)

    with get_session(db_path) as session:
        from sqlmodel import select
        leads = session.exec(select(Lead)).all()
        assert leads == []

        drafts = session.exec(select(ProposalDraft)).all()
        assert drafts == []

        projects = session.exec(select(ClientProject)).all()
        assert projects == []

        outcomes = session.exec(select(Outcome)).all()
        assert outcomes == []
    reset_engine()
