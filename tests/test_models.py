"""Phase 1: Tests for model creation and enums."""

import pytest
from datetime import datetime
from sqlmodel import Session, select

from freelance_os.models import (
    ClientProject,
    ClientProjectStatus,
    Decision,
    Lead,
    LeadStatus,
    Outcome,
    OutcomeResult,
    PortfolioItem,
    ProposalDraft,
    encode_json,
    decode_json,
)


def test_lead_status_enum_values():
    assert LeadStatus.NEW == "NEW"
    assert LeadStatus.SCORED == "SCORED"
    assert LeadStatus.WON == "WON"
    assert LeadStatus.REJECTED == "REJECTED"
    assert len(LeadStatus) == 10


def test_decision_enum_values():
    assert Decision.DRAFT_NOW == "DRAFT_NOW"
    assert Decision.WATCH == "WATCH"
    assert Decision.MAYBE == "MAYBE"
    assert Decision.REJECT == "REJECT"
    assert len(Decision) == 4


def test_client_project_status_enum():
    assert ClientProjectStatus.INTAKE == "INTAKE"
    assert ClientProjectStatus.ACTIVE == "ACTIVE"
    assert ClientProjectStatus.COMPLETE == "COMPLETE"
    assert len(ClientProjectStatus) == 8


def test_outcome_result_enum():
    assert OutcomeResult.WON == "WON"
    assert OutcomeResult.LOST == "LOST"
    assert OutcomeResult.NO_RESPONSE == "NO_RESPONSE"
    assert OutcomeResult.WITHDRAWN == "WITHDRAWN"


def test_lead_defaults(tmp_db):
    with Session(tmp_db) as session:
        lead = Lead(source="test")
        session.add(lead)
        session.commit()
        session.refresh(lead)
        assert lead.id is not None
        assert lead.status == LeadStatus.NEW
        assert lead.client_payment_verified is False
        assert lead.imported_at is not None


def test_lead_with_all_fields(tmp_db):
    with Session(tmp_db) as session:
        lead = Lead(
            source="upwork",
            source_url="https://upwork.com/jobs/123",
            title="Build FastAPI backend",
            description="We need a FastAPI backend with PostgreSQL",
            client_name="ACME Corp",
            client_rating=4.8,
            client_payment_verified=True,
            budget_type="fixed",
            budget_min=1000.0,
            budget_max=3000.0,
            country="US",
            status=LeadStatus.NEW,
        )
        session.add(lead)
        session.commit()
        session.refresh(lead)

        fetched = session.get(Lead, lead.id)
        assert fetched.title == "Build FastAPI backend"
        assert fetched.client_payment_verified is True
        assert fetched.budget_max == 3000.0


def test_proposal_draft_defaults(tmp_db):
    with Session(tmp_db) as session:
        lead = Lead(source="test")
        session.add(lead)
        session.commit()
        session.refresh(lead)

        draft = ProposalDraft(lead_id=lead.id)
        session.add(draft)
        session.commit()
        session.refresh(draft)

        assert draft.id is not None
        assert draft.version == 1
        assert draft.approved_by_user is False


def test_portfolio_item_creation(tmp_db):
    with Session(tmp_db) as session:
        item = PortfolioItem(
            name="Test Project",
            type="web_app",
            description="A test project",
            tags='["python", "fastapi"]',
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        assert item.id is not None
        assert item.name == "Test Project"


def test_client_project_creation(tmp_db):
    with Session(tmp_db) as session:
        lead = Lead(source="test")
        session.add(lead)
        session.commit()
        session.refresh(lead)

        project = ClientProject(
            lead_id=lead.id,
            client_name="ACME",
            project_name="dashboard",
            status=ClientProjectStatus.INTAKE,
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        assert project.id is not None
        assert project.status == ClientProjectStatus.INTAKE


def test_outcome_creation(tmp_db):
    with Session(tmp_db) as session:
        lead = Lead(source="test")
        session.add(lead)
        session.commit()
        session.refresh(lead)

        outcome = Outcome(
            lead_id=lead.id,
            result=OutcomeResult.WON,
            final_budget=1500.0,
        )
        session.add(outcome)
        session.commit()
        session.refresh(outcome)
        assert outcome.id is not None
        assert outcome.result == OutcomeResult.WON


def test_encode_decode_json():
    data = ["TECH_MATCH", "HIGH_BUDGET"]
    encoded = encode_json(data)
    assert isinstance(encoded, str)
    decoded = decode_json(encoded)
    assert decoded == data


def test_encode_decode_json_none():
    assert encode_json(None) is None
    assert decode_json(None) is None
