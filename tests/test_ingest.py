"""Tests for freelance_os.ingestion.ingest — operator CSV/JSON normalizer and ingest CLI command.

All tests are deterministic and offline (no network calls).
"""

import csv
import io
import json
import sys
from pathlib import Path

import pytest

from freelance_os.ingestion.ingest import (
    load_leads,
    _normalize_row,
    _parse_skills,
    _is_already_normalized,
    _pick,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(path: Path, rows: list, fieldnames: list = None):
    if fieldnames is None:
        # Collect all keys across all rows
        seen = {}
        for row in rows:
            for k in row:
                seen[k] = None
        fieldnames = list(seen)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# _pick
# ---------------------------------------------------------------------------

def test_pick_finds_first_alias():
    row = {"LINK": "https://ex.com", "url": "https://other.com"}
    assert _pick(row, ("url", "link")) == "https://other.com"


def test_pick_falls_back_to_alias():
    row = {"link": "https://ex.com"}
    assert _pick(row, ("url", "link")) == "https://ex.com"


def test_pick_returns_default_when_absent():
    assert _pick({}, ("url", "link"), default="x") == "x"


def test_pick_skips_empty_string():
    row = {"url": "", "link": "https://ex.com/real"}
    assert _pick(row, ("url", "link")) == "https://ex.com/real"


# ---------------------------------------------------------------------------
# _parse_skills
# ---------------------------------------------------------------------------

def test_parse_skills_comma_string():
    assert _parse_skills("Python, Django, REST") == ["Python", "Django", "REST"]


def test_parse_skills_list():
    assert _parse_skills(["Go", "Docker"]) == ["Go", "Docker"]


def test_parse_skills_empty():
    assert _parse_skills("") == []
    assert _parse_skills(None) == []


# ---------------------------------------------------------------------------
# _is_already_normalized
# ---------------------------------------------------------------------------

def test_is_normalized_detects_budget_dict():
    row = {"budget": {"amount": 100.0, "currency": "USD", "type": "fixed"}}
    assert _is_already_normalized(row)


def test_is_not_normalized_with_budget_string():
    row = {"budget": "$5000"}
    assert not _is_already_normalized(row)


# ---------------------------------------------------------------------------
# _normalize_row — unit tests
# ---------------------------------------------------------------------------

def test_normalize_row_skips_no_title_no_desc():
    row = {"url": "https://ex.com/x", "budget": "$1000"}
    assert _normalize_row(row, "test") is None


def test_normalize_row_keeps_title_only():
    row = {"title": "Some job", "url": "https://ex.com/t"}
    lead = _normalize_row(row, "test")
    assert lead is not None
    assert lead["title"] == "Some job"


def test_normalize_row_keeps_desc_only():
    row = {"description": "Long description here."}
    lead = _normalize_row(row, "test")
    assert lead is not None
    assert lead["description"] == "Long description here."


def test_normalize_row_url_aliases():
    for alias in ("url", "link", "job_url", "job_link"):
        row = {"title": "T", "description": "D", alias: "https://ex.com/alias"}
        lead = _normalize_row(row, "test")
        assert lead["url"] == "https://ex.com/alias", f"alias {alias!r} failed"


def test_normalize_row_desc_aliases():
    for alias in ("description", "desc", "body", "details", "summary"):
        row = {"title": "T", alias: "Some text"}
        lead = _normalize_row(row, "test")
        assert lead["description"] == "Some text", f"alias {alias!r} failed"


def test_normalize_row_budget_string_fixed():
    row = {"title": "T", "description": "D", "budget": "$5000"}
    lead = _normalize_row(row, "test")
    assert lead["budget"]["amount"] == pytest.approx(5000.0)
    assert lead["budget"]["type"] == "fixed"


def test_normalize_row_budget_rate_alias_hourly():
    row = {"title": "T", "description": "D", "rate": "$75/hr"}
    lead = _normalize_row(row, "test")
    assert lead["budget"]["type"] == "hourly"
    assert lead["budget"]["amount"] == pytest.approx(75.0)


def test_normalize_row_budget_salary_alias():
    row = {"title": "T", "description": "D", "salary": "€60k-80k EUR"}
    lead = _normalize_row(row, "test")
    assert lead["budget"]["currency"] == "EUR"
    assert lead["budget"]["amount"] == pytest.approx(70000.0)


def test_normalize_row_budget_numeric():
    row = {"title": "T", "description": "D", "budget": 2500}
    lead = _normalize_row(row, "test")
    assert lead["budget"]["amount"] == pytest.approx(2500.0)
    assert lead["budget"]["type"] == "fixed"


def test_normalize_row_default_source():
    row = {"title": "T", "description": "D"}
    lead = _normalize_row(row, "ingest:myfile.csv")
    assert lead["source"] == "ingest:myfile.csv"


def test_normalize_row_custom_source_in_row():
    row = {"title": "T", "description": "D", "source": "upwork"}
    lead = _normalize_row(row, "ingest:myfile.csv")
    assert lead["source"] == "upwork"


def test_normalize_row_client_fields():
    row = {
        "title": "T", "description": "D",
        "country": "US", "rating": "4.8", "hires": "12",
        "payment_verified": "true", "total_spend": "$5,000",
    }
    lead = _normalize_row(row, "test")
    assert lead["client"]["country"] == "US"
    assert lead["client"]["rating"] == pytest.approx(4.8)
    assert lead["client"]["hires"] == 12
    assert lead["client"]["payment_verified"] is True
    assert lead["client"]["total_spend"] == pytest.approx(5000.0)


def test_normalize_row_passthrough_normalized():
    already = {
        "source": "upwork",
        "url": "https://ex.com/pass",
        "title": "Pre-scored",
        "description": "Already shaped.",
        "budget": {"amount": 3000.0, "currency": "USD", "type": "fixed"},
        "skills": ["Python"],
        "posted_at": None,
        "client": {},
        "location": None,
        "remote": True,
    }
    lead = _normalize_row(already, "ingest:x.json")
    assert lead["budget"]["amount"] == pytest.approx(3000.0)
    assert lead["source"] == "upwork"


# ---------------------------------------------------------------------------
# load_leads — CSV
# ---------------------------------------------------------------------------

def test_load_csv_basic(tmp_path):
    rows = [
        {"title": "Python Dev", "description": "Build an API.", "url": "https://ex.com/1", "budget": "$5000"},
        {"title": "Data Eng", "description": "ETL pipeline.", "url": "https://ex.com/2", "rate": "$60/hr"},
        {"title": "", "description": "", "url": "https://ex.com/skip"},  # skipped
    ]
    csv_file = tmp_path / "leads.csv"
    _write_csv(csv_file, rows)
    leads = load_leads(csv_file)
    assert len(leads) == 2


def test_load_csv_fixed_budget(tmp_path):
    row = {"title": "Python Dev", "description": "Build REST API.", "url": "https://ex.com/fb", "budget": "$5000"}
    csv_file = tmp_path / "leads.csv"
    _write_csv(csv_file, [row])
    leads = load_leads(csv_file)
    assert leads[0]["budget"]["amount"] == pytest.approx(5000.0)
    assert leads[0]["budget"]["type"] == "fixed"
    assert leads[0]["budget"]["currency"] == "USD"


def test_load_csv_hourly_rate_alias(tmp_path):
    row = {"title": "Hourly dev", "description": "Some work.", "link": "https://ex.com/hr", "rate": "$75/hr"}
    csv_file = tmp_path / "leads.csv"
    _write_csv(csv_file, [row])
    leads = load_leads(csv_file, fmt="csv")
    assert leads[0]["budget"]["type"] == "hourly"
    assert leads[0]["budget"]["amount"] == pytest.approx(75.0)
    assert leads[0]["url"] == "https://ex.com/hr"


def test_load_csv_missing_budget(tmp_path):
    row = {"title": "Fix script", "description": "One-liner fix.", "url": "https://ex.com/nb"}
    csv_file = tmp_path / "leads.csv"
    _write_csv(csv_file, [row])
    leads = load_leads(csv_file)
    assert leads[0]["budget"]["amount"] is None
    assert leads[0]["budget"]["type"] == "unknown"


def test_load_csv_skips_empty_title_and_desc(tmp_path):
    rows = [
        {"title": "", "description": "", "url": "https://ex.com/skip"},
        {"title": "Valid Lead", "description": "Has a title.", "url": "https://ex.com/keep"},
    ]
    csv_file = tmp_path / "leads.csv"
    _write_csv(csv_file, rows)
    leads = load_leads(csv_file)
    assert len(leads) == 1
    assert leads[0]["title"] == "Valid Lead"


def test_load_csv_title_only_not_skipped(tmp_path):
    row = {"title": "Tiny task", "description": "", "url": "https://ex.com/tt"}
    csv_file = tmp_path / "leads.csv"
    _write_csv(csv_file, [row])
    leads = load_leads(csv_file)
    assert len(leads) == 1


def test_load_csv_default_source(tmp_path):
    row = {"title": "Test Lead", "description": "Desc.", "url": "https://ex.com/src"}
    csv_file = tmp_path / "myfile.csv"
    _write_csv(csv_file, [row])
    leads = load_leads(csv_file)
    assert leads[0]["source"] == "ingest:myfile.csv"


def test_load_csv_custom_source(tmp_path):
    row = {"title": "Test", "description": "D.", "url": "https://ex.com/cs", "source": "upwork"}
    csv_file = tmp_path / "leads.csv"
    _write_csv(csv_file, [row])
    leads = load_leads(csv_file)
    assert leads[0]["source"] == "upwork"


def test_load_csv_skills_comma_separated(tmp_path):
    row = {"title": "Dev", "description": "Work.", "url": "https://ex.com/sk", "skills": "Python, Django, REST"}
    csv_file = tmp_path / "leads.csv"
    _write_csv(csv_file, [row])
    leads = load_leads(csv_file)
    assert "Python" in leads[0]["skills"]
    assert "Django" in leads[0]["skills"]


def test_load_csv_skills_tags_alias(tmp_path):
    row = {"title": "Dev", "description": "Work.", "url": "https://ex.com/tg", "tags": "Go, Docker"}
    csv_file = tmp_path / "leads.csv"
    _write_csv(csv_file, [row])
    leads = load_leads(csv_file)
    assert "Go" in leads[0]["skills"]


def test_load_csv_dedupes_by_url(tmp_path):
    rows = [
        {"title": "Job A", "description": "Desc.", "url": "https://ex.com/dup"},
        {"title": "Job B", "description": "Desc.", "url": "https://ex.com/dup"},
    ]
    csv_file = tmp_path / "leads.csv"
    _write_csv(csv_file, rows)
    leads = load_leads(csv_file)
    assert len(leads) == 1


def test_load_csv_no_url_keeps_both(tmp_path):
    rows = [
        {"title": "No URL A", "description": "Desc A."},
        {"title": "No URL B", "description": "Desc B."},
    ]
    csv_file = tmp_path / "leads.csv"
    _write_csv(csv_file, rows)
    leads = load_leads(csv_file)
    assert len(leads) == 2


# ---------------------------------------------------------------------------
# load_leads — JSON
# ---------------------------------------------------------------------------

def test_load_json_list(tmp_path):
    data = [
        {"title": "Lead 1", "description": "Desc 1.", "url": "https://ex.com/j1", "budget": "$3000"},
        {"title": "Lead 2", "description": "Desc 2.", "url": "https://ex.com/j2", "rate": "$50/hr"},
    ]
    json_file = tmp_path / "leads.json"
    json_file.write_text(json.dumps(data), encoding="utf-8")
    leads = load_leads(json_file)
    assert len(leads) == 2
    assert leads[0]["title"] == "Lead 1"


def test_load_json_dict_with_leads_key(tmp_path):
    data = {"leads": [{"title": "Lead X", "description": "Desc.", "url": "https://ex.com/lx"}]}
    json_file = tmp_path / "leads.json"
    json_file.write_text(json.dumps(data), encoding="utf-8")
    leads = load_leads(json_file)
    assert len(leads) == 1
    assert leads[0]["title"] == "Lead X"


def test_load_json_already_normalized_passthrough(tmp_path):
    data = [{
        "source": "upwork",
        "url": "https://ex.com/norm",
        "title": "Normalized Lead",
        "description": "Already in lead-dict shape.",
        "budget": {"amount": 2500.0, "currency": "USD", "type": "fixed"},
        "skills": ["Python"],
        "posted_at": None,
        "client": {},
        "location": None,
        "remote": True,
    }]
    json_file = tmp_path / "leads.json"
    json_file.write_text(json.dumps(data), encoding="utf-8")
    leads = load_leads(json_file)
    assert leads[0]["budget"]["amount"] == pytest.approx(2500.0)
    assert leads[0]["budget"]["type"] == "fixed"
    assert leads[0]["source"] == "upwork"


def test_load_json_explicit_fmt_override(tmp_path):
    data = [{"title": "Fmt Lead", "description": "Desc.", "url": "https://ex.com/fmt"}]
    txt_file = tmp_path / "leads.txt"
    txt_file.write_text(json.dumps(data), encoding="utf-8")
    leads = load_leads(txt_file, fmt="json")
    assert len(leads) == 1


def test_load_json_auto_detects_extension(tmp_path):
    data = [{"title": "Auto JSON", "description": "Desc.", "url": "https://ex.com/auto"}]
    json_file = tmp_path / "leads.json"
    json_file.write_text(json.dumps(data), encoding="utf-8")
    leads = load_leads(json_file, fmt="auto")
    assert leads[0]["title"] == "Auto JSON"


# ---------------------------------------------------------------------------
# score_rank_render integration (direct call + CliRunner)
# ---------------------------------------------------------------------------

def _make_leads():
    return [
        {
            "source": "test",
            "url": "https://ex.com/sr1",
            "title": "Python API Developer",
            "description": "Build a REST API integration with FastAPI and PostgreSQL. Medium scope.",
            "budget": {"amount": 5000.0, "currency": "USD", "type": "fixed"},
            "skills": ["Python"],
            "posted_at": None,
            "client": {"payment_verified": True, "rating": 4.8},
            "location": None,
            "remote": True,
        },
        {
            "source": "test",
            "url": "https://ex.com/sr2",
            "title": "Quick script fix",
            "description": "Fix a bug in a small Python script.",
            "budget": {"amount": None, "currency": "USD", "type": "unknown"},
            "skills": [],
            "posted_at": None,
            "client": {},
            "location": None,
            "remote": True,
        },
    ]


def test_score_rank_render_json_output(tmp_path):
    """emit_json=True writes valid JSON to stdout, then exits 0."""
    import typer
    from freelance_os.scoring.pipeline import score_rank_render
    from rich.console import Console

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        with pytest.raises(typer.Exit) as exc_info:
            score_rank_render(
                _make_leads(),
                reputation_mode=False,
                min_margin=0.0,
                limit=10,
                emit_json=True,
                draft_top=0,
                persist=False,
                config=None,
                console=Console(file=io.StringIO()),
            )
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    assert exc_info.value.exit_code == 0
    data = json.loads(output)
    assert len(data) == 2
    assert "final_score" in data[0]
    assert "margin" in data[0]
    # Descending order
    assert data[0]["final_score"] >= data[1]["final_score"]


def test_score_rank_render_filters_min_margin():
    """min_margin > 0 removes leads that don't qualify; empty result exits 0."""
    import typer
    from freelance_os.scoring.pipeline import score_rank_render
    from rich.console import Console

    # A lead with no budget will score margin=0, so a high min_margin should filter it out.
    leads = [
        {
            "source": "test", "url": "https://ex.com/fm",
            "title": "No budget job", "description": "Some work.",
            "budget": {"amount": None, "currency": "USD", "type": "unknown"},
            "skills": [], "posted_at": None, "client": {}, "location": None, "remote": True,
        }
    ]
    captured = io.StringIO()
    con = Console(file=captured, highlight=False)
    with pytest.raises(typer.Exit) as exc_info:
        score_rank_render(
            leads,
            reputation_mode=False,
            min_margin=500.0,  # extremely high — nothing can pass
            limit=10,
            emit_json=False,
            draft_top=0,
            persist=False,
            config=None,
            console=con,
        )
    assert exc_info.value.exit_code == 0
    assert "No leads passed" in captured.getvalue()


# ---------------------------------------------------------------------------
# CLI integration (CliRunner)
# ---------------------------------------------------------------------------

def test_ingest_cli_csv_json_output(tmp_path):
    """freelance-os ingest <csv> --json emits a valid JSON ranked list."""
    from typer.testing import CliRunner
    from freelance_os.cli import app

    rows = [
        {"title": "Backend Dev", "description": "Build REST API with Django.", "url": "https://ex.com/c1", "budget": "$4000"},
        {"title": "Data pipeline", "description": "ETL pipeline setup in Python.", "url": "https://ex.com/c2", "rate": "$60/hr"},
    ]
    csv_file = tmp_path / "cli_test.csv"
    _write_csv(csv_file, rows)

    runner = CliRunner()
    result = runner.invoke(app, ["ingest", str(csv_file), "--json", "--draft-top", "0"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert len(data) == 2
    assert all("final_score" in d for d in data)
    # Verify descending score order
    scores = [d["final_score"] for d in data]
    assert scores == sorted(scores, reverse=True)


def test_ingest_cli_sample_fixture():
    """freelance-os ingest tests/fixtures/sample_leads.csv --json produces scored output."""
    from typer.testing import CliRunner
    from freelance_os.cli import app

    fixture = Path(__file__).parent / "fixtures" / "sample_leads.csv"
    runner = CliRunner()
    result = runner.invoke(app, ["ingest", str(fixture), "--json", "--draft-top", "0"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert len(data) >= 3  # 4 rows, 1 very short description might score OK
    assert all("final_score" in d for d in data)


def test_ingest_cli_missing_file(tmp_path):
    """ingest with a non-existent file exits with code 1."""
    from typer.testing import CliRunner
    from freelance_os.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["ingest", str(tmp_path / "nope.csv")])
    assert result.exit_code == 1


def test_ingest_cli_json_format_flag(tmp_path):
    """ingest --format json reads a JSON file."""
    from typer.testing import CliRunner
    from freelance_os.cli import app

    data = [{"title": "ML Engineer", "description": "Build classification model.", "url": "https://ex.com/ml1", "budget": "$8000"}]
    json_file = tmp_path / "leads.json"
    json_file.write_text(json.dumps(data), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["ingest", str(json_file), "--json", "--draft-top", "0"])
    assert result.exit_code == 0, result.output
    out = json.loads(result.output)
    assert out[0]["title"] == "ML Engineer"
    assert "final_score" in out[0]
