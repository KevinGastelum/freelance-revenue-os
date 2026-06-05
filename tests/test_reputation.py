"""Tests for CC-5: reputation aggregation, model fields, and /api/reputation endpoint."""

import pytest
from datetime import datetime
from sqlmodel import Session, SQLModel, create_engine, select

import freelance_os.models as _m  # noqa: F401 — register tables


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def engine(tmp_path):
    db_path = str(tmp_path / "rep_test.sqlite")
    eng = create_engine(f"sqlite:///{db_path}", echo=False)
    SQLModel.metadata.create_all(eng)
    return eng, db_path


def _seed(engine, outcomes_spec):
    """Insert leads + outcomes. outcomes_spec = list of dicts with keys:
    source, result, final_budget, rating, on_time, is_repeat_client, platform
    """
    from freelance_os.models import Lead, LeadStatus, Outcome, OutcomeResult

    with Session(engine) as session:
        leads = []
        for i, spec in enumerate(outcomes_spec):
            lead = Lead(
                source=spec.get("source", "upwork"),
                status=LeadStatus.WON if spec.get("result") == "WON" else LeadStatus.LOST,
            )
            session.add(lead)
            leads.append(lead)
        session.commit()
        for lead in leads:
            session.refresh(lead)

        for lead, spec in zip(leads, outcomes_spec):
            o = Outcome(
                lead_id=lead.id,
                result=OutcomeResult(spec["result"]),
                final_budget=spec.get("final_budget"),
                rating=spec.get("rating"),
                on_time=spec.get("on_time"),
                is_repeat_client=spec.get("is_repeat_client"),
                platform=spec.get("platform"),
            )
            session.add(o)
        session.commit()


# ---------------------------------------------------------------------------
# Model field persistence
# ---------------------------------------------------------------------------

def test_outcome_new_fields_persist(engine):
    """New reputation fields round-trip through SQLite correctly."""
    from freelance_os.models import Lead, LeadStatus, Outcome, OutcomeResult

    eng, _ = engine
    with Session(eng) as session:
        lead = Lead(source="upwork", status=LeadStatus.WON)
        session.add(lead)
        session.commit()
        session.refresh(lead)

        o = Outcome(
            lead_id=lead.id,
            result=OutcomeResult.WON,
            final_budget=1500.0,
            rating=4.7,
            review_text="Great work, fast delivery!",
            on_time=True,
            is_repeat_client=True,
            platform="upwork",
            delivered_at=datetime(2026, 5, 1, 12, 0),
        )
        session.add(o)
        session.commit()
        session.refresh(o)
        oid = o.id

    with Session(eng) as session:
        found = session.get(Outcome, oid)
        assert found is not None
        assert found.rating == pytest.approx(4.7)
        assert found.review_text == "Great work, fast delivery!"
        assert found.on_time is True
        assert found.is_repeat_client is True
        assert found.platform == "upwork"
        assert found.delivered_at == datetime(2026, 5, 1, 12, 0)


def test_outcome_new_fields_nullable(engine):
    """Existing Outcome creation still works when new fields are absent."""
    from freelance_os.models import Lead, LeadStatus, Outcome, OutcomeResult

    eng, _ = engine
    with Session(eng) as session:
        lead = Lead(source="fiverr", status=LeadStatus.LOST)
        session.add(lead)
        session.commit()
        session.refresh(lead)

        o = Outcome(lead_id=lead.id, result=OutcomeResult.LOST)
        session.add(o)
        session.commit()
        session.refresh(o)
        oid = o.id

    with Session(eng) as session:
        found = session.get(Outcome, oid)
        assert found.rating is None
        assert found.on_time is None
        assert found.is_repeat_client is None
        assert found.platform is None


# ---------------------------------------------------------------------------
# Aggregation math
# ---------------------------------------------------------------------------

def test_win_rate_calculation(engine):
    eng, db_path = engine
    _seed(eng, [
        {"result": "WON", "source": "upwork"},
        {"result": "WON", "source": "upwork"},
        {"result": "LOST", "source": "upwork"},
    ])
    from freelance_os.reports.reputation import aggregate_reputation
    data = aggregate_reputation({"paths": {"database_path": db_path}})
    assert data["wins"] == 2
    assert data["losses"] == 1
    assert data["win_rate"] == pytest.approx(2 / 3)


def test_avg_rating(engine):
    eng, db_path = engine
    _seed(eng, [
        {"result": "WON", "rating": 5.0},
        {"result": "WON", "rating": 4.0},
        {"result": "LOST"},  # no rating
    ])
    from freelance_os.reports.reputation import aggregate_reputation
    data = aggregate_reputation({"paths": {"database_path": db_path}})
    assert data["avg_rating"] == pytest.approx(4.5)


def test_avg_rating_none_when_no_ratings(engine):
    eng, db_path = engine
    _seed(eng, [
        {"result": "WON"},
        {"result": "LOST"},
    ])
    from freelance_os.reports.reputation import aggregate_reputation
    data = aggregate_reputation({"paths": {"database_path": db_path}})
    assert data["avg_rating"] is None


def test_on_time_pct(engine):
    eng, db_path = engine
    _seed(eng, [
        {"result": "WON", "on_time": True},
        {"result": "WON", "on_time": True},
        {"result": "LOST", "on_time": False},
    ])
    from freelance_os.reports.reputation import aggregate_reputation
    data = aggregate_reputation({"paths": {"database_path": db_path}})
    assert data["on_time_pct"] == pytest.approx(2 / 3)


def test_total_earnings(engine):
    eng, db_path = engine
    _seed(eng, [
        {"result": "WON", "final_budget": 1000.0},
        {"result": "WON", "final_budget": 2500.0},
        {"result": "LOST"},
    ])
    from freelance_os.reports.reputation import aggregate_reputation
    data = aggregate_reputation({"paths": {"database_path": db_path}})
    assert data["total_earnings"] == pytest.approx(3500.0)
    assert data["avg_project_value"] == pytest.approx(1750.0)


def test_repeat_client_count(engine):
    eng, db_path = engine
    _seed(eng, [
        {"result": "WON", "is_repeat_client": True},
        {"result": "WON", "is_repeat_client": True},
        {"result": "WON", "is_repeat_client": False},
    ])
    from freelance_os.reports.reputation import aggregate_reputation
    data = aggregate_reputation({"paths": {"database_path": db_path}})
    assert data["repeat_client_count"] == 2


# ---------------------------------------------------------------------------
# Per-platform breakdown
# ---------------------------------------------------------------------------

def test_per_platform_breakdown(engine):
    eng, db_path = engine
    _seed(eng, [
        {"result": "WON", "platform": "upwork", "final_budget": 1000.0, "rating": 5.0},
        {"result": "LOST", "platform": "upwork"},
        {"result": "WON", "platform": "fiverr", "final_budget": 300.0, "rating": 4.0},
    ])
    from freelance_os.reports.reputation import aggregate_reputation
    data = aggregate_reputation({"paths": {"database_path": db_path}})

    pp = {p["platform"]: p for p in data["per_platform"]}
    assert "upwork" in pp
    assert "fiverr" in pp

    uw = pp["upwork"]
    assert uw["wins"] == 1
    assert uw["losses"] == 1
    assert uw["win_rate"] == pytest.approx(0.5)
    assert uw["avg_rating"] == pytest.approx(5.0)
    assert uw["earnings"] == pytest.approx(1000.0)

    fv = pp["fiverr"]
    assert fv["wins"] == 1
    assert fv["losses"] == 0
    assert fv["win_rate"] == pytest.approx(1.0)
    assert fv["avg_rating"] == pytest.approx(4.0)


def test_per_platform_falls_back_to_lead_source(engine):
    """If outcome.platform is None, fall back to lead.source."""
    from freelance_os.models import Lead, LeadStatus, Outcome, OutcomeResult
    eng, db_path = engine

    with Session(eng) as session:
        lead = Lead(source="contra", status=LeadStatus.WON)
        session.add(lead)
        session.commit()
        session.refresh(lead)
        o = Outcome(lead_id=lead.id, result=OutcomeResult.WON, final_budget=500.0)
        session.add(o)
        session.commit()

    from freelance_os.reports.reputation import aggregate_reputation
    data = aggregate_reputation({"paths": {"database_path": db_path}})
    pp = {p["platform"]: p for p in data["per_platform"]}
    assert "contra" in pp
    assert pp["contra"]["wins"] == 1


# ---------------------------------------------------------------------------
# Momentum
# ---------------------------------------------------------------------------

def test_momentum_groups_by_month(engine):
    from freelance_os.models import Lead, LeadStatus, Outcome, OutcomeResult
    eng, db_path = engine

    with Session(eng) as session:
        for i, (month, result, budget) in enumerate([
            ("2026-01", OutcomeResult.WON, 1000.0),
            ("2026-01", OutcomeResult.LOST, None),
            ("2026-02", OutcomeResult.WON, 2000.0),
        ]):
            lead = Lead(source="upwork", status=LeadStatus.WON if result == OutcomeResult.WON else LeadStatus.LOST)
            session.add(lead)
            session.commit()
            session.refresh(lead)
            o = Outcome(
                lead_id=lead.id,
                result=result,
                final_budget=budget,
                created_at=datetime.fromisoformat(f"{month}-15T00:00:00"),
            )
            session.add(o)
        session.commit()

    from freelance_os.reports.reputation import aggregate_reputation
    data = aggregate_reputation({"paths": {"database_path": db_path}})
    periods = {m["period"]: m for m in data["momentum"]}
    assert "2026-01" in periods
    assert "2026-02" in periods
    assert periods["2026-01"]["wins"] == 1
    assert periods["2026-01"]["losses"] == 1
    assert periods["2026-01"]["earnings"] == pytest.approx(1000.0)
    assert periods["2026-02"]["wins"] == 1
    assert periods["2026-02"]["earnings"] == pytest.approx(2000.0)


# ---------------------------------------------------------------------------
# Empty DB edge case
# ---------------------------------------------------------------------------

def test_empty_db_returns_zeros(engine):
    eng, db_path = engine
    from freelance_os.reports.reputation import aggregate_reputation
    data = aggregate_reputation({"paths": {"database_path": db_path}})
    assert data["wins"] == 0
    assert data["losses"] == 0
    assert data["win_rate"] is None
    assert data["avg_rating"] is None
    assert data["total_earnings"] == 0.0
    assert data["per_platform"] == []
    assert data["momentum"] == []


# ---------------------------------------------------------------------------
# API endpoint /api/reputation
# ---------------------------------------------------------------------------

@pytest.fixture()
def api_client(engine):
    from fastapi.testclient import TestClient
    from freelance_os.tuner.app import app, configure

    eng, db_path = engine
    configure(db_path=db_path, scoring_rules_path="", config_dir="")
    with TestClient(app) as tc:
        yield tc, eng, db_path


def test_api_reputation_empty(api_client):
    tc, _, _ = api_client
    resp = tc.get("/api/reputation")
    assert resp.status_code == 200
    data = resp.json()
    assert "wins" in data
    assert "win_rate" in data
    assert "per_platform" in data
    assert "momentum" in data
    assert isinstance(data["per_platform"], list)
    assert isinstance(data["momentum"], list)


def test_api_reputation_with_data(api_client):
    tc, eng, db_path = api_client
    _seed(eng, [
        {"result": "WON", "platform": "upwork", "final_budget": 2000.0, "rating": 4.5, "on_time": True},
        {"result": "LOST", "platform": "fiverr"},
        {"result": "WON", "platform": "upwork", "final_budget": 1500.0, "is_repeat_client": True},
    ])
    resp = tc.get("/api/reputation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["wins"] == 2
    assert data["losses"] == 1
    assert data["total_earnings"] == pytest.approx(3500.0)
    assert data["avg_rating"] == pytest.approx(4.5)
    assert data["on_time_pct"] == pytest.approx(1.0)
    assert data["repeat_client_count"] == 1

    pp = {p["platform"]: p for p in data["per_platform"]}
    assert "upwork" in pp
    assert pp["upwork"]["wins"] == 2
    assert pp["upwork"]["earnings"] == pytest.approx(3500.0)

    assert "fiverr" in pp
    assert pp["fiverr"]["losses"] == 1
