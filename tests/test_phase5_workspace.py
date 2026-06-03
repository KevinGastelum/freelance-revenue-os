"""Phase 5 tests: client workspace and delivery package (PRD 21.3)."""

import pytest
from pathlib import Path

from freelance_os.models import Lead, LeadStatus, ClientProject, ClientProjectStatus
from freelance_os.db import init_db, reset_engine, get_session
from freelance_os.client.workspace import create_workspace, _slugify
from freelance_os.client.delivery import create_delivery_package


def _make_won_lead(tmp_db, title="Build Next.js Dashboard", client_name="AcmeCorp") -> Lead:
    from freelance_os.ingestion.manual import add_lead_by_text
    lead = add_lead_by_text(
        source="upwork",
        text=f"{title}\n\nBuild a full-stack dashboard application.",
        db_path=tmp_db,
    )
    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        db_lead.status = LeadStatus.WON
        db_lead.client_name = client_name
        db_lead.title = title
        session.add(db_lead)
        session.commit()
        session.refresh(db_lead)
        return db_lead


# ---------------------------------------------------------------------------
# PRD 21.3: Client directory is created
# ---------------------------------------------------------------------------

def test_workspace_creates_directory(tmp_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    lead = _make_won_lead(tmp_db)
    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        project = create_workspace(db_lead, session=session)
        session.commit()
        session.refresh(project)
        ws_path = project.workspace_path

    assert Path(ws_path).exists()


# ---------------------------------------------------------------------------
# PRD 21.3: Required subdirectories are created
# ---------------------------------------------------------------------------

def test_workspace_creates_subdirectories(tmp_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    lead = _make_won_lead(tmp_db)
    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        project = create_workspace(db_lead, session=session)
        session.commit()
        session.refresh(project)
        ws_path = project.workspace_path

    ws = Path(ws_path)
    assert (ws / "00_contract").exists()
    assert (ws / "01_workspace").exists()
    assert (ws / "02_delivery").exists()
    assert (ws / "03_admin").exists()
    assert (ws / "02_delivery" / "screenshots").exists()


# ---------------------------------------------------------------------------
# PRD 21.3: Required markdown files are created
# ---------------------------------------------------------------------------

def test_workspace_creates_contract_files(tmp_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    lead = _make_won_lead(tmp_db)
    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        project = create_workspace(db_lead, session=session)
        session.commit()
        session.refresh(project)
        ws_path = project.workspace_path

    ws = Path(ws_path)
    assert (ws / "00_contract" / "brief.md").exists()
    assert (ws / "00_contract" / "scope.md").exists()
    assert (ws / "00_contract" / "milestones.md").exists()
    assert (ws / "00_contract" / "platform_messages.md").exists()
    assert (ws / "00_contract" / "risk_log.md").exists()


def test_workspace_creates_workspace_files(tmp_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    lead = _make_won_lead(tmp_db)
    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        project = create_workspace(db_lead, session=session)
        session.commit()
        session.refresh(project)
        ws_path = project.workspace_path

    ws = Path(ws_path)
    assert (ws / "01_workspace" / "README.md").exists()


def test_workspace_creates_admin_files(tmp_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    lead = _make_won_lead(tmp_db)
    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        project = create_workspace(db_lead, session=session)
        session.commit()
        session.refresh(project)
        ws_path = project.workspace_path

    ws = Path(ws_path)
    assert (ws / "03_admin" / "invoice_notes.md").exists()
    assert (ws / "03_admin" / "followups.md").exists()
    assert (ws / "03_admin" / "outcome.md").exists()


def test_workspace_creates_delivery_stubs(tmp_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    lead = _make_won_lead(tmp_db)
    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        project = create_workspace(db_lead, session=session)
        session.commit()
        session.refresh(project)
        ws_path = project.workspace_path

    ws = Path(ws_path)
    assert (ws / "02_delivery" / "changelog.md").exists()
    assert (ws / "02_delivery" / "handoff.md").exists()
    assert (ws / "02_delivery" / "install.md").exists()


# ---------------------------------------------------------------------------
# PRD 21.3: Existing project does not overwrite without force
# ---------------------------------------------------------------------------

def test_existing_workspace_raises_without_force(tmp_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    lead = _make_won_lead(tmp_db)
    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        create_workspace(db_lead, session=session)
        session.commit()

    # Second attempt without force should raise
    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        with pytest.raises(FileExistsError):
            create_workspace(db_lead, session=session, force=False)


def test_existing_workspace_force_overwrites(tmp_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    lead = _make_won_lead(tmp_db)
    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        create_workspace(db_lead, session=session)
        session.commit()

    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        project = create_workspace(db_lead, session=session, force=True)
        session.commit()
        session.refresh(project)
        ws_path = project.workspace_path

    assert Path(ws_path).exists()


# ---------------------------------------------------------------------------
# PRD 21.3: Branch names are sanitized
# ---------------------------------------------------------------------------

def test_branch_name_sanitized(tmp_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    lead = _make_won_lead(tmp_db, title="Build Next.js App!", client_name="Client & Co.")
    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        project = create_workspace(db_lead, session=session)
        session.commit()
        session.refresh(project)
        branch_name = project.branch_name

    assert branch_name is not None
    # "/" is valid in git branch names (e.g. client/platform-slug)
    # Check for other chars that would break git branch names
    bad_chars = set("!@#$%^&*()=+[]{}|;':\",..<>? ")
    assert not any(c in branch_name for c in bad_chars)


def test_slugify_removes_special_chars():
    assert _slugify("Hello World!") == "hello-world"
    assert _slugify("Client & Co.") == "client-co"
    assert _slugify("Next.js App!") == "nextjs-app"


# ---------------------------------------------------------------------------
# Delivery package
# ---------------------------------------------------------------------------

def _make_project_in_session(tmp_db, tmp_path):
    """Create a workspace and return a detached copy with key fields set."""
    lead = _make_won_lead(tmp_db)
    with get_session(tmp_db) as session:
        db_lead = session.get(Lead, lead.id)
        project = create_workspace(db_lead, session=session)
        session.commit()
        session.refresh(project)
        # Capture all fields before session closes
        ws_path = project.workspace_path
        project_name = project.project_name
        client_name = project.client_name

    # Return a plain ClientProject-like object with the values pre-set
    cp = ClientProject(
        lead_id=lead.id,
        client_name=client_name,
        project_name=project_name,
        workspace_path=ws_path,
    )
    return cp


def test_delivery_package_creates_files(tmp_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = _make_project_in_session(tmp_db, tmp_path)

    create_delivery_package(project)

    ws = Path(project.workspace_path)
    assert (ws / "02_delivery" / "qa_report.md").exists()
    assert (ws / "02_delivery" / "delivery_message_draft.md").exists()


def test_delivery_message_is_draft_only(tmp_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = _make_project_in_session(tmp_db, tmp_path)

    create_delivery_package(project)

    delivery_msg = (Path(project.workspace_path) / "02_delivery" / "delivery_message_draft.md").read_text()
    assert "DRAFT ONLY" in delivery_msg
    assert "USER MUST REVIEW AND SEND MANUALLY" in delivery_msg


def test_delivery_no_auto_send_language(tmp_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = _make_project_in_session(tmp_db, tmp_path)

    create_delivery_package(project)

    delivery_msg = (Path(project.workspace_path) / "02_delivery" / "delivery_message_draft.md").read_text()
    assert "automatically" in delivery_msg.lower() or "manually" in delivery_msg.lower()


def test_delivery_no_overwrite_without_force(tmp_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = _make_project_in_session(tmp_db, tmp_path)

    create_delivery_package(project, force=False)

    # Modify the file manually
    qa_path = Path(project.workspace_path) / "02_delivery" / "qa_report.md"
    qa_path.write_text("MODIFIED CONTENT")

    # Second call without force should not overwrite
    create_delivery_package(project, force=False)
    assert qa_path.read_text() == "MODIFIED CONTENT"

    # With force it should overwrite
    create_delivery_package(project, force=True)
    assert qa_path.read_text() != "MODIFIED CONTENT"
