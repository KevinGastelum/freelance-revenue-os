"""Git worktree helpers — dry-run only, per PRD section 15.3."""

import re
from typing import List


def _branch_name(platform: str, client: str, task: str) -> str:
    """Generate branch name per PRD 15.3 convention."""
    def slug(s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r"[^\w\s-]", "", s)
        s = re.sub(r"[\s_]+", "-", s)
        return re.sub(r"-+", "-", s)[:20]

    return f"client/{slug(platform)}-{slug(client)}-{slug(task)}"


def generate_worktree_commands(
    project_name: str,
    repo_url: str,
    cfg: dict,
    platform: str = "platform",
    client: str = "",
) -> List[str]:
    """Return a list of git commands to set up a worktree (dry-run — not executed)."""
    import re as _re

    client_slug = client or _re.sub(r"[^\w-]", "-", project_name.split("-")[0])[:20]
    task_slug = project_name[:20]
    branch = _branch_name(platform, client_slug, task_slug)
    base_dir = cfg["paths"].get("client_work_dir", "./client-work")
    worktree_path = f"{base_dir}/{project_name}/01_workspace"

    commands = [
        f"# Clone repository (if not already cloned)",
        f"git clone {repo_url} {base_dir}/{project_name}-repo",
        f"",
        f"# Create and checkout worktree branch",
        f"cd {base_dir}/{project_name}-repo",
        f"git worktree add -b {branch} {worktree_path} main",
        f"",
        f"# Branch name: {branch}",
        f"# Worktree path: {worktree_path}",
        f"",
        f"# NOTE: Review before running. Do not push without human approval.",
    ]
    return commands
