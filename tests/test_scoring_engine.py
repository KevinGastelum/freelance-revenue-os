"""Phase 3: Additional scoring engine tests."""

import pytest
from freelance_os.models import Lead, LeadStatus
from freelance_os.scoring.lead_scorer import score_lead, _score_tech_fit, _score_budget_fit
from freelance_os.scoring.pricing import estimate_price


@pytest.fixture
def cfg():
    return {
        "scoring": {
            "target_hourly_rate": 75,
            "minimum_project_value": 300,
            "risk_multiplier_low": 1.0,
            "risk_multiplier_medium": 1.25,
            "risk_multiplier_high": 1.5,
            "rush_multiplier": 1.25,
        },
        "paths": {"portfolio_file": "config/portfolio.yaml"},
    }


def make_lead(**kwargs) -> Lead:
    return Lead(source="test", **kwargs)


def test_tech_fit_score_with_multiple_matches():
    """Multiple supported tech keywords increase score."""
    score, codes = _score_tech_fit("python fastapi react postgresql supabase")
    assert score >= 16
    assert "TECH_STACK_MATCH" in codes


def test_tech_fit_score_zero_for_unknown():
    """No supported tech keywords returns 0."""
    score, codes = _score_tech_fit("marketing copywriting blog post writing")
    assert score == 0
    assert "TECH_STACK_MATCH" not in codes


def test_budget_fit_high_fixed_budget(cfg):
    """High fixed budget (>=1000) returns max budget score."""
    lead = make_lead(budget_type="fixed", budget_max=2000.0)
    score, codes = _score_budget_fit(lead)
    assert score == 15
    assert "HIGH_BUDGET_FIT" in codes


def test_budget_fit_low_budget(cfg):
    """Low budget (<200) returns 0."""
    lead = make_lead(budget_type="fixed", budget_max=150.0)
    score, codes = _score_budget_fit(lead)
    assert score == 0
    assert "LOW_BUDGET" in codes


def test_pricing_estimate_minimum_value(cfg):
    """Price estimate respects minimum_project_value."""
    lead = make_lead(title="Small fix", description="Quick fix.")
    result = estimate_price(lead, cfg)
    assert result["recommended_quote"] >= 300  # minimum_project_value


def test_pricing_estimate_rush_job(cfg):
    """Rush job gets rush multiplier applied."""
    lead_normal = make_lead(title="Build API", description="Build a Python API. Long description " * 10)
    lead_rush = make_lead(title="Urgent API", description="URGENT - ASAP need a Python API. Long description " * 10)

    r_normal = estimate_price(lead_normal, cfg)
    r_rush = estimate_price(lead_rush, cfg)
    assert r_rush["recommended_quote"] > r_normal["recommended_quote"]
    assert r_rush["is_rush"] is True
    assert r_normal["is_rush"] is False


def test_pricing_returns_summary_string(cfg):
    """estimate_price returns a human-readable summary."""
    lead = make_lead(title="Build Dashboard", description="Need a dashboard with analytics.")
    result = estimate_price(lead, cfg)
    assert "summary" in result
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 10


def test_score_all_new_leads(cfg, tmp_path, monkeypatch):
    """Scoring all NEW leads updates their status to SCORED."""
    import freelance_os.models  # noqa: F401
    from freelance_os.models import Lead, LeadStatus
    from freelance_os.scoring.lead_scorer import score_lead
    from sqlmodel import create_engine, SQLModel, Session, select

    engine = create_engine(f"sqlite:///{tmp_path}/test.sqlite")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        for i in range(3):
            session.add(Lead(source=f"test{i}", title=f"Job {i}", description="Python FastAPI backend"))
        session.commit()

    with Session(engine) as session:
        leads = session.exec(select(Lead).where(Lead.status == LeadStatus.NEW)).all()
        for lead in leads:
            result = score_lead(lead, cfg)
            lead.lead_score = result["lead_score"]
            lead.status = LeadStatus.SCORED
            session.add(lead)
        session.commit()

    with Session(engine) as session:
        scored = session.exec(select(Lead).where(Lead.status == LeadStatus.SCORED)).all()
        assert len(scored) == 3
        for l in scored:
            assert l.lead_score is not None
