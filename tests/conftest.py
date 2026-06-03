import pytest


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Each test gets its own SQLite file; the module-level engine is reset around it."""
    import freelance_os.db as db_module

    db_path = tmp_path / "test.db"
    monkeypatch.setenv("FREELANCE_OS_DB", str(db_path))
    db_module.reset_engine()
    db_module.create_all()
    yield
    db_module.reset_engine()
