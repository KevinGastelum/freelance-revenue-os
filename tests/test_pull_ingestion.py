"""Tests for freelance_os.ingestion.pull — normalizers and fetchers.

All tests are deterministic and offline (urllib is mocked).
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO

from freelance_os.ingestion.pull import (
    _empty_lead,
    _parse_salary_string,
    _parse_iso,
    dedupe_leads,
    fetch_leads,
    fetch_remotive,
    fetch_remoteok,
    fetch_jobicy,
    fetch_hn_freelancer,
    SOURCES,
)


# ---------------------------------------------------------------------------
# _parse_salary_string
# ---------------------------------------------------------------------------

def test_parse_empty_salary():
    b = _parse_salary_string("")
    assert b["amount"] is None
    assert b["type"] == "unknown"
    assert b["currency"] == "USD"


def test_parse_fixed_salary_range():
    b = _parse_salary_string("$60k-$90k")
    assert b["amount"] == pytest.approx(75000, rel=0.01)
    assert b["type"] == "fixed"
    assert b["currency"] == "USD"


def test_parse_hourly_rate():
    b = _parse_salary_string("$50/hr")
    assert b["type"] == "hourly"
    assert b["amount"] == pytest.approx(50.0)


def test_parse_eur_currency():
    b = _parse_salary_string("80k EUR")
    assert b["currency"] == "EUR"
    assert b["amount"] == pytest.approx(80000.0)


def test_parse_salary_no_numbers():
    b = _parse_salary_string("competitive salary")
    assert b["amount"] is None


# ---------------------------------------------------------------------------
# _parse_iso
# ---------------------------------------------------------------------------

def test_parse_iso_none():
    assert _parse_iso(None) is None


def test_parse_iso_valid():
    result = _parse_iso("2024-03-15T10:00:00Z")
    assert "2024-03-15" in result


def test_parse_iso_garbage():
    assert _parse_iso("not-a-date") is None


# ---------------------------------------------------------------------------
# _empty_lead
# ---------------------------------------------------------------------------

def test_empty_lead_structure():
    lead = _empty_lead("remotive", "https://example.com/job/1", "Dev job", "Build stuff")
    assert lead["source"] == "remotive"
    assert lead["url"] == "https://example.com/job/1"
    assert lead["title"] == "Dev job"
    assert lead["remote"] is True
    assert lead["budget"]["amount"] is None


# ---------------------------------------------------------------------------
# dedupe_leads
# ---------------------------------------------------------------------------

def test_dedupe_removes_duplicate_urls():
    leads = [
        _empty_lead("a", "https://x.com/1", "Job A", "desc"),
        _empty_lead("b", "https://x.com/1", "Job A dup", "desc"),
        _empty_lead("c", "https://x.com/2", "Job B", "desc"),
    ]
    result = dedupe_leads(leads)
    assert len(result) == 2
    urls = [l["url"] for l in result]
    assert "https://x.com/1" in urls
    assert "https://x.com/2" in urls


def test_dedupe_keeps_no_url_leads():
    leads = [
        _empty_lead("a", "", "Anon 1", ""),
        _empty_lead("b", "", "Anon 2", ""),
    ]
    result = dedupe_leads(leads)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# fetch_remotive (mocked urllib)
# ---------------------------------------------------------------------------

def _make_urlopen_mock(payload: dict):
    """Return a context manager mock that returns payload JSON bytes."""
    raw = json.dumps(payload).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = raw
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_fetch_remotive_normalises_jobs():
    payload = {
        "jobs": [
            {
                "id": 1,
                "url": "https://remotive.com/job/1",
                "title": "Senior Python Dev",
                "description": "Build a FastAPI service. Python, PostgreSQL.",
                "salary": "$80k-$120k",
                "tags": ["python", "fastapi"],
                "publication_date": "2024-03-01T00:00:00Z",
                "candidate_required_location": "Worldwide",
            }
        ]
    }
    with patch("freelance_os.ingestion.pull.urllib.request.urlopen",
               return_value=_make_urlopen_mock(payload)):
        leads = fetch_remotive()

    assert len(leads) == 1
    lead = leads[0]
    assert lead["source"] == "remotive"
    assert "python" in lead["skills"]
    assert lead["budget"]["amount"] == pytest.approx(100000.0, rel=0.01)
    assert lead["budget"]["type"] == "fixed"
    assert lead["posted_at"] is not None


def test_fetch_remotive_handles_network_error():
    with patch("freelance_os.ingestion.pull.urllib.request.urlopen",
               side_effect=Exception("timeout")):
        leads = fetch_remotive()
    assert leads == []


def test_fetch_remotive_handles_no_budget():
    payload = {"jobs": [
        {"url": "https://remotive.com/job/2", "title": "Job", "description": "desc",
         "salary": "", "tags": [], "publication_date": None}
    ]}
    with patch("freelance_os.ingestion.pull.urllib.request.urlopen",
               return_value=_make_urlopen_mock(payload)):
        leads = fetch_remotive()
    assert leads[0]["budget"]["amount"] is None


# ---------------------------------------------------------------------------
# fetch_remoteok (mocked urllib)
# ---------------------------------------------------------------------------

def test_fetch_remoteok_skips_first_element():
    payload = [
        {"legal": "This is a notice — skip me"},
        {
            "id": "42",
            "url": "https://remoteok.com/remote-jobs/42",
            "position": "Go Engineer",
            "description": "Build microservices in Go.",
            "salary_min": 80000,
            "salary_max": 120000,
            "tags": ["go", "microservices"],
            "date": "2024-03-10T00:00:00Z",
        }
    ]
    with patch("freelance_os.ingestion.pull.urllib.request.urlopen",
               return_value=_make_urlopen_mock(payload)):
        leads = fetch_remoteok()

    assert len(leads) == 1
    lead = leads[0]
    assert lead["source"] == "remoteok"
    assert lead["budget"]["amount"] == pytest.approx(100000.0)
    assert "go" in lead["skills"]


def test_fetch_remoteok_handles_error():
    with patch("freelance_os.ingestion.pull.urllib.request.urlopen",
               side_effect=Exception("connection refused")):
        leads = fetch_remoteok()
    assert leads == []


# ---------------------------------------------------------------------------
# fetch_jobicy (mocked urllib)
# ---------------------------------------------------------------------------

def test_fetch_jobicy_normalises_jobs():
    payload = {
        "jobs": [
            {
                "url": "https://jobicy.com/jobs/1",
                "jobTitle": "Data Analyst",
                "jobDescription": "Analyze datasets with Python and SQL.",
                "annualSalaryMin": 60000,
                "annualSalaryMax": 80000,
                "jobIndustry": ["data", "analytics"],
                "pubDate": "2024-03-05T00:00:00Z",
                "jobGeo": "Remote",
            }
        ]
    }
    with patch("freelance_os.ingestion.pull.urllib.request.urlopen",
               return_value=_make_urlopen_mock(payload)):
        leads = fetch_jobicy()

    assert len(leads) == 1
    lead = leads[0]
    assert lead["source"] == "jobicy"
    assert lead["budget"]["amount"] == pytest.approx(70000.0)
    assert "data" in lead["skills"]


def test_fetch_jobicy_handles_error():
    with patch("freelance_os.ingestion.pull.urllib.request.urlopen",
               side_effect=OSError("network error")):
        leads = fetch_jobicy()
    assert leads == []


# ---------------------------------------------------------------------------
# fetch_hn_freelancer (mocked urllib)
# ---------------------------------------------------------------------------

def test_fetch_hn_freelancer_filters_non_hiring():
    thread_payload = {
        "hits": [
            {"objectID": "123", "title": "Ask HN: Freelancer? Seeking freelancer? 2024"}
        ]
    }
    comments_payload = {
        "hits": [
            {
                "objectID": "200",
                "comment_text": (
                    "SEEKING FREELANCER | Python automation | Remote | $100-200/hr\n"
                    "We need a Python developer to automate our workflow."
                ),
                "created_at": "2024-03-01T00:00:00Z",
            },
            {
                "objectID": "201",
                "comment_text": "AVAILABLE | I am a frontend developer looking for work.",
                "created_at": "2024-03-01T00:00:00Z",
            },
        ]
    }

    call_count = [0]

    def mock_urlopen(req, timeout=10):
        call_count[0] += 1
        if call_count[0] == 1:
            return _make_urlopen_mock(thread_payload)
        return _make_urlopen_mock(comments_payload)

    with patch("freelance_os.ingestion.pull.urllib.request.urlopen", side_effect=mock_urlopen):
        leads = fetch_hn_freelancer()

    # Only the "SEEKING FREELANCER" comment should pass
    assert len(leads) == 1
    assert leads[0]["source"] == "hn_freelancer"
    assert "news.ycombinator.com" in leads[0]["url"]


def test_fetch_hn_freelancer_no_thread_returns_empty():
    empty_thread = {"hits": []}
    with patch("freelance_os.ingestion.pull.urllib.request.urlopen",
               return_value=_make_urlopen_mock(empty_thread)):
        leads = fetch_hn_freelancer()
    assert leads == []


def test_fetch_hn_freelancer_handles_error():
    with patch("freelance_os.ingestion.pull.urllib.request.urlopen",
               side_effect=Exception("timeout")):
        leads = fetch_hn_freelancer()
    assert leads == []


# ---------------------------------------------------------------------------
# fetch_leads dispatcher
# ---------------------------------------------------------------------------

def test_fetch_leads_dispatches_named_sources():
    mock_lead = _empty_lead("remotive", "https://example.com/1", "Job", "desc")
    from freelance_os.ingestion import pull as _pull_mod
    with patch.dict(_pull_mod.SOURCES, {"remotive": lambda: [mock_lead]}):
        leads = fetch_leads(["remotive"])
    assert len(leads) == 1
    assert leads[0]["source"] == "remotive"


def test_fetch_leads_unknown_source_skipped():
    leads = fetch_leads(["nonexistent_source"])
    assert leads == []


def test_fetch_leads_dedupes_across_sources():
    lead_a = _empty_lead("remotive", "https://x.com/1", "Job", "desc")
    lead_b = _empty_lead("remoteok", "https://x.com/1", "Job dup", "desc")

    from freelance_os.ingestion import pull as _pull_mod
    with patch.dict(_pull_mod.SOURCES, {"remotive": lambda: [lead_a], "remoteok": lambda: [lead_b]}):
        leads = fetch_leads(["remotive", "remoteok"])

    assert len(leads) == 1


def test_fetch_leads_one_source_fails_rest_continue():
    good_lead = _empty_lead("jobicy", "https://jobicy.com/1", "Job", "desc")
    from freelance_os.ingestion import pull as _pull_mod
    with patch.dict(_pull_mod.SOURCES, {
        "remotive": lambda: [],
        "remoteok": lambda: [],
        "jobicy": lambda: [good_lead],
        "hn": lambda: [],
    }):
        leads = fetch_leads()

    assert len(leads) == 1
    assert leads[0]["source"] == "jobicy"


# ---------------------------------------------------------------------------
# SOURCES registry
# ---------------------------------------------------------------------------

def test_sources_registry_has_expected_keys():
    assert "remotive" in SOURCES
    assert "remoteok" in SOURCES
    assert "jobicy" in SOURCES
    assert "hn" in SOURCES
