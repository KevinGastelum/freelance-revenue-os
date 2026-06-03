"""Phase 1: Tests for init and database creation."""

import pytest
from pathlib import Path
from sqlmodel import SQLModel, create_engine, inspect, Session, select


def test_create_tables_creates_all_models(tmp_path):
    """All model tables should be created."""
    import freelance_os.models  # noqa: F401
    from freelance_os.db import create_tables

    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    create_tables(engine, str(tmp_path / "test.db"))

    insp = inspect(engine)
    tables = set(insp.get_table_names())
    assert "lead" in tables
    assert "proposaldraft" in tables
    assert "portfolioitem" in tables
    assert "clientproject" in tables
    assert "outcome" in tables


def test_create_tables_is_idempotent(tmp_path):
    """Calling create_tables twice should not raise."""
    import freelance_os.models  # noqa: F401
    from freelance_os.db import create_tables

    db_path = str(tmp_path / "test.db")
    engine = create_engine(f"sqlite:///{db_path}")
    create_tables(engine, db_path)
    create_tables(engine, db_path)  # Should not raise


def test_drop_and_recreate_tables(tmp_path):
    """drop_tables then create_tables should work."""
    import freelance_os.models  # noqa: F401
    from freelance_os.db import create_tables, drop_tables

    db_path = str(tmp_path / "test.db")
    engine = create_engine(f"sqlite:///{db_path}")
    create_tables(engine, db_path)
    drop_tables(engine)
    create_tables(engine, db_path)

    insp = inspect(engine)
    assert "lead" in insp.get_table_names()


def test_lead_can_be_inserted(tmp_db):
    """Can insert a Lead into the database."""
    from freelance_os.models import Lead, LeadStatus

    with Session(tmp_db) as session:
        lead = Lead(source="test", title="Test lead")
        session.add(lead)
        session.commit()
        session.refresh(lead)
        assert lead.id is not None
        assert lead.status == LeadStatus.NEW


def test_proposal_draft_can_be_inserted(tmp_db):
    """Can insert a ProposalDraft linked to a Lead."""
    from freelance_os.models import Lead, ProposalDraft

    with Session(tmp_db) as session:
        lead = Lead(source="test", title="Test lead")
        session.add(lead)
        session.commit()
        session.refresh(lead)

        draft = ProposalDraft(lead_id=lead.id, draft_text="Test proposal")
        session.add(draft)
        session.commit()
        session.refresh(draft)
        assert draft.id is not None
        assert draft.lead_id == lead.id
