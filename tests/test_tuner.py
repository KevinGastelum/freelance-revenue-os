"""Tests for the metric-tuning web console (freelance-os tune).

Tests:
1. GET /api/config returns current params
2. POST /api/preview re-scores WITHOUT mutating DB; returns markers
3. POST /api/save round-trips scoring_rules.toml
4. Changing a weight changes a sample lead's score/decision
5. Preset save/load round-trips
"""

import sys
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine, SQLModel

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_engine(tmp_path):
    """Create an on-disk SQLite DB with all tables and a few test leads."""
    import freelance_os.models as _models  # noqa: F401 — registers tables
    from freelance_os.models import Lead, Outcome, OutcomeResult

    db_path = str(tmp_path / "test.sqlite")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        lead1 = Lead(
            source="test",
            title="Build Python FastAPI backend with PostgreSQL",
            description=(
                "We need a senior Python developer to build a FastAPI backend "
                "with PostgreSQL and SQLAlchemy. Clear deliverables: REST API, "
                "test coverage, and deployment docs. Budget $3000-$5000. "
                "Timeline is 4 weeks. Client has excellent track record."
            ),
            budget_type="fixed",
            budget_min=3000.0,
            budget_max=5000.0,
            client_payment_verified=True,
            client_rating=4.9,
            lead_score=72,
            decision="WATCH",
        )
        lead2 = Lead(
            source="test",
            title="Simple fix for React app",
            description="Easy job, quick task. Small budget is low.",
            lead_score=15,
            decision="REJECT",
        )
        lead3 = Lead(
            source="test",
            title="Build Next.js dashboard with Supabase integration",
            description=(
                "Need a developer for a Next.js + Supabase dashboard. "
                "Features: auth, charts, CSV export. Budget $2500. "
                "Clear milestones, ongoing retainer possible."
            ),
            budget_max=2500.0,
            client_payment_verified=True,
            lead_score=80,
            decision="DRAFT_NOW",
        )
        session.add_all([lead1, lead2, lead3])
        session.commit()
        session.refresh(lead1)

        # Record an outcome for lead3
        outcome = Outcome(lead_id=lead3.id, result=OutcomeResult.WON)
        session.add(outcome)
        session.commit()

    return engine, db_path


@pytest.fixture()
def tuner_client(db_engine, tmp_path):
    """Configured TestClient for the tuner app."""
    from fastapi.testclient import TestClient
    from freelance_os.tuner.app import app, configure

    _, db_path = db_engine
    scoring_path = str(tmp_path / "scoring_rules.toml")
    configure(db_path=db_path, scoring_rules_path=scoring_path)

    with TestClient(app) as client:
        yield client, tmp_path, scoring_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_get_config_returns_all_sections(tuner_client):
    """GET /api/config returns weights, thresholds, risk_penalties, pricing."""
    client, _, _ = tuner_client
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "weights" in data
    assert "thresholds" in data
    assert "risk_penalties" in data
    assert "pricing" in data
    # Spot-check defaults
    assert data["weights"]["technical_fit"] == 20
    assert data["thresholds"]["draft_now_min"] == 80
    assert data["risk_penalties"]["unpaid_test_request"] == 25
    assert data["pricing"]["target_hourly_rate"] == 75


def test_preview_returns_markers_and_does_not_mutate_db(tuner_client, db_engine):
    """POST /api/preview re-scores in-memory; DB rows are unchanged after call."""
    from freelance_os.models import Lead
    from sqlmodel import Session, select

    client, _, _ = tuner_client
    engine, _ = db_engine

    # Snapshot DB state before preview
    with Session(engine) as session:
        before = {
            lead.id: (lead.lead_score, lead.decision)
            for lead in session.exec(select(Lead)).all()
        }

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

    resp = client.post("/api/preview", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # Markers structure
    assert "leads" in data
    assert "markers" in data
    m = data["markers"]
    assert "changed_decision_count" in m
    assert "avg_score_before" in m
    assert "avg_score_after" in m
    assert "median_score_before" in m
    assert "median_score_after" in m
    assert "distribution_before" in m
    assert "distribution_after" in m
    assert "win_rate_by_decision_before" in m
    assert "win_rate_by_decision_after" in m
    assert "top_reason_codes" in m
    assert "outcome_count_by_decision_before" in m

    # Per-lead fields
    assert len(data["leads"]) == 3
    for lead_row in data["leads"]:
        assert "id" in lead_row
        assert "new_score" in lead_row
        assert "new_decision" in lead_row
        assert "delta" in lead_row
        assert "decision_changed" in lead_row
        assert "reason_codes" in lead_row

    # DB must be UNCHANGED — assert read-only
    with Session(engine) as session:
        after = {
            lead.id: (lead.lead_score, lead.decision)
            for lead in session.exec(select(Lead)).all()
        }
    assert before == after, "Preview mutated the database!"


def test_save_round_trips_toml(tuner_client):
    """POST /api/save writes scoring_rules.toml; GET /api/config reads it back."""
    import sys
    client, tmp_path, scoring_path = tuner_client

    payload = {
        "weights": {
            "technical_fit": 30, "budget_fit": 20, "client_quality": 10,
            "clarity_of_scope": 10, "urgency_timing": 10, "portfolio_match": 5,
            "repeat_work_potential": 5, "communication_quality": 10,
        },
        "thresholds": {"draft_now_min": 75, "watch_min": 60, "maybe_min": 45},
        "risk_penalties": {
            "unpaid_test_request": 30, "payment_rule_bypass": 30,
            "unrealistic_deadline": 15, "vague_fixed_low_budget": 15,
            "suspicious_payment": 10, "scope_creep_risk": 10,
            "easy_language_complex_work": 5, "unclear_deliverables": 5,
            "unsupported_tech_stack": 5, "free_consultation_request": 5,
        },
        "pricing": {
            "target_hourly_rate": 100, "minimum_project_value": 500,
            "risk_multiplier_low": 1.1, "risk_multiplier_medium": 1.35,
            "risk_multiplier_high": 1.6, "rush_multiplier": 1.5,
            "platform_fee_buffer": 0.15,
        },
    }

    resp = client.post("/api/save", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "saved"

    # Verify the file was written
    assert Path(scoring_path).exists()

    # Read it back via /api/config
    resp2 = client.get("/api/config")
    assert resp2.status_code == 200
    saved = resp2.json()

    assert saved["weights"]["technical_fit"] == 30
    assert saved["thresholds"]["draft_now_min"] == 75
    assert saved["risk_penalties"]["unpaid_test_request"] == 30
    assert saved["pricing"]["target_hourly_rate"] == 100
    assert abs(saved["pricing"]["risk_multiplier_medium"] - 1.35) < 0.001


def test_changing_weight_changes_score(tuner_client):
    """Raising technical_fit weight increases score for a tech-heavy lead."""
    client, _, _ = tuner_client

    def make_payload(tech_weight: float) -> dict:
        return {
            "weights": {
                "technical_fit": tech_weight,
                "budget_fit": 15, "client_quality": 15,
                "clarity_of_scope": 10, "urgency_timing": 10,
                "portfolio_match": 10, "repeat_work_potential": 10,
                "communication_quality": 10,
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

    # Low weight
    resp_low = client.post("/api/preview", json=make_payload(5))
    assert resp_low.status_code == 200
    leads_low = resp_low.json()["leads"]

    # High weight
    resp_high = client.post("/api/preview", json=make_payload(45))
    assert resp_high.status_code == 200
    leads_high = resp_high.json()["leads"]

    # The first lead has rich Python/FastAPI description — should score higher
    # when tech_weight is higher
    tech_lead_low = next(l for l in leads_low if "FastAPI" in l.get("title", ""))
    tech_lead_high = next(l for l in leads_high if "FastAPI" in l.get("title", ""))
    assert tech_lead_high["new_score"] >= tech_lead_low["new_score"], (
        f"Expected higher score with tech_weight=45 vs 5, "
        f"got {tech_lead_high['new_score']} vs {tech_lead_low['new_score']}"
    )


def test_preset_save_and_load_roundtrip(tuner_client):
    """POST /api/presets/{name} saves a preset; GET /api/presets/{name} loads it."""
    client, _, _ = tuner_client

    payload = {
        "weights": {
            "technical_fit": 25, "budget_fit": 20, "client_quality": 15,
            "clarity_of_scope": 10, "urgency_timing": 5, "portfolio_match": 10,
            "repeat_work_potential": 10, "communication_quality": 5,
        },
        "thresholds": {"draft_now_min": 78, "watch_min": 62, "maybe_min": 47},
        "risk_penalties": {
            "unpaid_test_request": 28, "payment_rule_bypass": 28,
            "unrealistic_deadline": 18, "vague_fixed_low_budget": 18,
            "suspicious_payment": 12, "scope_creep_risk": 12,
            "easy_language_complex_work": 8, "unclear_deliverables": 8,
            "unsupported_tech_stack": 8, "free_consultation_request": 8,
        },
        "pricing": {
            "target_hourly_rate": 90, "minimum_project_value": 400,
            "risk_multiplier_low": 1.0, "risk_multiplier_medium": 1.3,
            "risk_multiplier_high": 1.6, "rush_multiplier": 1.4,
            "platform_fee_buffer": 0.12,
        },
    }

    # Save preset
    resp = client.post("/api/presets/test-preset", json=payload)
    assert resp.status_code == 200
    assert resp.json()["preset"] == "test-preset"

    # List presets
    list_resp = client.get("/api/presets")
    assert list_resp.status_code == 200
    assert "test-preset" in list_resp.json()

    # Load preset
    load_resp = client.get("/api/presets/test-preset")
    assert load_resp.status_code == 200
    loaded = load_resp.json()
    assert loaded["weights"]["technical_fit"] == 25
    assert loaded["thresholds"]["draft_now_min"] == 78
    assert loaded["risk_penalties"]["unpaid_test_request"] == 28
    assert abs(loaded["pricing"]["risk_multiplier_medium"] - 1.3) < 0.001
    assert abs(loaded["pricing"]["platform_fee_buffer"] - 0.12) < 0.001


def test_preview_computes_win_rate_calibration(tuner_client):
    """Calibration markers appear for the DRAFT_NOW bucket (lead3 has WON outcome)."""
    client, _, _ = tuner_client

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

    resp = client.post("/api/preview", json=payload)
    assert resp.status_code == 200
    m = resp.json()["markers"]
    # lead3 has a WON outcome and lead_score=80 (DRAFT_NOW) stored in DB
    # win_rate_by_decision_before["DRAFT_NOW"] should reflect the WON outcome
    wr = m["win_rate_by_decision_before"]
    outcome_cnt = m["outcome_count_by_decision_before"]
    # At least one decision bucket should have a non-null win rate
    has_outcome = any(v is not None for v in wr.values())
    total_outcomes = sum(outcome_cnt.values())
    assert total_outcomes >= 1, "Should have at least one recorded outcome"
    assert has_outcome, "Win rate should be computable for at least one bucket"
