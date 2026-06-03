"""Phase 5: Client workspace creation tests per PRD section 21.3."""

import pytest
from pathlib import Path
from sqlmodel import Session, create_engine, SQLModel


@pytest.fixture
def workspace_cfg(tmp_path):
    return {
        "paths": {
            "database_path": str(tmp_path / "test.sqlite"),
            "client_work_dir": str(tmp_path / "client-work"),
            "portfolio_file": str(tmp_path / "portfolio.yaml"),
        },
        "safety": {
            "allow_browser_automation": False,
            "allow_auto_submit": False,
            "allow_auto_message": False,
            "allow_scraping": False,
            "require_human_approval": True,
        },
        "scoring": {"target_hourly_rate": 75, "minimum_project_value": 300},
    }


@pytest.fixture
def db_engine(workspace_cfg):
    import freelance_os.models  # noqa: F401
    engine = create_engine(f"sqlite:///{workspace_cfg['paths']['database_path']}")
    SQLModel.metadata.create_all(engine)
    return engine


def create_won_lead(engine, cfg: dict):
    """Insert a WON lead into the DB and return it."""
    from freelance_os.models import Lead, LeadStatus
    from freelance_os.db import get_engine

    with Session(engine) as session:
        lead = Lead(
            source="upwork",
            title="Build FastAPI Dashboard",
            description="We need a FastAPI backend with dashboard.",
            client_name="ACME Corp",
            status=LeadStatus.WON,
            budget_min=1500.0,
            budget_max=3000.0,
        )
        session.add(lead)
        session.commit()
        session.refresh(lead)
        return lead


def test_workspace_directory_created(workspace_cfg, db_engine, monkeypatch):
    """init_workspace creates the client directory."""
    from freelance_os.client.workspace import init_workspace
    from freelance_os.db import get_engine

    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: db_engine)
    monkeypatch.setattr("freelance_os.ingestion.manual.get_engine", lambda path: db_engine)

    lead = create_won_lead(db_engine, workspace_cfg)
    project = init_workspace(lead_id=lead.id, cfg=workspace_cfg)

    workspace = Path(project.workspace_path)
    assert workspace.exists()


def test_workspace_required_subdirs_created(workspace_cfg, db_engine, monkeypatch):
    """Workspace must contain all required subdirectories."""
    from freelance_os.client.workspace import init_workspace

    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: db_engine)

    lead = create_won_lead(db_engine, workspace_cfg)
    project = init_workspace(lead_id=lead.id, cfg=workspace_cfg)
    workspace = Path(project.workspace_path)

    assert (workspace / "00_contract").is_dir()
    assert (workspace / "01_workspace").is_dir()
    assert (workspace / "02_delivery").is_dir()
    assert (workspace / "03_admin").is_dir()


def test_workspace_required_files_created(workspace_cfg, db_engine, monkeypatch):
    """Workspace must contain all required markdown files."""
    from freelance_os.client.workspace import init_workspace

    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: db_engine)

    lead = create_won_lead(db_engine, workspace_cfg)
    project = init_workspace(lead_id=lead.id, cfg=workspace_cfg)
    workspace = Path(project.workspace_path)

    assert (workspace / "00_contract" / "brief.md").exists()
    assert (workspace / "00_contract" / "scope.md").exists()
    assert (workspace / "00_contract" / "milestones.md").exists()
    assert (workspace / "00_contract" / "platform_messages.md").exists()
    assert (workspace / "00_contract" / "risk_log.md").exists()
    assert (workspace / "01_workspace" / "README.md").exists()
    assert (workspace / "02_delivery" / "changelog.md").exists()
    assert (workspace / "02_delivery" / "handoff.md").exists()
    assert (workspace / "02_delivery" / "install.md").exists()
    assert (workspace / "03_admin" / "invoice_notes.md").exists()
    assert (workspace / "03_admin" / "followups.md").exists()
    assert (workspace / "03_admin" / "outcome.md").exists()


def test_workspace_no_overwrite_without_force(workspace_cfg, db_engine, monkeypatch):
    """Second init without --force should raise FileExistsError."""
    from freelance_os.client.workspace import init_workspace

    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: db_engine)

    lead = create_won_lead(db_engine, workspace_cfg)
    init_workspace(lead_id=lead.id, cfg=workspace_cfg)

    with pytest.raises(FileExistsError):
        init_workspace(lead_id=lead.id, cfg=workspace_cfg, force=False)


def test_workspace_force_overwrites(workspace_cfg, db_engine, monkeypatch):
    """Second init with --force should not raise."""
    from freelance_os.client.workspace import init_workspace

    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: db_engine)

    lead = create_won_lead(db_engine, workspace_cfg)
    init_workspace(lead_id=lead.id, cfg=workspace_cfg)
    project2 = init_workspace(lead_id=lead.id, cfg=workspace_cfg, force=True)
    assert project2 is not None


def test_non_won_lead_raises_error(workspace_cfg, db_engine, monkeypatch):
    """init_workspace on a non-WON lead should raise ValueError."""
    from freelance_os.client.workspace import init_workspace
    from freelance_os.models import Lead, LeadStatus

    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: db_engine)

    with Session(db_engine) as session:
        lead = Lead(source="test", title="Test", status=LeadStatus.SCORED)
        session.add(lead)
        session.commit()
        session.refresh(lead)
        lead_id = lead.id

    with pytest.raises(ValueError, match="not WON"):
        init_workspace(lead_id=lead_id, cfg=workspace_cfg)


def test_delivery_package_creates_files(workspace_cfg, db_engine, monkeypatch, tmp_path):
    """generate_delivery_package should create all delivery files."""
    from freelance_os.client.delivery import generate_delivery_package
    from freelance_os.client.workspace import init_workspace

    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: db_engine)

    lead = create_won_lead(db_engine, workspace_cfg)
    project = init_workspace(lead_id=lead.id, cfg=workspace_cfg)

    # Get project folder name from workspace path
    project_folder = Path(project.workspace_path).name
    delivery_dir = generate_delivery_package(project_name=project_folder, cfg=workspace_cfg)

    delivery_path = Path(delivery_dir)
    assert (delivery_path / "changelog.md").exists()
    assert (delivery_path / "handoff.md").exists()
    assert (delivery_path / "install.md").exists()
    assert (delivery_path / "qa_report.md").exists()
    assert (delivery_path / "delivery_message_draft.md").exists()


def test_delivery_message_draft_header(workspace_cfg, db_engine, monkeypatch):
    """Delivery message must be marked DRAFT ONLY."""
    from freelance_os.client.delivery import generate_delivery_package
    from freelance_os.client.workspace import init_workspace

    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: db_engine)

    lead = create_won_lead(db_engine, workspace_cfg)
    project = init_workspace(lead_id=lead.id, cfg=workspace_cfg)
    project_folder = Path(project.workspace_path).name
    delivery_dir = generate_delivery_package(project_name=project_folder, cfg=workspace_cfg)

    draft_file = Path(delivery_dir) / "delivery_message_draft.md"
    content = draft_file.read_text(encoding="utf-8")
    assert "DRAFT ONLY" in content
    assert "MANUALLY" in content


def test_branch_name_sanitized():
    """Branch names should be sanitized per PRD 15.3."""
    from freelance_os.execution.worktree import _branch_name

    branch = _branch_name("upwork", "ACME Corp!", "Fix Auth Bug #42")
    assert " " not in branch
    assert "#" not in branch
    assert branch.startswith("client/")
    assert "upwork" in branch
