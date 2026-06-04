"""Phase 4: Proposal validation tests per PRD section 21.2."""

import pytest
from freelance_os.models import Lead, ProposalDraft
from freelance_os.proposal.proposal_validator import validate_draft
from freelance_os.proposal.draft_generator import generate_draft


@pytest.fixture
def base_cfg(tmp_path):
    # Use a portfolio.yaml with forbidden claims
    portfolio_yaml = tmp_path / "portfolio.yaml"
    portfolio_yaml.write_text(
        """items:
  - name: "Test Project"
    type: web_app
    tags: [python, fastapi]
    description: "Test project"
    proof_points: ["Built APIs."]
    allowed_claims: ["I have built FastAPI apps."]
    forbidden_claims: ["I have scaled this to millions of users."]
""",
        encoding="utf-8",
    )
    return {
        "paths": {"portfolio_file": str(portfolio_yaml)},
        "scoring": {"target_hourly_rate": 75, "minimum_project_value": 300},
    }


def make_draft(text: str, diagnosis: str = "Test diagnosis") -> ProposalDraft:
    return ProposalDraft(
        lead_id=1,
        draft_text=text,
        technical_diagnosis=diagnosis,
    )


def test_clean_draft_passes(base_cfg):
    """A clean proposal draft should pass validation."""
    draft = make_draft(
        "I'd approach this as a data architecture problem.\n"
        "Here's how I'd handle it:\n"
        "- Design the database schema\n"
        "- Implement the API endpoints\n"
        "- Add tests\n\n"
        "I've built FastAPI apps before.\n\n"
        "One question: What is the hard deadline?"
    )
    result = validate_draft(draft, base_cfg)
    assert result["status"] in ("PASS", "WARN")


def test_banned_phrase_causes_fail(base_cfg):
    """Banned phrase 'I hope this message finds you well' should FAIL."""
    draft = make_draft(
        "I hope this message finds you well. "
        "I'd like to help with your project. What is your deadline?"
    )
    result = validate_draft(draft, base_cfg)
    assert result["status"] == "FAIL"
    assert any("banned phrase" in r for r in result["reasons"])


def test_ideal_candidate_phrase_fails(base_cfg):
    """'I am the perfect candidate' should FAIL."""
    draft = make_draft(
        "I am the perfect candidate for this role. "
        "I have extensive experience. What deliverables do you expect?"
    )
    result = validate_draft(draft, base_cfg)
    assert result["status"] == "FAIL"


def test_off_platform_communication_fails(base_cfg):
    """Off-platform communication suggestion should FAIL."""
    draft = make_draft(
        "Let's connect outside the platform to discuss further. "
        "What is your deadline for this project?"
    )
    result = validate_draft(draft, base_cfg)
    assert result["status"] == "FAIL"
    assert any("off-platform" in r for r in result["reasons"])


def test_missing_clarifying_question_warns(base_cfg):
    """No question mark should produce a WARN."""
    draft = make_draft(
        "I would approach this as a data problem. "
        "I have built FastAPI applications before with clear deliverables. "
        "This is a solid 40-hour project.",
        diagnosis="Data architecture",
    )
    result = validate_draft(draft, base_cfg)
    assert result["status"] in ("WARN", "FAIL")
    assert any("clarifying question" in r for r in result["reasons"])


def test_forbidden_claim_fails(base_cfg):
    """Forbidden portfolio claim should FAIL."""
    draft = make_draft(
        "I have scaled this to millions of users. "
        "I'll solve your problem efficiently. What is your timeline?"
    )
    result = validate_draft(draft, base_cfg)
    assert result["status"] == "FAIL"
    assert any("unsupported claim" in r for r in result["reasons"])


def test_very_short_draft_warns(base_cfg):
    """A very short draft should warn."""
    draft = make_draft("Short proposal text.")
    result = validate_draft(draft, base_cfg)
    assert result["status"] in ("WARN", "FAIL")
    assert any("short" in r.lower() for r in result["reasons"])


def test_generate_draft_produces_question(base_cfg, tmp_path):
    """Generated draft should always contain a clarifying question."""
    lead = Lead(
        id=1,
        source="upwork",
        title="Build Python API",
        description="We need a FastAPI backend with PostgreSQL and authentication.",
    )
    draft_data = generate_draft(lead, base_cfg)
    assert "?" in draft_data["draft_text"]
    assert draft_data["technical_diagnosis"]


def test_generate_draft_has_required_sections(base_cfg, tmp_path):
    """Generated draft should have all required sections."""
    lead = Lead(
        id=1,
        source="upwork",
        title="Build data dashboard",
        description="Analytics dashboard with SQL database and reporting.",
    )
    draft_data = generate_draft(lead, base_cfg)
    text = draft_data["draft_text"]
    assert "approach" in text.lower() or "handle" in text.lower()
    assert "?" in text
    assert len(text.split()) >= 30
