"""Phase 1/PRD 21.4: Safety enforcement tests."""

import pytest
from freelance_os.config import load_config, ConfigError


def test_no_auto_submit_in_code():
    """Verify no auto-submit functionality exists in the codebase."""
    from pathlib import Path

    src_root = Path(__file__).resolve().parents[1] / "src" / "freelance_os"
    hits = []
    for py_file in src_root.rglob("*.py"):
        if "config.py" in py_file.name:
            continue
        if "auto_submit" in py_file.read_text(encoding="utf-8"):
            hits.append(str(py_file))
    assert not hits, f"auto_submit found in non-config files: {hits}"


def test_no_browser_automation_in_code():
    """Verify no browser automation code exists."""
    from pathlib import Path

    src_root = Path(__file__).resolve().parents[1] / "src" / "freelance_os"
    for keyword in ["selenium", "playwright", "puppeteer", "webdriver"]:
        hits = [
            str(p) for p in src_root.rglob("*.py")
            if keyword in p.read_text(encoding="utf-8")
        ]
        assert not hits, f"Browser automation keyword '{keyword}' found in: {hits}"


def test_no_proxy_or_captcha_in_code():
    """Verify no proxy/CAPTCHA bypass code exists."""
    from pathlib import Path

    src_root = Path(__file__).resolve().parents[1] / "src" / "freelance_os"
    for keyword in ["captcha", "proxy_rotate", "2captcha", "anticaptcha"]:
        hits = [
            str(p) for p in src_root.rglob("*.py")
            if keyword in p.read_text(encoding="utf-8").lower()
        ]
        assert not hits, f"Prohibited keyword '{keyword}' found in: {hits}"


def test_delivery_message_always_marked_draft():
    """delivery_message_draft.md content must include DRAFT ONLY header."""
    from freelance_os.client.delivery import _delivery_message_draft
    content = _delivery_message_draft("test-project")
    assert "DRAFT ONLY" in content
    assert "MANUALLY" in content
    assert "automatically" not in content.lower() or "do not" in content.lower()


def test_config_defaults_are_safe():
    """Default config must have all automation flags false."""
    from freelance_os.config import SAFE_DEFAULTS
    safety = SAFE_DEFAULTS["safety"]
    assert safety["allow_auto_submit"] is False
    assert safety["allow_browser_automation"] is False
    assert safety["allow_auto_message"] is False
    assert safety["allow_scraping"] is False
    assert safety["require_human_approval"] is True


def test_all_four_unsafe_flags_enforced():
    """All four unsafe flags must each independently trigger ConfigError."""
    import tempfile
    from pathlib import Path

    flags = [
        "allow_auto_submit",
        "allow_browser_automation",
        "allow_auto_message",
        "allow_scraping",
    ]
    for flag in flags:
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / "settings.toml"
            cfg_path.write_text(f"[safety]\n{flag} = true\n", encoding="utf-8")
            with pytest.raises(ConfigError):
                load_config(str(cfg_path))


def test_worktree_generate_is_dry_run():
    """generate_worktree_commands must not execute any commands."""
    from freelance_os.execution.worktree import generate_worktree_commands

    cfg = {"paths": {"client_work_dir": "/tmp/client-work"}}
    cmds = generate_worktree_commands(
        project_name="test-project",
        repo_url="git@github.com:test/repo.git",
        cfg=cfg,
    )
    # Should return a list of strings, not execute anything
    assert isinstance(cmds, list)
    assert all(isinstance(c, str) for c in cmds)
    assert any("git" in c for c in cmds)
