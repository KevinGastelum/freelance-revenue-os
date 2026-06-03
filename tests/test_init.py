import sqlite3

import pytest
from typer.testing import CliRunner

from freelance_os.cli import app

runner = CliRunner()


def test_init_creates_database(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "data" / "freelance_os.sqlite").exists()


def test_init_creates_expected_tables(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])

    db_path = tmp_path / "data" / "freelance_os.sqlite"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    expected = {"lead", "proposaldraft", "portfolioitem", "clientproject", "outcome"}
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"


def test_init_prints_table_count(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert "Tables" in result.output
    assert "5" in result.output


def test_init_idempotent(tmp_path, monkeypatch):
    """Re-running init must not raise an error."""
    monkeypatch.chdir(tmp_path)
    r1 = runner.invoke(app, ["init"])
    r2 = runner.invoke(app, ["init"])
    assert r1.exit_code == 0, r1.output
    assert r2.exit_code == 0, r2.output


def test_init_does_not_overwrite_existing_config(tmp_path, monkeypatch):
    """init must not overwrite an existing settings.toml unless --force."""
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    settings = config_dir / "settings.toml"
    settings.write_text("[user]\nname = 'Existing'\n")

    runner.invoke(app, ["init"])
    assert settings.read_text() == "[user]\nname = 'Existing'\n"
