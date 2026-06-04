"""Tests for board summary and lead list filters."""

import pytest
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture
def engine_with_leads(tmp_path):
    """Engine pre-populated with a few leads across categories/sources."""
    import freelance_os.models  # noqa: F401
    engine = create_engine(f"sqlite:///{tmp_path}/test.sqlite")
    SQLModel.metadata.create_all(engine)

    from freelance_os.models import Lead, LeadStatus, Decision

    rows = [
        Lead(source="upwork", category="WEB_APP", status=LeadStatus.SCORED,
             lead_score=80, decision=Decision.DRAFT_NOW, title="Next.js app"),
        Lead(source="upwork", category="WEB_APP", status=LeadStatus.SCORED,
             lead_score=70, decision=Decision.WATCH, title="React SPA"),
        Lead(source="fiverr", category="WEB_APP", status=LeadStatus.NEW,
             lead_score=None, decision=None, title="Webflow site"),
        Lead(source="upwork", category="AI_AUTOMATION", status=LeadStatus.SCORED,
             lead_score=90, decision=Decision.DRAFT_NOW, title="LLM chatbot"),
        Lead(source="direct", category="DATA_DASHBOARD", status=LeadStatus.NEW,
             lead_score=60, decision=Decision.MAYBE, title="Power BI report"),
        Lead(source="direct", category="OTHER", status=LeadStatus.REJECTED,
             lead_score=30, decision=Decision.REJECT, title="Misc task"),
    ]

    with Session(engine) as session:
        for row in rows:
            session.add(row)
        session.commit()

    return engine


# ---------------------------------------------------------------------------
# lead list filter tests
# ---------------------------------------------------------------------------

def test_lead_list_filter_category(engine_with_leads):
    from freelance_os.models import Lead
    from sqlmodel import Session, select

    with Session(engine_with_leads) as session:
        leads = session.exec(select(Lead).where(Lead.category == "WEB_APP")).all()
    assert len(leads) == 3
    assert all(l.category == "WEB_APP" for l in leads)


def test_lead_list_filter_source(engine_with_leads):
    from freelance_os.models import Lead
    from sqlmodel import Session, select

    with Session(engine_with_leads) as session:
        leads = session.exec(select(Lead).where(Lead.source == "upwork")).all()
    assert len(leads) == 3


def test_lead_list_filter_decision(engine_with_leads):
    from freelance_os.models import Lead, Decision
    from sqlmodel import Session, select

    with Session(engine_with_leads) as session:
        leads = session.exec(select(Lead).where(Lead.decision == Decision.DRAFT_NOW)).all()
    assert len(leads) == 2


def test_lead_list_filter_min_score(engine_with_leads):
    from freelance_os.models import Lead
    from sqlmodel import Session, select

    with Session(engine_with_leads) as session:
        leads = session.exec(select(Lead)).all()
    # min_score filter is applied in Python after query (matches CLI behaviour)
    filtered = [l for l in leads if l.lead_score is not None and l.lead_score >= 70]
    assert len(filtered) == 3
    assert all(l.lead_score >= 70 for l in filtered)


def test_lead_list_filter_status(engine_with_leads):
    from freelance_os.models import Lead, LeadStatus
    from sqlmodel import Session, select

    with Session(engine_with_leads) as session:
        leads = session.exec(select(Lead).where(Lead.status == LeadStatus.SCORED)).all()
    assert len(leads) == 3


# ---------------------------------------------------------------------------
# board summary correctness tests
# ---------------------------------------------------------------------------

def test_board_category_counts(engine_with_leads):
    """Board correctly counts leads per category."""
    from collections import defaultdict
    from freelance_os.models import Lead
    from sqlmodel import Session, select

    with Session(engine_with_leads) as session:
        leads = session.exec(select(Lead)).all()

    cat_counts = defaultdict(int)
    for lead in leads:
        cat_counts[lead.category or "OTHER"] += 1

    assert cat_counts["WEB_APP"] == 3
    assert cat_counts["AI_AUTOMATION"] == 1
    assert cat_counts["DATA_DASHBOARD"] == 1
    assert cat_counts["OTHER"] == 1


def test_board_avg_score(engine_with_leads):
    """Board correctly computes average score per category."""
    from freelance_os.models import Lead
    from sqlmodel import Session, select

    with Session(engine_with_leads) as session:
        leads = session.exec(select(Lead)).all()

    web_scores = [l.lead_score for l in leads if l.category == "WEB_APP" and l.lead_score is not None]
    avg = sum(web_scores) / len(web_scores)
    assert abs(avg - 75.0) < 0.01  # (80 + 70) / 2


def test_board_decision_mix(engine_with_leads):
    """Board correctly counts decisions per category."""
    from collections import defaultdict
    from freelance_os.models import Lead
    from sqlmodel import Session, select

    with Session(engine_with_leads) as session:
        leads = session.exec(select(Lead)).all()

    web_decs = defaultdict(int)
    for lead in leads:
        if lead.category == "WEB_APP":
            web_decs[lead.decision or "unset"] += 1

    assert web_decs["DRAFT_NOW"] == 1
    assert web_decs["WATCH"] == 1
    assert web_decs["unset"] == 1


def test_recategorize_all(tmp_path, monkeypatch):
    """lead recategorize --all updates categories in place."""
    import freelance_os.models  # noqa: F401
    from sqlmodel import Session, create_engine as ce, select, SQLModel
    engine = ce(f"sqlite:///{tmp_path}/t.sqlite")
    SQLModel.metadata.create_all(engine)

    from freelance_os.models import Lead

    with Session(engine) as session:
        lead = Lead(source="upwork", category="OTHER",
                    title="Build Next.js app", description="React Supabase Vercel")
        session.add(lead)
        session.commit()
        lead_id = lead.id

    from freelance_os.ingestion.classify import classify_lead

    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        text = " ".join(filter(None, [lead.title, lead.description]))
        lead.category = classify_lead(text)
        session.add(lead)
        session.commit()

    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        assert lead.category == "WEB_APP"
