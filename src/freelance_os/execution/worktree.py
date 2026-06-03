"""Git worktree helper — dry-run only, never auto-pushes."""

from __future__ import annotations

import re
from rich.console import Console

console = Console()


def _sanitize_branch(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^\w/-]", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")


def show_worktree_commands(project_name: str, repo_url: str) -> None:
    """Print (dry-run) the git commands to set up a worktree for a project."""
    branch = _sanitize_branch(f"client/project-{project_name}")
    worktree_dir = f"./client-work/{project_name}"

    console.print("[bold yellow]DRY RUN — Worktree Setup Commands[/bold yellow]")
    console.print("Review and run these commands manually:\n")
    console.print(f"  git clone {repo_url} {worktree_dir}-repo")
    console.print(f"  cd {worktree_dir}-repo")
    console.print(f"  git worktree add ../{project_name} -b {branch}")
    console.print(f"\nBranch: [cyan]{branch}[/cyan]")
    console.print("[dim]Do not push until the work is reviewed and ready.[/dim]")
