"""Shared pytest fixtures."""

import pytest
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session


@pytest.fixture
def tmp_db(tmp_path):
    """Create an in-memory (or tmp file) SQLite engine with all tables."""
    import freelance_os.models  # noqa: F401 — registers all tables

    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture
def tmp_cfg(tmp_path):
    """Return a minimal safe config pointing to tmp_path."""
    return {
        "user": {"name": "Test", "target_hourly_rate": 75, "minimum_project_value": 300},
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
        "scoring": {
            "target_hourly_rate": 75,
            "minimum_project_value": 300,
        },
    }
