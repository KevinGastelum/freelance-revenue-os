"""Phase 4: Proposal drafting integration tests."""

import pytest
from pathlib import Path
from freelance_os.models import Lead, ProposalDraft
from freelance_os.proposal.draft_generator import generate_draft
from freelance_os.proposal.proposal_validator import validate_draft
from freelance_os.proposal.portfolio_matcher import match_portfolio, load_portfolio
from freelance_os.proposal.templates import render_proposal


@pytest.fixture
def portfolio_cfg(tmp_path):
    portfolio_yaml = tmp_path / "portfolio.yaml"
    portfolio_yaml.write_text("""\
items:
  - name: "Python FastAPI Project"
    type: backend
    tags: [python, fastapi, api, postgres]
    description: "Built Python FastAPI backends."
    proof_points: ["Built REST APIs with FastAPI and SQLModel."]
    allowed_claims: ["I have built FastAPI APIs."]
    forbidden_claims: ["I scaled this to billions of users."]
  - name: "React Dashboard"
    type: web_app
    tags: [react, nextjs, dashboard, charts]
    description: "Built React dashboards."
    proof_points: ["Built analytics dashboards with React."]
    allowed_claims: ["I have built React dashboards."]
    forbidden_claims: ["I am a React expert with 10 years experience."]
""", encoding="utf-8")
    return {
        "paths": {"portfolio_file": str(portfolio_yaml)},
        "scoring": {"target_hourly_rate": 75, "minimum_project_value": 300},
    }


def test_render_proposal_template():
    """Template rendering produces correct output."""
    text = render_proposal(
        core_bottleneck="data architecture",
        surface_task="dashboard",
        step_1="Design database schema",
        step_2="Build API endpoints",
        step_3="Implement dashboard UI",
        project_reference="My FastAPI project",
        proof_point="Built production REST APIs",
        clarifying_question="What is the hard deadline?",
    )
    assert "data architecture" in text
    assert "dashboard" in text
    assert "Design database schema" in text
    assert "What is the hard deadline?" in text


def test_portfolio_match_returns_relevant_items(portfolio_cfg):
    """Portfolio matcher returns relevant items for tech keywords."""
    matches = match_portfolio("Build Python FastAPI backend with PostgreSQL", portfolio_cfg)
    assert len(matches) > 0
    assert any("FastAPI" in m.get("name", "") for m in matches)


def test_portfolio_match_empty_for_unrelated(portfolio_cfg):
    """Portfolio matcher returns nothing for unrelated text."""
    matches = match_portfolio("Marketing copywriting blog post", portfolio_cfg)
    assert len(matches) == 0


def test_generate_draft_full_pipeline(portfolio_cfg):
    """generate_draft produces all required keys."""
    lead = Lead(
        id=1, source="upwork",
        title="Build Python API",
        description="We need a FastAPI backend with PostgreSQL. Clear scope. Budget $2000.",
    )
    result = generate_draft(lead, portfolio_cfg)
    assert "draft_text" in result
    assert "technical_diagnosis" in result
    assert "clarifying_questions" in result
    assert "portfolio_matches" in result
    assert "price_recommendation" in result


def test_generate_draft_no_banned_phrases(portfolio_cfg):
    """Generated draft must not contain any banned phrases by default."""
    from freelance_os.proposal.proposal_validator import _load_banned_phrases

    lead = Lead(
        id=1, source="upwork",
        title="Data Analytics Dashboard",
        description="Build a Power BI style dashboard with SQL backend.",
    )
    result = generate_draft(lead, portfolio_cfg)
    text_lower = result["draft_text"].lower()
    banned = _load_banned_phrases(portfolio_cfg)
    for phrase in banned:
        assert phrase.lower() not in text_lower, f"Banned phrase found: {phrase}"


def test_validate_clean_draft_passes(portfolio_cfg):
    """A clean, complete draft passes validation."""
    draft = ProposalDraft(
        lead_id=1,
        technical_diagnosis="Core problem: data architecture",
        draft_text=(
            "I'd approach this as a data architecture problem, not just a dashboard task.\n\n"
            "Here's how I'd handle it:\n"
            "- Design the database schema\n"
            "- Build the API\n"
            "- Implement the dashboard\n\n"
            "I have built FastAPI APIs for similar projects.\n\n"
            "One question: What is the expected data volume?"
        ),
    )
    result = validate_draft(draft, portfolio_cfg)
    assert result["status"] in ("PASS", "WARN")


def test_validator_flags_off_platform(portfolio_cfg):
    """Validator catches off-platform communication."""
    draft = ProposalDraft(
        lead_id=1,
        technical_diagnosis="API problem",
        draft_text=(
            "I'd solve this. Let's connect outside the platform for details. "
            "One question: when is the deadline?"
        ),
    )
    result = validate_draft(draft, portfolio_cfg)
    assert result["status"] == "FAIL"


def test_validator_detects_forbidden_claim(portfolio_cfg):
    """Validator catches forbidden portfolio claims."""
    draft = ProposalDraft(
        lead_id=1,
        technical_diagnosis="API problem",
        draft_text=(
            "I scaled this to billions of users. I can do this for you. "
            "One question: what is the deadline?"
        ),
    )
    result = validate_draft(draft, portfolio_cfg)
    assert result["status"] == "FAIL"
    assert any("unsupported claim" in r for r in result["reasons"])
