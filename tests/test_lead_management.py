"""Phase 2 — Lead Management tests.

Covers: add-url, add-text, list, show, status (valid + invalid).
"""

import pytest
from typer.testing import CliRunner

from freelance_os.cli import app
from freelance_os.db import get_session
from freelance_os.models import Lead
from freelance_os.schemas import LeadStatus

runner = CliRunner()


# ---------------------------------------------------------------------------
# add-url
# ---------------------------------------------------------------------------


def test_add_url_creates_new_lead():
    result = runner.invoke(app, ["lead", "add-url", "https://example.com/job/1"])
    assert result.exit_code == 0, result.output
    lead_id = int(result.output.strip())
    assert lead_id > 0

    with get_session() as s:
        lead = s.get(Lead, lead_id)

    assert lead is not None
    assert lead.source == "manual_url"
    assert lead.source_url == "https://example.com/job/1"
    assert lead.status == LeadStatus.NEW
    assert lead.description is None


def test_add_url_with_description():
    result = runner.invoke(
        app,
        ["lead", "add-url", "https://example.com/job/2", "--description", "Need a dashboard"],
    )
    assert result.exit_code == 0, result.output
    lead_id = int(result.output.strip())

    with get_session() as s:
        lead = s.get(Lead, lead_id)

    assert lead is not None
    assert lead.description == "Need a dashboard"
    assert lead.status == LeadStatus.NEW


# ---------------------------------------------------------------------------
# add-text
# ---------------------------------------------------------------------------


def test_add_text_creates_lead_with_extracted_title():
    job_text = "Build a React dashboard\nClient: Acme Corp\nBudget: $500 - $1,000\nDetails here."
    result = runner.invoke(
        app,
        ["lead", "add-text", "--source", "upwork", "--text", job_text],
    )
    assert result.exit_code == 0, result.output
    lead_id = int(result.output.strip())

    with get_session() as s:
        lead = s.get(Lead, lead_id)

    assert lead is not None
    assert lead.source == "upwork"
    assert lead.status == LeadStatus.NEW
    assert lead.title == "Build a React dashboard"
    assert lead.budget_min == 500.0
    assert lead.budget_max == 1000.0


def test_add_text_reads_stdin_when_no_text_flag():
    job_text = "Fix Python API performance\nPosted by: TechStart"
    result = runner.invoke(
        app,
        ["lead", "add-text", "--source", "direct"],
        input=job_text,
    )
    assert result.exit_code == 0, result.output
    lead_id = int(result.output.strip())

    with get_session() as s:
        lead = s.get(Lead, lead_id)

    assert lead is not None
    assert lead.title == "Fix Python API performance"
    assert lead.source == "direct"


def test_add_text_minimal_input():
    result = runner.invoke(
        app,
        ["lead", "add-text", "--source", "fiverr", "--text", "Quick logo design"],
    )
    assert result.exit_code == 0, result.output
    lead_id = int(result.output.strip())
    assert lead_id > 0


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def test_list_shows_added_leads():
    runner.invoke(app, ["lead", "add-url", "https://example.com/job/10"])
    runner.invoke(app, ["lead", "add-url", "https://example.com/job/11"])

    result = runner.invoke(app, ["lead", "list"])
    assert result.exit_code == 0, result.output
    assert "manual_url" in result.output
    assert "NEW" in result.output


def test_list_empty_db():
    result = runner.invoke(app, ["lead", "list"])
    assert result.exit_code == 0, result.output
    assert "No leads found" in result.output


def test_list_contains_id_and_status():
    r = runner.invoke(app, ["lead", "add-url", "https://example.com/job/20"])
    lead_id = r.output.strip()

    result = runner.invoke(app, ["lead", "list"])
    assert result.exit_code == 0
    assert lead_id in result.output
    assert "NEW" in result.output


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


def test_show_returns_fields():
    r = runner.invoke(
        app,
        ["lead", "add-url", "https://example.com/job/30", "--description", "Need help"],
    )
    lead_id = r.output.strip()

    result = runner.invoke(app, ["lead", "show", lead_id])
    assert result.exit_code == 0, result.output
    assert "source" in result.output
    assert "manual_url" in result.output
    assert "https://example.com/job/30" in result.output
    assert "Need help" in result.output
    assert "NEW" in result.output


def test_show_not_found():
    result = runner.invoke(app, ["lead", "show", "9999"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


def test_status_updates_valid_status():
    r = runner.invoke(app, ["lead", "add-url", "https://example.com/job/40"])
    lead_id = int(r.output.strip())

    result = runner.invoke(app, ["lead", "status", str(lead_id), "SCORED"])
    assert result.exit_code == 0, result.output
    assert "SCORED" in result.output

    with get_session() as s:
        lead = s.get(Lead, lead_id)
    assert lead.status == LeadStatus.SCORED


def test_status_rejects_invalid_value():
    r = runner.invoke(app, ["lead", "add-url", "https://example.com/job/50"])
    lead_id = r.output.strip()

    result = runner.invoke(app, ["lead", "status", lead_id, "BOGUS_STATUS"])
    assert result.exit_code == 1
    assert "Invalid status" in result.stderr or "Invalid status" in result.output


def test_status_case_insensitive():
    r = runner.invoke(app, ["lead", "add-url", "https://example.com/job/60"])
    lead_id = int(r.output.strip())

    result = runner.invoke(app, ["lead", "status", str(lead_id), "won"])
    assert result.exit_code == 0, result.output

    with get_session() as s:
        lead = s.get(Lead, lead_id)
    assert lead.status == LeadStatus.WON


def test_status_not_found():
    result = runner.invoke(app, ["lead", "status", "9999", "SCORED"])
    assert result.exit_code == 1
