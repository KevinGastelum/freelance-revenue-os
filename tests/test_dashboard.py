"""Tests for the Command Center dashboard API endpoints.

Covers:
- GET /api/leads (all, with filters)
- GET /api/leads/{id} (detail + draft)
- POST /api/leads/{id}/action (score, estimate, draft, validate, status, save_draft)
- GET /api/sources
- GET /api/quickwins
- Existing tuner endpoints still pass (smoke check)
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_engine(tmp_path):
    """SQLite DB with three test leads of varying data."""
    import freelance_os.models as _m  # noqa: F401 — registers tables
    from freelance_os.models import Decision, Lead, LeadStatus

    db_path = str(tmp_path / "dash_test.sqlite")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        lead1 = Lead(
            source="upwork",
            title="Build Python FastAPI backend with PostgreSQL",
            description=(
                "Need a FastAPI + PostgreSQL backend. Budget $3000. "
                "Deliverables: REST API, test coverage, deployment docs."
            ),
            category="WEB_APP",
            budget_max=3000.0,
            client_payment_verified=True,
            client_rating=4.8,
            lead_score=72,
            decision=Decision.WATCH,
            status=LeadStatus.SCORED,
            effort_hours_low=8,
            effort_hours_high=16,
            feasibility_confidence="MED",
            warren_feasible=True,
            suggested_price=1020.0,
            suggested_turnaround_days=3,
        )
        lead2 = Lead(
            source="fiverr",
            title="Quick bug fix for React app",
            description="Simple one-page fix. Basic small budget.",
            category="BUG_FIX",
            budget_max=200.0,
            lead_score=15,
            decision=Decision.REJECT,
            status=LeadStatus.SCORED,
            effort_hours_low=2,
            effort_hours_high=4,
            feasibility_confidence="HIGH",
            warren_feasible=True,
            suggested_price=300.0,
            suggested_turnaround_days=1,
        )
        lead3 = Lead(
            source="upwork",
            title="Data dashboard with charts and Supabase",
            description=(
                "Need a Next.js + Supabase dashboard. Clear milestones. Budget $2500. "
                "Features: auth, charts, CSV export. Ongoing retainer possible."
            ),
            category="DATA_DASHBOARD",
            budget_max=2500.0,
            lead_score=80,
            decision=Decision.DRAFT_NOW,
            status=LeadStatus.NEW,
        )
        session.add_all([lead1, lead2, lead3])
        session.commit()

    return engine, db_path


@pytest.fixture()
def client(db_engine, tmp_path):
    """TestClient configured against the dashboard app."""
    from fastapi.testclient import TestClient
    from freelance_os.tuner.app import app, configure

    _, db_path = db_engine
    scoring_path = str(tmp_path / "scoring_rules.toml")
    configure(db_path=db_path, scoring_rules_path=scoring_path, config_dir=str(tmp_path))

    with TestClient(app) as tc:
        yield tc, db_engine


# ---------------------------------------------------------------------------
# /api/leads — listing and filtering
# ---------------------------------------------------------------------------


def test_list_leads_returns_all(client):
    tc, _ = client
    resp = tc.get("/api/leads")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    # Required fields present in every row
    for l in data:
        for field in ("id", "title", "category", "source", "lead_score",
                      "decision", "status", "effort_hours_low", "effort_hours_high",
                      "warren_feasible", "suggested_price"):
            assert field in l, f"Missing field {field!r}"


def test_list_leads_filter_source(client):
    tc, _ = client
    resp = tc.get("/api/leads?source=upwork")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(l["source"] == "upwork" for l in data)


def test_list_leads_filter_category(client):
    tc, _ = client
    resp = tc.get("/api/leads?category=BUG_FIX")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["category"] == "BUG_FIX"


def test_list_leads_filter_decision(client):
    tc, _ = client
    resp = tc.get("/api/leads?decision=WATCH")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["decision"] == "WATCH"


def test_list_leads_filter_status(client):
    tc, _ = client
    resp = tc.get("/api/leads?status=NEW")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "NEW"


def test_list_leads_filter_min_score(client):
    tc, _ = client
    resp = tc.get("/api/leads?min_score=70")
    assert resp.status_code == 200
    data = resp.json()
    # lead1 (72) and lead3 (80) qualify; lead2 (15) does not
    assert len(data) == 2
    assert all((l["lead_score"] or 0) >= 70 for l in data)


def test_list_leads_filter_warren_feasible_true(client):
    tc, _ = client
    resp = tc.get("/api/leads?warren_feasible=true")
    assert resp.status_code == 200
    data = resp.json()
    # lead1 and lead2 have warren_feasible=True; lead3 does not
    assert len(data) == 2
    assert all(l["warren_feasible"] for l in data)


def test_list_leads_filter_warren_feasible_false(client):
    tc, _ = client
    resp = tc.get("/api/leads?warren_feasible=false")
    assert resp.status_code == 200
    data = resp.json()
    # lead3 has warren_feasible=None (not False), so 0 results
    assert all(not l["warren_feasible"] for l in data)


def test_list_leads_quickwins_only(client):
    tc, _ = client
    resp = tc.get("/api/leads?quickwins_only=true")
    assert resp.status_code == 200
    data = resp.json()
    # lead1 (warren=True, MED, effort set) and lead2 (warren=True, HIGH, effort set)
    assert len(data) == 2
    assert all(l["warren_feasible"] for l in data)
    assert all(l["feasibility_confidence"] in ("MED", "HIGH") for l in data)


def test_list_leads_sort_by_score_desc(client):
    tc, _ = client
    resp = tc.get("/api/leads?sort_by=score&order=desc")
    assert resp.status_code == 200
    data = resp.json()
    scores = [l["lead_score"] or 0 for l in data]
    assert scores == sorted(scores, reverse=True)


def test_list_leads_sort_by_score_asc(client):
    tc, _ = client
    resp = tc.get("/api/leads?sort_by=score&order=asc")
    assert resp.status_code == 200
    data = resp.json()
    scores = [l["lead_score"] or 0 for l in data]
    assert scores == sorted(scores)


# ---------------------------------------------------------------------------
# /api/leads/{id} — detail
# ---------------------------------------------------------------------------


def test_get_lead_detail_fields(client):
    tc, _ = client
    resp = tc.get("/api/leads")
    lead_id = resp.json()[0]["id"]

    resp = tc.get(f"/api/leads/{lead_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == lead_id
    assert "description" in data
    assert "draft" in data  # key present, value may be None


def test_get_lead_detail_not_found(client):
    tc, _ = client
    resp = tc.get("/api/leads/99999")
    assert resp.status_code == 404


def test_get_lead_detail_draft_is_none_initially(client):
    tc, _ = client
    # lead3 (NEW, no draft yet)
    resp = tc.get("/api/leads")
    lead3 = next(l for l in resp.json() if l["title"].startswith("Data dashboard"))
    lead_id = lead3["id"]

    resp = tc.get(f"/api/leads/{lead_id}")
    assert resp.status_code == 200
    assert resp.json()["draft"] is None


# ---------------------------------------------------------------------------
# /api/leads/{id}/action
# ---------------------------------------------------------------------------


def test_action_score_persists(client):
    from freelance_os.models import Lead, LeadStatus
    tc, (engine, _) = client

    resp = tc.get("/api/leads")
    lead3 = next(l for l in resp.json() if l["title"].startswith("Data dashboard"))
    lead_id = lead3["id"]

    resp = tc.post(f"/api/leads/{lead_id}/action", json={"action": "score", "params": {}})
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "score"
    assert "lead_score" in body["result"]
    assert "decision" in body["result"]

    # Verify DB was updated
    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        assert lead.lead_score is not None
        assert lead.status == LeadStatus.SCORED


def test_action_estimate_persists(client):
    from freelance_os.models import Lead
    tc, (engine, _) = client

    resp = tc.get("/api/leads")
    lead3 = next(l for l in resp.json() if l["title"].startswith("Data dashboard"))
    lead_id = lead3["id"]

    resp = tc.post(f"/api/leads/{lead_id}/action", json={"action": "estimate", "params": {}})
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "estimate"
    assert "effort_hours_low" in body["result"]
    assert "warren_feasible" in body["result"]

    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        assert lead.effort_hours_low is not None
        assert lead.effort_hours_high is not None
        assert lead.warren_feasible is not None


def test_action_draft_creates_proposal(client):
    from freelance_os.models import ProposalDraft
    from sqlmodel import select
    tc, (engine, _) = client

    resp = tc.get("/api/leads")
    lead_id = resp.json()[0]["id"]

    resp = tc.post(f"/api/leads/{lead_id}/action", json={"action": "draft", "params": {}})
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "draft"
    assert "draft_text" in body
    assert body["draft_text"]  # non-empty

    with Session(engine) as session:
        draft = session.exec(
            select(ProposalDraft).where(ProposalDraft.lead_id == lead_id)
        ).first()
        assert draft is not None
        assert draft.draft_text


def test_action_validate_after_draft(client):
    tc, _ = client
    resp = tc.get("/api/leads")
    lead_id = resp.json()[0]["id"]

    # Need a draft first
    tc.post(f"/api/leads/{lead_id}/action", json={"action": "draft", "params": {}})

    resp = tc.post(f"/api/leads/{lead_id}/action", json={"action": "validate", "params": {}})
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "validate"
    assert body["result"]["status"] in ("PASS", "WARN", "FAIL")
    assert isinstance(body["result"].get("reasons"), list)


def test_action_validate_no_draft_returns_400(client):
    tc, _ = client
    resp = tc.get("/api/leads")
    # lead3 (NEW, no draft)
    lead3 = next(l for l in resp.json() if l["title"].startswith("Data dashboard"))
    lead_id = lead3["id"]

    resp = tc.post(f"/api/leads/{lead_id}/action", json={"action": "validate", "params": {}})
    assert resp.status_code == 400


def test_action_status_persists(client):
    from freelance_os.models import Lead, LeadStatus
    tc, (engine, _) = client

    resp = tc.get("/api/leads")
    lead_id = resp.json()[0]["id"]

    resp = tc.post(f"/api/leads/{lead_id}/action", json={
        "action": "status",
        "params": {"status": "APPROVED_TO_APPLY"},
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "status"
    assert body["new_status"] == "APPROVED_TO_APPLY"

    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        assert lead.status == LeadStatus.APPROVED_TO_APPLY


def test_action_status_invalid_returns_400(client):
    tc, _ = client
    resp = tc.get("/api/leads")
    lead_id = resp.json()[0]["id"]

    resp = tc.post(f"/api/leads/{lead_id}/action", json={
        "action": "status",
        "params": {"status": "NOT_A_REAL_STATUS"},
    })
    assert resp.status_code == 400


def test_action_save_draft(client):
    from freelance_os.models import ProposalDraft
    from sqlmodel import select
    tc, (engine, _) = client

    resp = tc.get("/api/leads")
    lead_id = resp.json()[0]["id"]

    # Create a draft first
    tc.post(f"/api/leads/{lead_id}/action", json={"action": "draft", "params": {}})

    # Edit it
    new_text = "Custom edited draft text."
    resp = tc.post(f"/api/leads/{lead_id}/action", json={
        "action": "save_draft",
        "params": {"draft_text": new_text},
    })
    assert resp.status_code == 200
    assert resp.json()["saved"] is True

    with Session(engine) as session:
        draft = session.exec(
            select(ProposalDraft).where(ProposalDraft.lead_id == lead_id)
        ).first()
        assert draft.draft_text == new_text


def test_action_save_draft_no_draft_returns_400(client):
    tc, _ = client
    resp = tc.get("/api/leads")
    lead3 = next(l for l in resp.json() if l["title"].startswith("Data dashboard"))
    lead_id = lead3["id"]

    resp = tc.post(f"/api/leads/{lead_id}/action", json={
        "action": "save_draft",
        "params": {"draft_text": "text"},
    })
    assert resp.status_code == 400


def test_action_unknown_returns_400(client):
    tc, _ = client
    resp = tc.get("/api/leads")
    lead_id = resp.json()[0]["id"]

    resp = tc.post(f"/api/leads/{lead_id}/action", json={"action": "bogus", "params": {}})
    assert resp.status_code == 400


def test_action_lead_not_found_returns_404(client):
    tc, _ = client
    resp = tc.post("/api/leads/99999/action", json={"action": "score", "params": {}})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Lead detail includes draft after drafting
# ---------------------------------------------------------------------------


def test_lead_detail_includes_draft_after_action(client):
    tc, _ = client
    resp = tc.get("/api/leads")
    lead_id = resp.json()[0]["id"]

    tc.post(f"/api/leads/{lead_id}/action", json={"action": "draft", "params": {}})

    resp = tc.get(f"/api/leads/{lead_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["draft"] is not None
    assert data["draft"]["draft_text"]
    assert "validator_flags" in data["draft"]
    assert "portfolio_matches" in data["draft"]
    assert "clarifying_questions" in data["draft"]


# ---------------------------------------------------------------------------
# /api/sources
# ---------------------------------------------------------------------------


def test_get_sources_returns_list(client):
    """Returns a list (may be empty if no sources.yaml in tmp config dir)."""
    tc, _ = client
    resp = tc.get("/api/sources")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_sources_with_filters(client):
    """Filter params are accepted without error."""
    tc, _ = client
    resp = tc.get("/api/sources?category=WEB_APP&newcomer=true&region=global")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# /api/quickwins
# ---------------------------------------------------------------------------


def test_get_quickwins_returns_feasible_leads(client):
    tc, _ = client
    resp = tc.get("/api/quickwins")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # lead1 (warren=True, MED) and lead2 (warren=True, HIGH) qualify
    assert len(data) == 2
    assert all(l["warren_feasible"] for l in data)
    assert all(l["feasibility_confidence"] in ("MED", "HIGH") for l in data)


def test_get_quickwins_limit(client):
    tc, _ = client
    resp = tc.get("/api/quickwins?limit=1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 1


def test_get_quickwins_sorted_by_score_over_effort(client):
    """Lead with higher score/effort ratio comes first."""
    tc, _ = client
    resp = tc.get("/api/quickwins")
    data = resp.json()
    if len(data) >= 2:
        spe0 = (data[0]["lead_score"] or 50) / data[0]["effort_hours_high"]
        spe1 = (data[1]["lead_score"] or 50) / data[1]["effort_hours_high"]
        assert spe0 >= spe1


# ---------------------------------------------------------------------------
# Existing tuner endpoints still pass (smoke)
# ---------------------------------------------------------------------------


def test_tuner_get_config_still_works(client):
    tc, _ = client
    resp = tc.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "weights" in data
    assert "thresholds" in data
    assert "risk_penalties" in data
    assert "pricing" in data


def test_tuner_preview_still_works(client):
    tc, _ = client
    payload = {
        "weights": {
            "technical_fit": 20, "budget_fit": 15, "client_quality": 15,
            "clarity_of_scope": 10, "urgency_timing": 10, "portfolio_match": 10,
            "repeat_work_potential": 10, "communication_quality": 10,
        },
        "thresholds": {"draft_now_min": 80, "watch_min": 65, "maybe_min": 50},
        "risk_penalties": {
            "unpaid_test_request": 25, "payment_rule_bypass": 25,
            "unrealistic_deadline": 20, "vague_fixed_low_budget": 20,
            "suspicious_payment": 15, "scope_creep_risk": 15,
            "easy_language_complex_work": 10, "unclear_deliverables": 10,
            "unsupported_tech_stack": 10, "free_consultation_request": 10,
        },
        "pricing": {
            "target_hourly_rate": 75, "minimum_project_value": 300,
            "risk_multiplier_low": 1.0, "risk_multiplier_medium": 1.25,
            "risk_multiplier_high": 1.5, "rush_multiplier": 1.25,
            "platform_fee_buffer": 0.10,
        },
    }
    resp = tc.post("/api/preview", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "leads" in data
    assert "markers" in data
    assert len(data["leads"]) == 3


def test_tuner_save_still_works(client, tmp_path):
    tc, _ = client
    payload = {
        "weights": {
            "technical_fit": 25, "budget_fit": 15, "client_quality": 15,
            "clarity_of_scope": 10, "urgency_timing": 10, "portfolio_match": 5,
            "repeat_work_potential": 10, "communication_quality": 10,
        },
        "thresholds": {"draft_now_min": 80, "watch_min": 65, "maybe_min": 50},
        "risk_penalties": {
            "unpaid_test_request": 25, "payment_rule_bypass": 25,
            "unrealistic_deadline": 20, "vague_fixed_low_budget": 20,
            "suspicious_payment": 15, "scope_creep_risk": 15,
            "easy_language_complex_work": 10, "unclear_deliverables": 10,
            "unsupported_tech_stack": 10, "free_consultation_request": 10,
        },
        "pricing": {
            "target_hourly_rate": 75, "minimum_project_value": 300,
            "risk_multiplier_low": 1.0, "risk_multiplier_medium": 1.25,
            "risk_multiplier_high": 1.5, "rush_multiplier": 1.25,
            "platform_fee_buffer": 0.10,
        },
    }
    resp = tc.post("/api/save", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "saved"
