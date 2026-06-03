"""Phase 3 tests: lead scoring engine (PRD 21.1)."""

import pytest
from freelance_os.models import Lead, LeadStatus, Decision
from freelance_os.scoring.lead_scorer import score_lead, ScoreResult
from freelance_os.scoring.risk_rules import apply_risk_penalties


def _make_lead(**kwargs) -> Lead:
    defaults = dict(
        source="upwork",
        status=LeadStatus.NEW,
    )
    defaults.update(kwargs)
    return Lead(**defaults)


# ---------------------------------------------------------------------------
# PRD 21.1: High-quality lead gets high score
# ---------------------------------------------------------------------------

def test_high_quality_lead_high_score(sample_lead):
    result = score_lead(sample_lead)
    assert result.lead_score >= 65, f"Expected high score, got {result.lead_score}"
    assert result.decision in (Decision.DRAFT_NOW, Decision.WATCH)


def test_high_quality_lead_has_reason_codes(sample_lead):
    result = score_lead(sample_lead)
    assert len(result.reason_codes) > 0


def test_high_budget_increases_score():
    lead = _make_lead(
        title="Build Next.js app",
        description="Build a Python FastAPI backend with PostgreSQL. " * 10,
        budget_min=5000,
        budget_max=10000,
        client_payment_verified=True,
        client_rating=4.9,
    )
    result = score_lead(lead)
    assert result.lead_score >= 70


# ---------------------------------------------------------------------------
# PRD 21.1: Low-budget vague lead gets rejected
# ---------------------------------------------------------------------------

def test_low_budget_vague_lead_rejected(low_quality_lead):
    result = score_lead(low_quality_lead)
    assert result.lead_score < 50
    assert result.decision == Decision.REJECT


def test_low_budget_leads_to_low_score():
    lead = _make_lead(
        title="Quick task",
        description="Simple task",
        budget_min=50,
        budget_max=50,
    )
    result = score_lead(lead)
    assert result.decision in (Decision.REJECT, Decision.MAYBE)


# ---------------------------------------------------------------------------
# PRD 21.1: Unsupported tech stack reduces score
# ---------------------------------------------------------------------------

def test_unsupported_stack_reduces_score():
    lead = _make_lead(
        title="iOS app development",
        description="Build an iOS app using Swift and UIKit for mobile.",
        budget_min=2000,
        budget_max=5000,
    )
    result = score_lead(lead)
    assert "UNSUPPORTED_STACK" in result.reason_codes


def test_supported_stack_gives_tech_match():
    lead = _make_lead(
        title="Python FastAPI backend",
        description="Build a Python FastAPI backend with PostgreSQL and Docker.",
        budget_min=2000,
        budget_max=4000,
    )
    result = score_lead(lead)
    assert "TECH_STACK_MATCH" in result.reason_codes


# ---------------------------------------------------------------------------
# PRD 21.1: Unpaid test request triggers severe penalty
# ---------------------------------------------------------------------------

def test_unpaid_test_request_penalty():
    lead = _make_lead(
        title="Developer needed",
        description="We need a developer. Please do a test first for free before we hire.",
        budget_min=1000,
        budget_max=2000,
    )
    result = score_lead(lead)
    assert "UNPAID_TEST_REQUEST" in result.reason_codes
    assert result.risk_score >= 25


def test_bypass_payment_penalty():
    lead = _make_lead(
        title="Web developer",
        description="Pay via PayPal direct, outside upwork for this project.",
    )
    result = score_lead(lead)
    assert "BYPASS_PAYMENT_RISK" in result.reason_codes


# ---------------------------------------------------------------------------
# PRD 21.1: Score always includes reason codes
# ---------------------------------------------------------------------------

def test_score_always_has_reason_codes():
    lead = _make_lead(title="Any project", description="Any description here.")
    result = score_lead(lead)
    assert isinstance(result.reason_codes, list)
    assert len(result.reason_codes) > 0


def test_score_result_structure(sample_lead):
    result = score_lead(sample_lead)
    assert isinstance(result, ScoreResult)
    assert 0 <= result.lead_score <= 100
    assert result.risk_score >= 0
    assert result.decision in Decision.__members__.values()


# ---------------------------------------------------------------------------
# Decision thresholds (PRD 10.3)
# ---------------------------------------------------------------------------

def test_decision_thresholds():
    from freelance_os.scoring.lead_scorer import _decide, Decision
    assert _decide(85) == Decision.DRAFT_NOW
    assert _decide(80) == Decision.DRAFT_NOW
    assert _decide(70) == Decision.WATCH
    assert _decide(65) == Decision.WATCH
    assert _decide(55) == Decision.MAYBE
    assert _decide(50) == Decision.MAYBE
    assert _decide(49) == Decision.REJECT
    assert _decide(0) == Decision.REJECT


# ---------------------------------------------------------------------------
# Risk rules direct tests
# ---------------------------------------------------------------------------

def test_risk_rules_unrealistic_deadline():
    lead = _make_lead(
        title="Need this ASAP today only",
        description="Complete by end of day ASAP.",
    )
    penalty, codes = apply_risk_penalties(lead)
    assert "UNREALISTIC_DEADLINE" in codes
    assert penalty >= 20


def test_risk_rules_scope_creep():
    lead = _make_lead(
        title="Project",
        description="Client has many revisions and keeps adding features.",
    )
    penalty, codes = apply_risk_penalties(lead)
    assert "SCOPE_CREEP_RISK" in codes


def test_risk_rules_no_risks():
    lead = _make_lead(
        title="Clean Python API project",
        description=(
            "Build a REST API using FastAPI and PostgreSQL. "
            "Clear scope, reasonable budget, timeline flexible. "
            "Payment verified through the platform."
        ),
    )
    penalty, codes = apply_risk_penalties(lead)
    assert penalty == 0
    assert codes == []
