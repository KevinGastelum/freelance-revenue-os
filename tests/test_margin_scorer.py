"""Tests for freelance_os.scoring.margin — AI-leverage margin scorer.

All tests are deterministic and offline.
"""

import math
import pytest

from freelance_os.scoring.margin import (
    _estimate_effort_hours,
    _estimate_confidence,
    _compute_budget_usd,
    _reputation_value,
    _to_usd,
    score_lead,
    _CURRENCY_TO_USD,
    _norm_margin,
    _LOG_MARGIN_FLOOR,
    _LOG_MARGIN_CAP,
)


def _make_lead(**kwargs):
    base = {
        "source": "test",
        "url": "https://example.com/job",
        "title": "",
        "description": "",
        "budget": {"amount": None, "currency": "USD", "type": "fixed"},
        "skills": [],
        "posted_at": None,
        "client": {},
        "location": None,
        "remote": True,
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# _estimate_effort_hours
# ---------------------------------------------------------------------------

def test_big_scope_word_raises_effort():
    # "rebuild" and "platform" are both in _BIG_SCOPE; word-count clamping must not override them
    hours = _estimate_effort_hours(
        "We need to rebuild the entire platform from scratch, including the full architecture.",
        "Platform rebuild",
    )
    assert hours >= 40


def test_small_scope_word_lowers_effort():
    hours = _estimate_effort_hours("Quick fix for a minor bug in the login page.", "Bug fix")
    assert hours <= 8


def test_medium_scope_falls_between():
    hours = _estimate_effort_hours("Build a REST API integration with a third-party service.", "API integration")
    assert 8 <= hours <= 25


def test_effort_without_scope_keywords():
    hours = _estimate_effort_hours("We need some help with our project.")
    assert hours > 0


def test_long_description_raises_effort():
    # No scope keyword, > 300 words -> word-count heuristic should push to 20h
    long_desc = "we require some help with various things and there is lots of work to do " * 30
    hours = _estimate_effort_hours(long_desc)
    assert hours >= 20


# ---------------------------------------------------------------------------
# _estimate_confidence
# ---------------------------------------------------------------------------

def test_confidence_high_with_budget_and_verified():
    lead = _make_lead(
        description="We need a Python developer " * 30,
        budget={"amount": 5000, "currency": "USD", "type": "fixed"},
        client={"payment_verified": True, "rating": 4.8},
        skills=["python"],
        posted_at="2024-03-01",
    )
    conf = _estimate_confidence(lead)
    assert conf >= 0.7


def test_confidence_low_with_no_budget():
    lead = _make_lead(
        description="Quick task",
        budget={"amount": None, "currency": "USD", "type": "unknown"},
        client={},
    )
    conf = _estimate_confidence(lead)
    assert conf < 0.35


def test_confidence_capped_at_one():
    lead = _make_lead(
        description="Very detailed spec " * 50,
        budget={"amount": 9999, "currency": "USD", "type": "fixed"},
        client={"payment_verified": True, "rating": 5.0},
        skills=["python", "react"],
        posted_at="2024-03-01",
    )
    assert _estimate_confidence(lead) <= 1.0


# ---------------------------------------------------------------------------
# _to_usd
# ---------------------------------------------------------------------------

def test_to_usd_identity_for_usd():
    assert _to_usd(1000.0, "USD") == pytest.approx(1000.0)


def test_to_usd_converts_eur():
    result = _to_usd(1000.0, "EUR")
    assert result == pytest.approx(1000.0 * _CURRENCY_TO_USD["EUR"])


def test_to_usd_unknown_currency_defaults_to_1():
    assert _to_usd(500.0, "XYZ") == pytest.approx(500.0)


# ---------------------------------------------------------------------------
# _compute_budget_usd
# ---------------------------------------------------------------------------

def test_compute_budget_usd_fixed():
    lead = _make_lead(budget={"amount": 2000.0, "currency": "USD", "type": "fixed"})
    assert _compute_budget_usd(lead) == pytest.approx(2000.0)


def test_compute_budget_usd_hourly_multiplied():
    lead = _make_lead(budget={"amount": 50.0, "currency": "USD", "type": "hourly"})
    result = _compute_budget_usd(lead, assumed_hours=20.0)
    assert result == pytest.approx(50.0 * 20.0)


def test_compute_budget_usd_none_returns_zero():
    lead = _make_lead(budget={"amount": None, "currency": "USD", "type": "unknown"})
    assert _compute_budget_usd(lead) == 0.0


def test_compute_budget_usd_eur_converted():
    lead = _make_lead(budget={"amount": 1000.0, "currency": "EUR", "type": "fixed"})
    result = _compute_budget_usd(lead)
    assert result > 1000.0  # EUR > USD


# ---------------------------------------------------------------------------
# _reputation_value
# ---------------------------------------------------------------------------

def test_reputation_boosts_easy_win():
    lead = _make_lead(
        title="Simple quick fix",
        description="Easy small task.",
        client={"payment_verified": True},
    )
    rep = _reputation_value(lead)
    assert rep >= 0.6


def test_reputation_penalises_vague_tiny_desc():
    lead = _make_lead(title="Job", description="do it")
    rep = _reputation_value(lead)
    assert rep < 0.5


def test_reputation_zero_clamped():
    lead = _make_lead(title="", description="x")  # < 15 words
    rep = _reputation_value(lead)
    assert 0.0 <= rep <= 1.0


# ---------------------------------------------------------------------------
# score_lead (integration)
# ---------------------------------------------------------------------------

def test_score_lead_returns_all_fields():
    lead = _make_lead(
        title="Build a Python API",
        description="Implement a FastAPI backend with database integration. Clear scope.",
        budget={"amount": 1500.0, "currency": "USD", "type": "fixed"},
        client={"payment_verified": True, "rating": 4.7},
        skills=["python"],
        posted_at="2024-03-01",
    )
    result = score_lead(lead)
    for field in ("effort_hours", "confidence", "budget_usd", "margin", "reputation_value",
                  "final_score", "verdict"):
        assert field in result


def test_score_lead_final_score_between_zero_and_one():
    lead = _make_lead(
        title="Fix a small bug",
        description="There is a minor bug in the login page. Quick fix needed.",
        budget={"amount": 200.0, "currency": "USD", "type": "fixed"},
    )
    result = score_lead(lead)
    assert 0.0 <= result["final_score"] <= 1.0


def test_score_lead_reputation_mode_does_not_down_rank_cheap_gig():
    cheap_lead = _make_lead(
        title="Simple quick fix",
        description="Small bug fix, should be easy and quick.",
        budget={"amount": 150.0, "currency": "USD", "type": "fixed"},
        client={"payment_verified": True},
    )
    expensive_lead = _make_lead(
        title="Enterprise platform migration",
        description="Migrate our monolith to microservices. Full architecture overhaul.",
        budget={"amount": None, "currency": "USD", "type": "unknown"},
    )
    cheap_score = score_lead(cheap_lead, reputation_mode=True)["final_score"]
    expensive_score = score_lead(expensive_lead, reputation_mode=True)["final_score"]
    # With reputation mode ON, the cheap easy gig should not be ranked far below
    # the large vague gig (which has no budget and is high-effort)
    assert cheap_score >= expensive_score * 0.5, (
        f"Cheap easy gig ({cheap_score:.3f}) ranked too far below "
        f"vague large gig ({expensive_score:.3f}) in reputation mode"
    )


def test_score_lead_high_budget_raises_score():
    low_budget = _make_lead(
        title="Write a script",
        description="Create an automation script for data processing.",
        budget={"amount": 100.0, "currency": "USD", "type": "fixed"},
    )
    high_budget = _make_lead(
        title="Write a script",
        description="Create an automation script for data processing.",
        budget={"amount": 5000.0, "currency": "USD", "type": "fixed"},
    )
    low_score = score_lead(low_budget, reputation_mode=False)["final_score"]
    high_score = score_lead(high_budget, reputation_mode=False)["final_score"]
    assert high_score > low_score


def test_score_lead_verdict_format():
    lead = _make_lead(
        title="Quick Fix",
        description="A quick, simple bug fix.",
        budget={"amount": 200.0, "currency": "USD", "type": "fixed"},
    )
    result = score_lead(lead)
    verdict = result["verdict"]
    assert "quick buck" in verdict
    assert "h," in verdict
    assert "conf" in verdict


def test_score_lead_no_budget_verdict_shows_question_mark():
    lead = _make_lead(title="Unknown Budget Job", description="No budget info provided.")
    result = score_lead(lead)
    assert "?" in result["verdict"]


def test_score_lead_margin_zero_when_no_budget():
    lead = _make_lead(description="No budget info here.")
    result = score_lead(lead)
    assert result["budget_usd"] == 0.0
    assert result["margin"] == 0.0


def test_score_lead_custom_weights_no_reputation_mode():
    lead = _make_lead(
        title="Large platform rebuild",
        description="Rebuild the entire enterprise platform from scratch.",
        budget={"amount": 20000.0, "currency": "USD", "type": "fixed"},
    )
    result = score_lead(lead, w_margin=1.0, w_rep=0.0, w_conf=0.0, reputation_mode=False)
    # With all weight on margin, final_score == log-normalized margin
    expected_norm = _norm_margin(result["margin"])
    assert result["final_score"] == pytest.approx(expected_norm, rel=0.001)


# ---------------------------------------------------------------------------
# FIX 1 — log-curve margin normalization
# ---------------------------------------------------------------------------

def test_norm_margin_strictly_increasing():
    values = [50, 150, 300, 600, 1000]
    norms = [_norm_margin(v) for v in values]
    for i in range(len(norms) - 1):
        assert norms[i] < norms[i + 1], (
            f"norm_margin not strictly increasing at {values[i]} vs {values[i+1]}: "
            f"{norms[i]:.4f} >= {norms[i+1]:.4f}"
        )


def test_norm_margin_low_clearly_below_high():
    # $30/hr (below FLOOR) should score clearly below $300/hr
    assert _norm_margin(30) < _norm_margin(300) * 0.5


def test_norm_margin_at_or_above_cap_is_one():
    assert _norm_margin(1000) == pytest.approx(1.0)
    assert _norm_margin(2000) == pytest.approx(1.0)


def test_norm_margin_at_floor_is_zero():
    assert _norm_margin(_LOG_MARGIN_FLOOR) == pytest.approx(0.0)


def test_suspicious_margin_note_in_verdict():
    # High margin + low confidence -> "[suspicious margin]" note
    lead = _make_lead(
        title="Quick task",
        description="Do a thing",
        budget={"amount": 50000.0, "currency": "USD", "type": "fixed"},
    )
    result = score_lead(lead)
    assert "[suspicious margin]" in result["verdict"]


def test_no_suspicious_note_for_high_confidence():
    # High confidence should suppress the suspicious note even at high margin
    lead = _make_lead(
        title="Quick task",
        description="Do a thing. " * 40,  # > 80 words
        budget={"amount": 50000.0, "currency": "USD", "type": "fixed"},
        client={"payment_verified": True, "rating": 4.8},
        skills=["python"],
        posted_at="2024-03-01",
    )
    result = score_lead(lead)
    assert "[suspicious margin]" not in result["verdict"]


# ---------------------------------------------------------------------------
# FIX 2 — annual salary type
# ---------------------------------------------------------------------------

def test_annual_90k_vs_180k_score_differently():
    lead_90k = _make_lead(
        title="Software Engineer",
        description="Full-time remote role.",
        budget={"amount": 90000.0, "currency": "USD", "type": "annual"},
    )
    lead_180k = _make_lead(
        title="Senior Software Engineer",
        description="Full-time remote role.",
        budget={"amount": 180000.0, "currency": "USD", "type": "annual"},
    )
    score_90 = score_lead(lead_90k)["final_score"]
    score_180 = score_lead(lead_180k)["final_score"]
    assert score_180 > score_90


def test_annual_ranks_below_real_gig():
    real_gig = _make_lead(
        title="Build a REST API integration",
        description="Implement a FastAPI backend with database integration.",
        budget={"amount": 5000.0, "currency": "USD", "type": "fixed"},
        client={"payment_verified": True},
        skills=["python"],
        posted_at="2024-03-01",
    )
    annual_180k = _make_lead(
        title="Senior Engineer",
        description="Full-time role with competitive salary.",
        budget={"amount": 180000.0, "currency": "USD", "type": "annual"},
    )
    gig_score = score_lead(real_gig)["final_score"]
    annual_score = score_lead(annual_180k)["final_score"]
    assert gig_score > annual_score


def test_annual_verdict_shows_salaried():
    lead = _make_lead(
        title="Staff Engineer",
        description="Full-time position.",
        budget={"amount": 120000.0, "currency": "USD", "type": "annual"},
    )
    result = score_lead(lead)
    assert "salaried" in result["verdict"]
    assert "yr" in result["verdict"]


def test_annual_margin_uses_2080_hours():
    lead = _make_lead(
        title="Engineer",
        description="Role.",
        budget={"amount": 104000.0, "currency": "USD", "type": "annual"},
    )
    result = score_lead(lead)
    # $104k / 2080 = $50/hr exactly
    assert result["margin"] == pytest.approx(50.0, rel=0.01)


# ---------------------------------------------------------------------------
# FIX 3 — richer effort heuristic
# ---------------------------------------------------------------------------

def test_effort_short_vs_long_multideliverable():
    short_hours = _estimate_effort_hours("Fix typo in header text", "Fix typo")
    long_desc = (
        "Build a web application with the following features:\n"
        "- User authentication and registration\n"
        "- Dashboard with 5 screens\n"
        "- REST API with 10 endpoints\n"
        "- Database integration\n"
        "- Admin panel with reports\n"
        "- Email notifications\n"
        "- Export to PDF feature\n"
        "This is a complex project requiring extensive testing."
    )
    long_hours = _estimate_effort_hours(long_desc, "Complex web app")
    assert short_hours < long_hours
    assert short_hours <= 6
    assert long_hours >= 20
