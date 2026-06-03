"""Phase 1: Tests for config loading and safety enforcement."""

import pytest
import tempfile
from pathlib import Path
from freelance_os.config import load_config, ConfigError, SAFE_DEFAULTS


def test_load_config_no_file_uses_safe_defaults():
    """Loading config with no file should return safe defaults."""
    cfg = load_config(None)
    assert cfg["safety"]["allow_auto_submit"] is False
    assert cfg["safety"]["allow_browser_automation"] is False
    assert cfg["safety"]["allow_auto_message"] is False
    assert cfg["safety"]["allow_scraping"] is False
    assert cfg["safety"]["require_human_approval"] is True


def test_safe_defaults_are_all_false():
    """Verify safe defaults have all automation flags False."""
    safety = SAFE_DEFAULTS["safety"]
    assert safety["allow_auto_submit"] is False
    assert safety["allow_browser_automation"] is False
    assert safety["allow_auto_message"] is False
    assert safety["allow_scraping"] is False
    assert safety["require_human_approval"] is True


def _write_toml(tmp_path: Path, content: str) -> str:
    cfg_path = tmp_path / "settings.toml"
    cfg_path.write_text(content, encoding="utf-8")
    return str(cfg_path)


def test_allow_auto_submit_true_raises(tmp_path):
    """allow_auto_submit=true must raise ConfigError."""
    path = _write_toml(tmp_path, "[safety]\nallow_auto_submit = true\n")
    with pytest.raises(ConfigError, match="allow_auto_submit"):
        load_config(path)


def test_allow_browser_automation_true_raises(tmp_path):
    """allow_browser_automation=true must raise ConfigError."""
    path = _write_toml(tmp_path, "[safety]\nallow_browser_automation = true\n")
    with pytest.raises(ConfigError, match="allow_browser_automation"):
        load_config(path)


def test_allow_auto_message_true_raises(tmp_path):
    """allow_auto_message=true must raise ConfigError."""
    path = _write_toml(tmp_path, "[safety]\nallow_auto_message = true\n")
    with pytest.raises(ConfigError, match="allow_auto_message"):
        load_config(path)


def test_allow_scraping_true_raises(tmp_path):
    """allow_scraping=true must raise ConfigError."""
    path = _write_toml(tmp_path, "[safety]\nallow_scraping = true\n")
    with pytest.raises(ConfigError, match="allow_scraping"):
        load_config(path)


def test_valid_config_loads_without_error(tmp_path):
    """A valid safe config file loads without error."""
    content = """
[user]
name = "Test User"
target_hourly_rate = 80

[safety]
allow_auto_submit = false
allow_browser_automation = false
allow_auto_message = false
allow_scraping = false
require_human_approval = true
"""
    path = _write_toml(tmp_path, content)
    cfg = load_config(path)
    assert cfg["user"]["name"] == "Test User"
    assert cfg["user"]["target_hourly_rate"] == 80


def test_config_merges_with_defaults(tmp_path):
    """User config should be merged with defaults, not replace them."""
    content = "[user]\nname = \"Merged User\"\n"
    path = _write_toml(tmp_path, content)
    cfg = load_config(path)
    assert cfg["user"]["name"] == "Merged User"
    # Defaults should still be present
    assert "database_path" in cfg["paths"]
    assert cfg["safety"]["require_human_approval"] is True


def test_nonexistent_config_path_uses_defaults():
    """Passing a nonexistent config path uses defaults (no error)."""
    cfg = load_config("/nonexistent/path/settings.toml")
    assert cfg["safety"]["allow_auto_submit"] is False
