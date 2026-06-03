"""Phase 4 tests: proposal drafting and validation (PRD 21.2)."""

import pytest
from pathlib import Path

from freelance_os.models import Lead, LeadStatus, ProposalDraft
from freelance_os.proposal.proposal_validator import validate_draft, ValidationResult
from freelance_os.proposal.portfolio_matcher import find_matches
from freelance_os.proposal.templates import render_proposal
from freelance_os.db import init_db, reset_engine, get_session


def _make_draft(**kwargs) -> ProposalDraft:
    defaults = dict(
        lead_id=1,
        version=1,
        technical_diagnosis="The lead describes a data pipeline problem. Core challenge: integration.",
        clarifying_questions="What does the existing data flow look like?",
    )
    defaults.update(kwargs)
    return ProposalDraft(**defaults)


def _make_lead(**kwargs) -> Lead:
    defaults = dict(source="upwork", status=LeadStatus.NEW)
    defaults.update(kwargs)
    return Lead(**defaults)


# ---------------------------------------------------------------------------
# PRD 21.2: Banned phrases are detected
# ---------------------------------------------------------------------------

def test_banned_phrase_detected_hope_message():
    draft = _make_draft(draft_text="I hope this message finds you well. Here is my proposal.")
    lead = _make_lead()
    result = validate_draft(draft, lead)
    assert result.status == "FAIL"
    assert any("BANNED_PHRASE" in f for f in result.flags)


def test_banned_phrase_detected_perfect_candidate():
    draft = _make_draft(draft_text="I am the perfect candidate for this role.")
    lead = _make_lead()
    result = validate_draft(draft, lead)
    assert result.status == "FAIL"


def test_banned_phrase_detected_extensive_experience():
    draft = _make_draft(draft_text="I have extensive experience in this field.")
    lead = _make_lead()
    result = validate_draft(draft, lead)
    assert result.status == "FAIL"


def test_clean_draft_passes():
    draft = _make_draft(
        draft_text=(
            "I'd approach this as a data pipeline problem.\n\n"
            "Here's how I'd handle it:\n"
            "- Step 1: audit the data flow\n"
            "- Step 2: design schema\n"
            "- Step 3: implement with tests\n\n"
            "I've built similar systems before.\n\n"
            "One question: what does the existing data flow look like?"
        )
    )
    lead = _make_lead()
    result = validate_draft(draft, lead)
    assert result.status == "PASS"


# ---------------------------------------------------------------------------
# PRD 21.2: Off-platform communication phrase fails
# ---------------------------------------------------------------------------

def test_off_platform_phrase_fails():
    draft = _make_draft(draft_text="Let's connect outside Upwork to discuss this further.")
    lead = _make_lead()
    result = validate_draft(draft, lead)
    assert result.status == "FAIL"
    assert any("OFF_PLATFORM" in f for f in result.flags)


def test_telegram_off_platform_fails():
    draft = _make_draft(draft_text="Please contact me on Telegram for faster response.")
    lead = _make_lead()
    result = validate_draft(draft, lead)
    assert result.status == "FAIL"


# ---------------------------------------------------------------------------
# PRD 21.2: Missing clarifying question produces warning
# ---------------------------------------------------------------------------

def test_missing_clarifying_question_warns():
    draft = _make_draft(
        draft_text="I'd approach this as a workflow automation problem. Here is my plan.",
        clarifying_questions="",
    )
    lead = _make_lead()
    result = validate_draft(draft, lead)
    assert result.status in ("WARN", "FAIL")
    assert any("clarifying" in f.lower() for f in result.flags)


def test_draft_with_question_mark_passes_question_check():
    draft = _make_draft(
        draft_text=(
            "I'd solve this with Python FastAPI.\n"
            "One question: what does success look like at the end of week one?"
        )
    )
    lead = _make_lead()
    result = validate_draft(draft, lead)
    # Should not flag missing clarifying question
    assert not any("Missing clarifying question" in f for f in result.flags)


# ---------------------------------------------------------------------------
# PRD 21.2: Draft with technical diagnosis passes
# ---------------------------------------------------------------------------

def test_draft_with_technical_diagnosis_passes():
    draft = _make_draft(
        draft_text=(
            "I'd approach this as an integration problem, not just a build task.\n\n"
            "Here's how I'd handle it:\n"
            "- Step 1\n- Step 2\n- Step 3\n\n"
            "What does the current data flow look like?"
        ),
        technical_diagnosis="The lead describes an API integration challenge. Core: data consistency.",
    )
    lead = _make_lead()
    result = validate_draft(draft, lead)
    assert result.status == "PASS"


def test_missing_technical_diagnosis_warns():
    draft = _make_draft(
        draft_text="Here is my proposal. What is the timeline?",
        technical_diagnosis="",
    )
    lead = _make_lead()
    result = validate_draft(draft, lead)
    assert result.status in ("WARN", "FAIL")
    assert any("Technical diagnosis" in f for f in result.flags)


# ---------------------------------------------------------------------------
# PRD 21.2: Unsupported portfolio claims are detected
# ---------------------------------------------------------------------------

def test_unsupported_claim_detected():
    draft = _make_draft(
        draft_text=(
            "I have scaled this to millions of users. "
            "What is the expected load for this project?"
        ),
        technical_diagnosis="Technical diagnosis: data pipeline.",
    )
    lead = _make_lead()

    portfolio = [{
        "name": "Next.js Platform",
        "forbidden_claims": ["I have scaled this to millions of users."],
        "allowed_claims": ["I can build Next.js apps."],
    }]

    from freelance_os.proposal.proposal_validator import validate_draft as vd
    from unittest.mock import patch
    with patch("freelance_os.proposal.proposal_validator.load_portfolio", return_value=portfolio):
        result = vd(draft, lead)

    assert any("UNSUPPORTED_CLAIM" in f for f in result.flags)
    assert result.status in ("WARN", "FAIL")


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

def test_template_renders_correctly():
    text = render_proposal(
        core_bottleneck="data pipeline",
        surface_task="build task",
        step_1="Audit existing flow",
        step_2="Design schema",
        step_3="Implement with tests",
        portfolio_ref="a Next.js/Supabase platform",
        proof_point="Implemented database-backed workflows",
        clarifying_question="What does success look like at end of week one?",
    )
    assert "data pipeline" in text
    assert "Audit existing flow" in text
    assert "What does success look like" in text
    assert "?" in text


# ---------------------------------------------------------------------------
# Portfolio matcher
# ---------------------------------------------------------------------------

def test_portfolio_matcher_finds_relevant():
    lead = _make_lead(
        title="Build a Next.js dashboard",
        description="We need a Next.js application with Supabase backend.",
    )
    portfolio = [
        {
            "name": "Next.js Platform",
            "tags": ["nextjs", "supabase", "postgres"],
            "proof_points": ["Built Next.js apps with Supabase."],
        },
        {
            "name": "iOS App",
            "tags": ["swift", "ios", "xcode"],
            "proof_points": ["Built iOS apps."],
        },
    ]
    matches = find_matches(lead, portfolio=portfolio)
    assert len(matches) >= 1
    assert matches[0]["name"] == "Next.js Platform"


def test_portfolio_matcher_no_match():
    lead = _make_lead(
        title="Hardware firmware project",
        description="Embedded firmware in C++ for ARM processor.",
    )
    portfolio = [
        {
            "name": "Next.js Platform",
            "tags": ["nextjs", "react", "supabase"],
            "proof_points": ["Built web apps."],
        },
    ]
    matches = find_matches(lead, portfolio=portfolio)
    assert matches == []


# ---------------------------------------------------------------------------
# Draft generation integration test
# ---------------------------------------------------------------------------

def test_draft_generation_end_to_end(tmp_db):
    from freelance_os.ingestion.manual import add_lead_by_text
    from freelance_os.proposal.draft_generator import generate_draft

    lead = add_lead_by_text(
        source="upwork",
        text=(
            "Build a Python FastAPI backend with PostgreSQL. "
            "We need a REST API with authentication, data validation, and tests. "
            "Budget $2000-$4000. Payment verified."
        ),
        db_path=tmp_db,
    )

    with get_session(tmp_db) as session:
        lead_db = session.get(Lead, lead.id)
        draft = generate_draft(lead_db, session=session)
        session.commit()
        assert draft.draft_text is not None
        assert len(draft.draft_text) > 50
        assert draft.technical_diagnosis is not None
        assert draft.clarifying_questions is not None
