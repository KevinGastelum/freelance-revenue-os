"""Phase 6 tests: execution harness — tmux scripts, worktree dry-run, agent files."""

import pytest
from pathlib import Path

from freelance_os.execution.tmux import generate_tmux_script
from freelance_os.execution.worktree import _sanitize_branch
from freelance_os.execution.qa import generate_qa_checklist
from freelance_os.execution.agent_files import generate_agent_files
from freelance_os.models import ClientProject, ClientProjectStatus


def _make_project(workspace_path: Path) -> ClientProject:
    return ClientProject(
        client_name="AcmeCorp",
        project_name="dashboard-rebuild",
        platform="upwork",
        status=ClientProjectStatus.ACTIVE,
        workspace_path=str(workspace_path),
        branch_name="client/upwork-acmecorp-dashboard-rebuild",
    )


# ---------------------------------------------------------------------------
# Tmux script generation (PRD 15.1)
# ---------------------------------------------------------------------------

def test_tmux_script_is_created(tmp_path):
    script_path = generate_tmux_script("myproject", scripts_dir=tmp_path / "scripts")
    assert script_path.exists()


def test_tmux_script_is_executable(tmp_path):
    script_path = generate_tmux_script("myproject", scripts_dir=tmp_path / "scripts")
    assert script_path.stat().st_mode & 0o111  # executable bit set


def test_tmux_script_contains_windows(tmp_path):
    script_path = generate_tmux_script("myproject", scripts_dir=tmp_path / "scripts")
    content = script_path.read_text()
    # Must define the 5 windows per PRD 15.1
    assert "orchestrator" in content
    assert "coder" in content
    assert "qa" in content
    assert "docs-delivery" in content
    assert "git" in content or "logs" in content


def test_tmux_script_uses_project_name(tmp_path):
    script_path = generate_tmux_script("acmecorp-dashboard", scripts_dir=tmp_path / "scripts")
    content = script_path.read_text()
    assert "acmecorp-dashboard" in content


def test_tmux_script_does_not_auto_launch(tmp_path):
    """The script is generated but never auto-executed."""
    script_path = generate_tmux_script("myproject", scripts_dir=tmp_path / "scripts")
    # The function returns the path, not the exit code of tmux
    assert isinstance(script_path, Path)
    # Content is a shell script to be run manually
    content = script_path.read_text()
    assert content.startswith("#!/")


# ---------------------------------------------------------------------------
# Worktree dry-run (PRD 15.3)
# ---------------------------------------------------------------------------

def test_worktree_branch_sanitize():
    branch = _sanitize_branch("My Project Name!")
    assert " " not in branch
    assert "!" not in branch


def test_worktree_branch_format():
    branch = _sanitize_branch("client/upwork-acme-dashboard-auth-fix")
    assert branch == "client/upwork-acme-dashboard-auth-fix"


def test_worktree_branch_lowercases():
    branch = _sanitize_branch("Client/Upwork-ACME")
    assert branch == branch.lower()


# ---------------------------------------------------------------------------
# QA checklist generation
# ---------------------------------------------------------------------------

def test_qa_checklist_created(tmp_path):
    workspace = tmp_path / "myproject"
    workspace.mkdir()
    (workspace / "01_workspace").mkdir()
    checklist_path = generate_qa_checklist(workspace)
    assert checklist_path.exists()


def test_qa_checklist_has_checkboxes(tmp_path):
    workspace = tmp_path / "myproject"
    workspace.mkdir()
    (workspace / "01_workspace").mkdir()
    checklist_path = generate_qa_checklist(workspace)
    content = checklist_path.read_text()
    assert "- [ ]" in content


# ---------------------------------------------------------------------------
# Agent instruction files (PRD 15.2)
# ---------------------------------------------------------------------------

def test_agent_files_generated(tmp_path):
    workspace = tmp_path / "client-project"
    workspace.mkdir()
    project = _make_project(workspace)
    files = generate_agent_files(project, workspace)

    assert (workspace / ".agent" / "orchestrator.md").exists()
    assert (workspace / ".agent" / "coder.md").exists()
    assert (workspace / ".agent" / "qa.md").exists()
    assert (workspace / ".agent" / "docs.md").exists()


def test_agent_orchestrator_contains_scope_ref(tmp_path):
    workspace = tmp_path / "client-project"
    workspace.mkdir()
    project = _make_project(workspace)
    generate_agent_files(project, workspace)
    content = (workspace / ".agent" / "orchestrator.md").read_text()
    assert "scope.md" in content


def test_agent_orchestrator_forbids_auto_submit(tmp_path):
    workspace = tmp_path / "client-project"
    workspace.mkdir()
    project = _make_project(workspace)
    generate_agent_files(project, workspace)
    content = (workspace / ".agent" / "orchestrator.md").read_text()
    assert "NOT" in content or "not" in content.lower()
    assert "submit" in content.lower() or "manually" in content.lower()


def test_agent_docs_marks_delivery_as_draft(tmp_path):
    workspace = tmp_path / "client-project"
    workspace.mkdir()
    project = _make_project(workspace)
    generate_agent_files(project, workspace)
    content = (workspace / ".agent" / "docs.md").read_text()
    assert "DRAFT ONLY" in content or "manually" in content.lower()


def test_agent_coder_has_branch_name(tmp_path):
    workspace = tmp_path / "client-project"
    workspace.mkdir()
    project = _make_project(workspace)
    generate_agent_files(project, workspace)
    content = (workspace / ".agent" / "coder.md").read_text()
    assert "client/upwork-acmecorp-dashboard-rebuild" in content


# ---------------------------------------------------------------------------
# Safety: execution harness never auto-launches
# ---------------------------------------------------------------------------

def test_tmux_generator_returns_path_not_result(tmp_path):
    """Verify generate_tmux_script returns Path (script), not a process result."""
    result = generate_tmux_script("test-project", scripts_dir=tmp_path / "scripts")
    assert isinstance(result, Path)


def test_worktree_show_is_dry_run(tmp_path, capsys):
    from freelance_os.execution.worktree import show_worktree_commands
    # Should not raise or execute git commands
    show_worktree_commands("myproject", "https://github.com/example/repo.git")
    # Function returns None — it prints to console (dry-run)
    # No git commands are actually executed
