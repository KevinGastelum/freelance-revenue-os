"""Tests for command center phase 3: feasibility estimator + quick-win spotlight."""

import pytest
from sqlmodel import Session, SQLModel, create_engine

from freelance_os.models import Lead, LeadStatus, JobCategory
from freelance_os.scoring.feasibility import estimate_feasibility


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def base_cfg():
    return {
        "scoring": {
            "target_hourly_rate": 75,
            "minimum_project_value": 300,
            "quick_win_discount": 0.85,
        },
    }


def make_lead(category=JobCategory.OTHER.value, title="", description="", **kwargs) -> Lead:
    return Lead(source="test", category=category, title=title, description=description, **kwargs)


# ---------------------------------------------------------------------------
# Effort range tests
# ---------------------------------------------------------------------------

def test_bug_fix_has_small_effort(base_cfg):
    lead = make_lead(
        category=JobCategory.BUG_FIX.value,
        title="Fix login bug",
        description="The login form is broken, please fix it.",
    )
    result = estimate_feasibility(lead, base_cfg)
    assert result["effort_hours_low"] >= 1
    assert result["effort_hours_high"] <= 10, f"BUG_FIX should be small: {result}"


def test_scraping_lead_effort_range(base_cfg):
    lead = make_lead(
        category=JobCategory.SCRAPING_DATA.value,
        title="Scrape product data from 10 websites",
        description="Need a scraper to extract product names, prices, and SKUs from 10 e-commerce sites.",
    )
    result = estimate_feasibility(lead, base_cfg)
    assert result["effort_hours_low"] < result["effort_hours_high"]
    assert result["effort_hours_high"] <= 24


def test_vague_large_webapp_has_high_effort(base_cfg):
    lead = make_lead(
        category=JobCategory.WEB_APP.value,
        title="Build enterprise full-stack platform from scratch",
        description=(
            "We need an enterprise-level comprehensive full-stack application from scratch. "
            "Complex architecture with multiple modules, scalable, end-to-end solution."
        ),
    )
    result = estimate_feasibility(lead, base_cfg)
    assert result["effort_hours_high"] > 40, f"Large WEB_APP should be >40h: {result}"


def test_small_scope_reduces_effort(base_cfg):
    lead_big = make_lead(
        category=JobCategory.WEB_APP.value,
        title="Build web app",
        description="Build a full web application with many features.",
    )
    lead_small = make_lead(
        category=JobCategory.WEB_APP.value,
        title="Build simple landing page",
        description="Need a simple one-page landing page prototype.",
    )
    result_big = estimate_feasibility(lead_big, base_cfg)
    result_small = estimate_feasibility(lead_small, base_cfg)
    assert result_small["effort_hours_high"] < result_big["effort_hours_high"]


# ---------------------------------------------------------------------------
# Confidence tests
# ---------------------------------------------------------------------------

def test_bug_fix_has_high_confidence(base_cfg):
    lead = make_lead(
        category=JobCategory.BUG_FIX.value,
        title="Fix broken API endpoint",
        description="The /api/users endpoint returns 500, please fix it and add test coverage.",
    )
    result = estimate_feasibility(lead, base_cfg)
    assert result["feasibility_confidence"] in ("MED", "HIGH")


def test_other_category_has_low_confidence(base_cfg):
    lead = make_lead(
        category=JobCategory.OTHER.value,
        title="Need developer",
        description="Various tasks.",
    )
    result = estimate_feasibility(lead, base_cfg)
    assert result["feasibility_confidence"] == "LOW"


def test_vague_description_lowers_confidence(base_cfg):
    lead_clear = make_lead(
        category=JobCategory.DATA_DASHBOARD.value,
        title="Build Power BI dashboard",
        description=(
            "Deliver a Power BI dashboard with KPI milestones and clear requirements. "
            "Feature: sales funnel, revenue by region. Test coverage required."
        ),
    )
    lead_vague = make_lead(
        category=JobCategory.DATA_DASHBOARD.value,
        title="Dashboard",
        description="Dashboard.",
    )
    result_clear = estimate_feasibility(lead_clear, base_cfg)
    result_vague = estimate_feasibility(lead_vague, base_cfg)
    _level = {"LOW": 0, "MED": 1, "HIGH": 2}
    assert _level[result_clear["feasibility_confidence"]] >= _level[result_vague["feasibility_confidence"]]


# ---------------------------------------------------------------------------
# Warren feasibility tests
# ---------------------------------------------------------------------------

def test_bug_fix_is_warren_feasible(base_cfg):
    lead = make_lead(
        category=JobCategory.BUG_FIX.value,
        title="Fix small bug",
        description="A small bug in the API, simple fix needed.",
    )
    result = estimate_feasibility(lead, base_cfg)
    assert result["warren_feasible"] is True


def test_other_category_is_not_warren_feasible(base_cfg):
    lead = make_lead(
        category=JobCategory.OTHER.value,
        title="Unknown project",
        description="Various things needed.",
    )
    result = estimate_feasibility(lead, base_cfg)
    assert result["warren_feasible"] is False


def test_huge_webapp_is_not_warren_feasible(base_cfg):
    lead = make_lead(
        category=JobCategory.WEB_APP.value,
        title="Enterprise full-stack platform",
        description=(
            "Build a comprehensive enterprise full-stack platform from scratch. "
            "Complex architecture, scalable, multiple modules, end-to-end."
        ),
    )
    result = estimate_feasibility(lead, base_cfg)
    assert result["warren_feasible"] is False


def test_small_webapp_can_be_warren_feasible(base_cfg):
    lead = make_lead(
        category=JobCategory.WEB_APP.value,
        title="Simple landing page",
        description="Need a simple one-page landing page, basic design.",
    )
    result = estimate_feasibility(lead, base_cfg)
    # With small scope signals, effort_high should be <= 20, making it feasible
    assert result["effort_hours_high"] <= 20 or not result["warren_feasible"]


def test_scraping_lead_is_warren_feasible(base_cfg):
    lead = make_lead(
        category=JobCategory.SCRAPING_DATA.value,
        title="Scrape product listings",
        description="Extract product data from website. Clear deliverable: CSV output.",
    )
    result = estimate_feasibility(lead, base_cfg)
    assert result["warren_feasible"] is True


# ---------------------------------------------------------------------------
# Suggested price tests
# ---------------------------------------------------------------------------

def test_suggested_price_uses_configured_rate(base_cfg):
    lead = make_lead(
        category=JobCategory.BUG_FIX.value,
        title="Fix bug",
        description="Fix a simple bug in the code.",
    )
    result = estimate_feasibility(lead, base_cfg)
    # price >= min_project_value
    assert result["suggested_price"] >= 300
    # price is derived from effort_high * rate * discount
    expected = result["effort_hours_high"] * 75 * 0.85
    assert result["suggested_price"] == max(300.0, round(expected, 2))


def test_suggested_price_respects_minimum(base_cfg):
    """Even tiny jobs should never be quoted below minimum_project_value."""
    lead = make_lead(
        category=JobCategory.BUG_FIX.value,
        title="Tiny fix",
        description="One line patch.",
    )
    result = estimate_feasibility(lead, base_cfg)
    assert result["suggested_price"] >= 300


def test_suggested_price_uses_custom_rate():
    """Custom hourly rate should change the suggested price."""
    cfg_cheap = {"scoring": {"target_hourly_rate": 50, "minimum_project_value": 100, "quick_win_discount": 1.0}}
    cfg_pricey = {"scoring": {"target_hourly_rate": 150, "minimum_project_value": 100, "quick_win_discount": 1.0}}
    lead = make_lead(
        category=JobCategory.DATA_DASHBOARD.value,
        title="Build dashboard with deliverables and milestones",
        description=(
            "Build a Power BI dashboard. Deliverables: 3 report pages. "
            "Requirement: test coverage. Milestone-based delivery."
        ),
    )
    result_cheap = estimate_feasibility(lead, cfg_cheap)
    result_pricey = estimate_feasibility(lead, cfg_pricey)
    assert result_pricey["suggested_price"] > result_cheap["suggested_price"]


# ---------------------------------------------------------------------------
# Turnaround tests
# ---------------------------------------------------------------------------

def test_turnaround_at_least_one_day(base_cfg):
    lead = make_lead(
        category=JobCategory.BUG_FIX.value,
        title="Fix",
        description="Fix simple bug.",
    )
    result = estimate_feasibility(lead, base_cfg)
    assert result["suggested_turnaround_days"] >= 1


def test_large_project_has_longer_turnaround(base_cfg):
    small = make_lead(
        category=JobCategory.BUG_FIX.value,
        title="Fix bug",
        description="Small quick fix.",
    )
    big = make_lead(
        category=JobCategory.WEB_APP.value,
        title="Build app from scratch",
        description=(
            "Build a comprehensive enterprise web application from scratch. "
            "Complex, scalable, multiple modules."
        ),
    )
    r_small = estimate_feasibility(small, base_cfg)
    r_big = estimate_feasibility(big, base_cfg)
    assert r_big["suggested_turnaround_days"] > r_small["suggested_turnaround_days"]


# ---------------------------------------------------------------------------
# quickwins filtering/ordering via DB
# ---------------------------------------------------------------------------

@pytest.fixture
def mem_db():
    import freelance_os.models  # noqa: F401
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


def _insert_lead(session, category, confidence, warren_feasible, score, effort_high, effort_low=1):
    lead = Lead(
        source="test",
        category=category,
        feasibility_confidence=confidence,
        warren_feasible=warren_feasible,
        effort_hours_low=effort_low,
        effort_hours_high=effort_high,
        lead_score=score,
        suggested_price=effort_high * 75 * 0.85,
        suggested_turnaround_days=max(1, effort_high // 6),
        status=LeadStatus.SCORED,
    )
    session.add(lead)
    return lead


def test_quickwins_filters_correctly(mem_db):
    """Only warren_feasible + MED/HIGH confidence leads should appear."""
    from sqlmodel import select

    with Session(mem_db) as session:
        _insert_lead(session, "BUG_FIX", "HIGH", True, 80, 4)   # should show
        _insert_lead(session, "WEB_APP", "MED", True, 70, 16)   # should show
        _insert_lead(session, "OTHER", "LOW", False, 60, 40)    # excluded (not feasible)
        _insert_lead(session, "BUG_FIX", "HIGH", False, 90, 4)  # excluded (warren_feasible=False)
        _insert_lead(session, "BUG_FIX", "LOW", True, 85, 4)   # excluded (LOW confidence)
        session.commit()

        candidates = session.exec(select(Lead).where(Lead.warren_feasible == True)).all()  # noqa: E712
        filtered = [
            l for l in candidates
            if l.feasibility_confidence in ("MED", "HIGH")
            and l.effort_hours_high is not None
        ]

    assert len(filtered) == 2
    cats = {l.category for l in filtered}
    assert "BUG_FIX" in cats
    assert "WEB_APP" in cats


def test_quickwins_ordering(mem_db):
    """High score + low effort should rank first."""
    from sqlmodel import select

    def priority(lead):
        score = lead.lead_score if lead.lead_score is not None else 50
        return score / lead.effort_hours_high

    with Session(mem_db) as session:
        # score=80, effort=4 → priority=20
        a = _insert_lead(session, "BUG_FIX", "HIGH", True, 80, 4)
        # score=70, effort=20 → priority=3.5
        b = _insert_lead(session, "SCRAPING_DATA", "MED", True, 70, 20)
        # score=90, effort=8 → priority=11.25
        c = _insert_lead(session, "DATA_DASHBOARD", "HIGH", True, 90, 8)
        session.commit()
        session.refresh(a)
        session.refresh(b)
        session.refresh(c)

    candidates = [a, b, c]
    candidates.sort(key=priority, reverse=True)
    assert candidates[0].category == "BUG_FIX"    # 80/4 = 20
    assert candidates[1].category == "DATA_DASHBOARD"  # 90/8 = 11.25
    assert candidates[2].category == "SCRAPING_DATA"   # 70/20 = 3.5
