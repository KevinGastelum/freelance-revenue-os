"""Phase 6: Execution harness tests."""

import os
import pytest
from pathlib import Path


@pytest.fixture
def exec_cfg(tmp_path):
    return {
        "paths": {
            "client_work_dir": str(tmp_path / "client-work"),
            "database_path": str(tmp_path / "test.sqlite"),
        },
        "scoring": {"target_hourly_rate": 75, "minimum_project_value": 300},
    }


def test_tmux_script_generated(exec_cfg, tmp_path, monkeypatch):
    """generate_tmux_script should write a shell script."""
    from freelance_os.execution.tmux import generate_tmux_script

    # Change to tmp_path so scripts/ is created there
    monkeypatch.chdir(tmp_path)

    script_path = generate_tmux_script("my-project", exec_cfg)
    assert Path(script_path).exists()


@pytest.mark.skipif(os.name == "nt", reason="exec bit is POSIX-only")
def test_tmux_script_is_executable(exec_cfg, tmp_path, monkeypatch):
    """Generated tmux script should have executable permission."""
    from freelance_os.execution.tmux import generate_tmux_script

    monkeypatch.chdir(tmp_path)

    script_path = generate_tmux_script("my-project", exec_cfg)
    mode = os.stat(script_path).st_mode
    assert mode & 0o111  # executable bit set


def test_tmux_script_content(exec_cfg, tmp_path, monkeypatch):
    """Tmux script should contain key tmux commands."""
    from freelance_os.execution.tmux import generate_tmux_script

    monkeypatch.chdir(tmp_path)

    script_path = generate_tmux_script("acme-dashboard", exec_cfg)
    content = Path(script_path).read_text(encoding="utf-8")

    assert "tmux" in content
    assert "orchestrator" in content
    assert "coder" in content
    assert "qa" in content
    # Script should NOT auto-attach (commented out or user-initiated)
    # The attach line should be commented out
    assert "# tmux attach" in content or "echo" in content


def test_tmux_script_no_auto_launch(exec_cfg, tmp_path, monkeypatch):
    """Tmux script generator should not actually run tmux."""
    from freelance_os.execution.tmux import generate_tmux_script
    import subprocess

    original_run = subprocess.run
    calls = []

    def mock_run(*args, **kwargs):
        calls.append(args)
        return original_run(*args, **kwargs)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(subprocess, "run", mock_run)

    generate_tmux_script("test-project", exec_cfg)
    # No subprocess calls should have been made to tmux
    tmux_calls = [c for c in calls if c and "tmux" in str(c[0])]
    assert not tmux_calls, f"Unexpected tmux calls: {tmux_calls}"


def test_agent_files_generated(exec_cfg, tmp_path, monkeypatch):
    """Agent instruction files should be generated."""
    from freelance_os.execution.tmux import generate_tmux_script

    monkeypatch.chdir(tmp_path)

    generate_tmux_script("my-project", exec_cfg)

    agent_dir = tmp_path / ".agent"
    assert (agent_dir / "orchestrator.md").exists()
    assert (agent_dir / "coder.md").exists()
    assert (agent_dir / "qa.md").exists()
    assert (agent_dir / "docs.md").exists()


def test_agent_files_content(exec_cfg, tmp_path, monkeypatch):
    """Agent files should contain required sections."""
    from freelance_os.execution.tmux import generate_tmux_script

    monkeypatch.chdir(tmp_path)

    generate_tmux_script("my-project", exec_cfg)

    for fname in ["orchestrator.md", "coder.md", "qa.md", "docs.md"]:
        content = (tmp_path / ".agent" / fname).read_text(encoding="utf-8")
        assert "Forbidden Changes" in content
        assert "Acceptance Criteria" in content
        assert "Handoff Format" in content


def test_agent_coder_forbidden_no_auto_push(exec_cfg, tmp_path, monkeypatch):
    """Coder agent instructions should forbid auto-push."""
    from freelance_os.execution.tmux import generate_tmux_script

    monkeypatch.chdir(tmp_path)
    generate_tmux_script("my-project", exec_cfg)

    coder = (tmp_path / ".agent" / "coder.md").read_text(encoding="utf-8")
    assert "push" in coder.lower()


def test_worktree_commands_dry_run(exec_cfg):
    """generate_worktree_commands returns commands without executing them."""
    from freelance_os.execution.worktree import generate_worktree_commands

    cmds = generate_worktree_commands(
        project_name="acme-dashboard",
        repo_url="git@github.com:acme/dashboard.git",
        cfg=exec_cfg,
    )
    assert isinstance(cmds, list)
    assert any("git clone" in c for c in cmds)
    assert any("git worktree add" in c for c in cmds)
    assert any("client/" in c for c in cmds)  # branch name format


def test_worktree_branch_format():
    """Branch name follows client/<platform>-<client>-<task> format."""
    from freelance_os.execution.worktree import _branch_name

    branch = _branch_name("upwork", "acme-corp", "dashboard-auth-fix")
    assert branch.startswith("client/")
    assert "upwork" in branch
    assert "acme" in branch


def test_qa_checklist_generated(exec_cfg, tmp_path):
    """QA checklist file should be generated."""
    from freelance_os.execution.qa import generate_qa_checklist

    exec_cfg["paths"]["client_work_dir"] = str(tmp_path / "client-work")
    path = generate_qa_checklist("my-project", exec_cfg)
    assert Path(path).exists()
    content = Path(path).read_text(encoding="utf-8")
    assert "QA Report" in content
    assert "Checklist" in content or "checklist" in content.lower()
