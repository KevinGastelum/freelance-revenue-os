"""Phase 5: Client workspace integration tests."""

import pytest
from pathlib import Path
from sqlmodel import Session, create_engine, SQLModel


@pytest.fixture
def ws_engine_cfg(tmp_path):
    import freelance_os.models  # noqa: F401
    engine = create_engine(f"sqlite:///{tmp_path}/test.sqlite")
    SQLModel.metadata.create_all(engine)
    cfg = {
        "paths": {
            "database_path": str(tmp_path / "test.sqlite"),
            "client_work_dir": str(tmp_path / "client-work"),
            "portfolio_file": str(tmp_path / "portfolio.yaml"),
        },
        "scoring": {"target_hourly_rate": 75, "minimum_project_value": 300},
    }
    return engine, cfg


def _won_lead(engine):
    from freelance_os.models import Lead, LeadStatus
    with Session(engine) as session:
        lead = Lead(
            source="upwork",
            title="Python API Build",
            client_name="Acme Corp",
            description="Build a Python API.",
            status=LeadStatus.WON,
            budget_min=1000.0,
            budget_max=2000.0,
        )
        session.add(lead)
        session.commit()
        session.refresh(lead)
        return lead


def test_workspace_scope_md_content(ws_engine_cfg, monkeypatch):
    """scope.md should contain in-scope section and acceptance criteria."""
    from freelance_os.client.workspace import init_workspace
    engine, cfg = ws_engine_cfg
    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: engine)

    lead = _won_lead(engine)
    project = init_workspace(lead_id=lead.id, cfg=cfg)
    scope_md = (Path(project.workspace_path) / "00_contract" / "scope.md").read_text(encoding="utf-8")

    assert "In Scope" in scope_md
    assert "Out of Scope" in scope_md
    assert "Acceptance Criteria" in scope_md


def test_workspace_milestones_md_content(ws_engine_cfg, monkeypatch):
    """milestones.md should contain milestone table."""
    from freelance_os.client.workspace import init_workspace
    engine, cfg = ws_engine_cfg
    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: engine)

    lead = _won_lead(engine)
    project = init_workspace(lead_id=lead.id, cfg=cfg)
    ms_md = (Path(project.workspace_path) / "00_contract" / "milestones.md").read_text(encoding="utf-8")

    assert "Milestone" in ms_md
    assert "Kickoff" in ms_md
    assert "milestone payment" in ms_md.lower() or "no milestone" in ms_md.lower()


def test_workspace_readme_contains_project_info(ws_engine_cfg, monkeypatch):
    """README.md should contain client and project info."""
    from freelance_os.client.workspace import init_workspace
    engine, cfg = ws_engine_cfg
    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: engine)

    lead = _won_lead(engine)
    project = init_workspace(lead_id=lead.id, cfg=cfg)
    readme = (Path(project.workspace_path) / "01_workspace" / "README.md").read_text(encoding="utf-8")

    assert "Acme Corp" in readme or "Client" in readme


def test_workspace_all_files_utf8(ws_engine_cfg, monkeypatch):
    """All workspace files should be readable as UTF-8."""
    from freelance_os.client.workspace import init_workspace
    engine, cfg = ws_engine_cfg
    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: engine)

    lead = _won_lead(engine)
    project = init_workspace(lead_id=lead.id, cfg=cfg)
    workspace = Path(project.workspace_path)

    for md_file in workspace.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        assert isinstance(content, str)


def test_client_project_persisted_in_db(ws_engine_cfg, monkeypatch):
    """ClientProject record should be saved in DB after init_workspace."""
    from freelance_os.client.workspace import init_workspace
    from freelance_os.models import ClientProject
    from sqlmodel import select

    engine, cfg = ws_engine_cfg
    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: engine)

    lead = _won_lead(engine)
    project = init_workspace(lead_id=lead.id, cfg=cfg)

    with Session(engine) as session:
        found = session.get(ClientProject, project.id)
        assert found is not None
        assert found.client_name == "Acme Corp"
        assert found.lead_id == lead.id


def test_delivery_package_no_auto_send_language(ws_engine_cfg, monkeypatch):
    """Delivery package should not contain auto-send language."""
    from freelance_os.client.delivery import generate_delivery_package
    from freelance_os.client.workspace import init_workspace

    engine, cfg = ws_engine_cfg
    monkeypatch.setattr("freelance_os.db.get_engine", lambda path: engine)

    lead = _won_lead(engine)
    project = init_workspace(lead_id=lead.id, cfg=cfg)
    project_folder = Path(project.workspace_path).name
    delivery_dir = generate_delivery_package(project_name=project_folder, cfg=cfg)

    delivery_msg = (Path(delivery_dir) / "delivery_message_draft.md").read_text(encoding="utf-8")
    # Should NOT say "automatically sending"
    assert "automatically send" not in delivery_msg.lower()
    # MUST say DRAFT ONLY
    assert "DRAFT ONLY" in delivery_msg
