import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from freelance_os.models import (
    ClientProject,
    Lead,
    Outcome,
    PortfolioItem,
    ProposalDraft,
)
from freelance_os.schemas import (
    ClientProjectStatus,
    Decision,
    LeadStatus,
    OutcomeResult,
)


@pytest.fixture
def engine(tmp_path):
    db_path = tmp_path / "test.sqlite"
    eng = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(eng)
    yield eng
    eng.dispose()


def test_lead_create_and_roundtrip(engine):
    with Session(engine) as session:
        lead = Lead(
            title="Build a Next.js dashboard",
            source="upwork",
            status=LeadStatus.NEW,
            decision=Decision.DRAFT_NOW,
        )
        session.add(lead)
        session.commit()
        session.refresh(lead)

    assert lead.id is not None
    assert lead.title == "Build a Next.js dashboard"
    assert lead.status == LeadStatus.NEW
    assert lead.decision == Decision.DRAFT_NOW


def test_lead_status_values_match_enum(engine):
    with Session(engine) as session:
        for status in LeadStatus:
            lead = Lead(title=f"Lead {status.value}", status=status)
            session.add(lead)
        session.commit()

    with Session(engine) as session:
        leads = session.exec(select(Lead)).all()
    statuses = {l.status for l in leads}
    assert statuses == {s.value for s in LeadStatus}


def test_proposal_draft_linked_to_lead(engine):
    with Session(engine, expire_on_commit=False) as session:
        lead = Lead(title="Test lead", status=LeadStatus.NEW)
        session.add(lead)
        session.commit()
        session.refresh(lead)
        lead_id = lead.id

        draft = ProposalDraft(
            lead_id=lead_id,
            draft_text="I'd approach this as a data pipeline problem.",
            technical_diagnosis="The bottleneck is ETL latency.",
        )
        session.add(draft)
        session.commit()
        session.refresh(draft)
        draft_id = draft.id
        draft_lead_id = draft.lead_id
        draft_version = draft.version
        draft_approved = draft.approved_by_user

    assert draft_id is not None
    assert draft_lead_id == lead_id
    assert draft_version == 1
    assert draft_approved is False


def test_portfolio_item_create(engine):
    with Session(engine) as session:
        item = PortfolioItem(
            name="Next.js + Supabase Platform",
            type="web_app",
            tags='["nextjs","supabase","prisma"]',
        )
        session.add(item)
        session.commit()
        session.refresh(item)

    assert item.id is not None
    assert item.name == "Next.js + Supabase Platform"


def test_client_project_create(engine):
    with Session(engine) as session:
        project = ClientProject(
            client_name="ACME Corp",
            project_name="acme-dashboard",
            status=ClientProjectStatus.INTAKE,
        )
        session.add(project)
        session.commit()
        session.refresh(project)

    assert project.id is not None
    assert project.status == ClientProjectStatus.INTAKE


def test_outcome_linked_to_lead(engine):
    with Session(engine, expire_on_commit=False) as session:
        lead = Lead(title="Outcome test lead", status=LeadStatus.WON)
        session.add(lead)
        session.commit()
        session.refresh(lead)
        lead_id = lead.id

        outcome = Outcome(
            lead_id=lead_id,
            result=OutcomeResult.WON,
            final_rate=85.0,
            lessons="Clear scope from the start worked well.",
        )
        session.add(outcome)
        session.commit()
        session.refresh(outcome)
        outcome_id = outcome.id
        outcome_lead_id = outcome.lead_id
        outcome_result = outcome.result

    assert outcome_id is not None
    assert outcome_lead_id == lead_id
    assert outcome_result == OutcomeResult.WON
