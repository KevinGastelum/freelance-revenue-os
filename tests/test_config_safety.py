import pytest

from freelance_os.config import SafetyConfigError, load_config


def test_safe_defaults_when_no_file(tmp_path):
    """Loading with a non-existent path must succeed and return safe defaults."""
    cfg = load_config(config_path=tmp_path / "nonexistent.toml")
    safety = cfg["safety"]
    assert safety["allow_auto_submit"] is False
    assert safety["allow_browser_automation"] is False
    assert safety["allow_auto_message"] is False
    assert safety["allow_scraping"] is False
    assert safety["require_human_approval"] is True


def test_safe_example_config_loads(tmp_path):
    """The settings.example.toml shipped with the project must load without error."""
    from pathlib import Path
    example = Path("config/settings.example.toml")
    if not example.exists():
        pytest.skip("settings.example.toml not present in CWD")
    cfg = load_config(config_path=example)
    assert cfg["safety"]["allow_auto_submit"] is False


def test_allow_auto_submit_true_is_rejected(tmp_path):
    bad_config = tmp_path / "bad.toml"
    bad_config.write_text("[safety]\nallow_auto_submit = true\n")
    with pytest.raises(SafetyConfigError, match="allow_auto_submit"):
        load_config(config_path=bad_config)


def test_allow_browser_automation_true_is_rejected(tmp_path):
    bad_config = tmp_path / "bad.toml"
    bad_config.write_text("[safety]\nallow_browser_automation = true\n")
    with pytest.raises(SafetyConfigError, match="allow_browser_automation"):
        load_config(config_path=bad_config)


def test_allow_auto_message_true_is_rejected(tmp_path):
    bad_config = tmp_path / "bad.toml"
    bad_config.write_text("[safety]\nallow_auto_message = true\n")
    with pytest.raises(SafetyConfigError, match="allow_auto_message"):
        load_config(config_path=bad_config)


def test_allow_scraping_true_is_rejected(tmp_path):
    bad_config = tmp_path / "bad.toml"
    bad_config.write_text("[safety]\nallow_scraping = true\n")
    with pytest.raises(SafetyConfigError, match="allow_scraping"):
        load_config(config_path=bad_config)


def test_partial_config_merges_safe_defaults(tmp_path):
    """A config that only sets [user] must still have safe safety defaults."""
    partial = tmp_path / "partial.toml"
    partial.write_text('[user]\nname = "Test"\n')
    cfg = load_config(config_path=partial)
    assert cfg["safety"]["allow_auto_submit"] is False
    assert cfg["user"]["name"] == "Test"
    assert cfg["user"]["target_hourly_rate"] == 75


def test_require_human_approval_defaults_true(tmp_path):
    cfg = load_config(config_path=tmp_path / "nonexistent.toml")
    assert cfg["safety"]["require_human_approval"] is True
