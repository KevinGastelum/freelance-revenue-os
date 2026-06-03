"""Main CLI entry point for Freelance Revenue OS."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(
    name="freelance-os",
    help="Freelance Revenue OS — AI prepares, human commits.",
    no_args_is_help=True,
)
console = Console()

lead_app = typer.Typer(help="Lead management commands.")
client_app = typer.Typer(help="Client project commands.")
outcome_app = typer.Typer(help="Outcome tracking commands.")
report_app = typer.Typer(help="Reporting commands.")

app.add_typer(lead_app, name="lead")
app.add_typer(client_app, name="client")
app.add_typer(outcome_app, name="outcome")
app.add_typer(report_app, name="report")


def _get_db_path() -> Path:
    from freelance_os.config import load_settings
    try:
        settings = load_settings()
        return settings.database_path
    except Exception:
        return Path("data/freelance_os.sqlite")


@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Overwrite existing data directory."),
) -> None:
    """Initialize the local Freelance OS workspace."""
    from freelance_os.config import load_settings, UnsafeConfigError
    from freelance_os.db import init_db, reset_engine

    try:
        settings = load_settings()
    except UnsafeConfigError as e:
        console.print(f"[red]SAFETY ERROR:[/red] {e}")
        raise typer.Exit(1)

    db_path = settings.database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if db_path.exists() and not force:
        console.print(f"[yellow]Database already exists:[/yellow] {db_path}")
        console.print("Use --force to reinitialize.")
        raise typer.Exit(0)

    if db_path.exists() and force:
        db_path.unlink()
        reset_engine()

    reset_engine()
    init_db(db_path)
    console.print(f"[green]Initialized:[/green] {db_path}")
    console.print("[green]All tables created.[/green]")


# ---------------------------------------------------------------------------
# Lead commands (stubs — filled in per phase)
# ---------------------------------------------------------------------------

@lead_app.command("add-url")
def lead_add_url(
    url: str = typer.Argument(..., help="URL of the job posting."),
    description: str = typer.Option("", "--description", "-d", help="Optional job description."),
) -> None:
    """Add a lead by URL."""
    from freelance_os.ingestion.manual import add_lead_by_url
    from freelance_os.db import reset_engine
    db_path = _get_db_path()
    reset_engine()
    lead = add_lead_by_url(url, description or None, db_path=db_path)
    console.print(f"[green]Lead #{lead.id} added:[/green] {lead.title or url}")


@lead_app.command("add-text")
def lead_add_text(
    source: str = typer.Option(..., "--source", help="Source platform (e.g. upwork, fiverr)."),
    text: str = typer.Option("", "--text", help="Job description text (or omit to read stdin)."),
) -> None:
    """Add a lead from pasted text."""
    from freelance_os.ingestion.manual import add_lead_by_text
    from freelance_os.db import reset_engine
    db_path = _get_db_path()
    reset_engine()

    if not text:
        console.print("Paste the job description. Press Ctrl-D (or Ctrl-Z on Windows) when done:")
        text = sys.stdin.read().strip()

    if not text:
        console.print("[red]No text provided.[/red]")
        raise typer.Exit(1)

    lead = add_lead_by_text(source=source, text=text, db_path=db_path)
    console.print(f"[green]Lead #{lead.id} added:[/green] {lead.title or '(untitled)'}")


@lead_app.command("list")
def lead_list() -> None:
    """List all leads."""
    from freelance_os.db import reset_engine, get_session
    from freelance_os.models import Lead
    from sqlmodel import select
    from rich.table import Table

    db_path = _get_db_path()
    reset_engine()

    with get_session(db_path) as session:
        leads = session.exec(select(Lead).order_by(Lead.id)).all()

    if not leads:
        console.print("No leads found. Use [bold]freelance-os lead add-url[/bold] to add one.")
        return

    table = Table(title="Leads")
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Source")
    table.add_column("Status", style="yellow")
    table.add_column("Score")
    table.add_column("Decision")

    for lead in leads:
        table.add_row(
            str(lead.id),
            (lead.title or "(untitled)")[:50],
            lead.source,
            lead.status.value,
            str(round(lead.lead_score, 1)) if lead.lead_score is not None else "—",
            lead.decision.value if lead.decision else "—",
        )
    console.print(table)


@lead_app.command("show")
def lead_show(lead_id: int = typer.Argument(..., help="Lead ID.")) -> None:
    """Show details of a lead."""
    from freelance_os.db import reset_engine, get_session
    from freelance_os.models import Lead
    from sqlmodel import select

    db_path = _get_db_path()
    reset_engine()

    with get_session(db_path) as session:
        lead = session.get(Lead, lead_id)

    if not lead:
        console.print(f"[red]Lead #{lead_id} not found.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Lead #{lead.id}[/bold]")
    console.print(f"  Title:   {lead.title or '(none)'}")
    console.print(f"  Source:  {lead.source}")
    console.print(f"  URL:     {lead.source_url or '(none)'}")
    console.print(f"  Status:  {lead.status.value}")
    console.print(f"  Score:   {lead.lead_score}")
    console.print(f"  Risk:    {lead.risk_score}")
    console.print(f"  Decision:{lead.decision.value if lead.decision else '(none)'}")
    console.print(f"  Reasons: {', '.join(lead.get_reason_codes()) or '(none)'}")
    if lead.description:
        console.print(f"\n[dim]Description:[/dim]\n{lead.description[:500]}")


@lead_app.command("status")
def lead_status_cmd(
    lead_id: int = typer.Argument(..., help="Lead ID."),
    status: str = typer.Argument(..., help="New status value."),
) -> None:
    """Set the status of a lead."""
    from freelance_os.db import reset_engine, get_session
    from freelance_os.models import Lead, LeadStatus

    try:
        new_status = LeadStatus(status.upper())
    except ValueError:
        valid = [s.value for s in LeadStatus]
        console.print(f"[red]Invalid status '{status}'. Valid:[/red] {', '.join(valid)}")
        raise typer.Exit(1)

    db_path = _get_db_path()
    reset_engine()

    with get_session(db_path) as session:
        lead = session.get(Lead, lead_id)
        if not lead:
            console.print(f"[red]Lead #{lead_id} not found.[/red]")
            raise typer.Exit(1)
        lead.status = new_status
        session.add(lead)
        session.commit()

    console.print(f"[green]Lead #{lead_id} status → {new_status.value}[/green]")


@lead_app.command("score")
def lead_score_cmd(
    lead_id: int = typer.Argument(0, help="Lead ID (or use --all-new)."),
    all_new: bool = typer.Option(False, "--all-new", help="Score all NEW leads."),
) -> None:
    """Score a lead (or all new leads)."""
    from freelance_os.db import reset_engine, get_session
    from freelance_os.models import Lead, LeadStatus
    from freelance_os.scoring.lead_scorer import score_lead
    from sqlmodel import select

    db_path = _get_db_path()
    reset_engine()

    with get_session(db_path) as session:
        if all_new:
            leads = session.exec(
                select(Lead).where(Lead.status == LeadStatus.NEW)
            ).all()
        elif lead_id:
            lead = session.get(Lead, lead_id)
            leads = [lead] if lead else []
        else:
            console.print("[red]Provide a lead ID or --all-new.[/red]")
            raise typer.Exit(1)

        if not leads:
            console.print("No leads to score.")
            return

        for lead in leads:
            result = score_lead(lead)
            lead.lead_score = result.lead_score
            lead.risk_score = result.risk_score
            lead.decision = result.decision
            lead.set_reason_codes(result.reason_codes)
            lead.status = LeadStatus.SCORED
            session.add(lead)
            console.print(
                f"[cyan]Lead #{lead.id}[/cyan] score={result.lead_score:.0f} "
                f"risk={result.risk_score:.0f} → [bold]{result.decision.value}[/bold] "
                f"({', '.join(result.reason_codes[:3])})"
            )

        session.commit()


@lead_app.command("draft")
def lead_draft_cmd(lead_id: int = typer.Argument(..., help="Lead ID.")) -> None:
    """Generate a proposal draft for a lead."""
    from freelance_os.db import reset_engine, get_session
    from freelance_os.models import Lead, LeadStatus
    from freelance_os.proposal.draft_generator import generate_draft

    db_path = _get_db_path()
    reset_engine()

    with get_session(db_path) as session:
        lead = session.get(Lead, lead_id)
        if not lead:
            console.print(f"[red]Lead #{lead_id} not found.[/red]")
            raise typer.Exit(1)
        draft = generate_draft(lead, session=session)
        lead.status = LeadStatus.DRAFTED
        session.add(lead)
        session.commit()
        session.refresh(draft)

    console.print(f"[green]Draft #{draft.id} created for Lead #{lead_id}.[/green]")
    console.print("\n" + (draft.draft_text or ""))


@lead_app.command("validate-draft")
def lead_validate_draft_cmd(lead_id: int = typer.Argument(..., help="Lead ID.")) -> None:
    """Validate the latest proposal draft for a lead."""
    from freelance_os.db import reset_engine, get_session
    from freelance_os.models import Lead, ProposalDraft
    from freelance_os.proposal.proposal_validator import validate_draft
    from sqlmodel import select

    db_path = _get_db_path()
    reset_engine()

    with get_session(db_path) as session:
        lead = session.get(Lead, lead_id)
        if not lead:
            console.print(f"[red]Lead #{lead_id} not found.[/red]")
            raise typer.Exit(1)

        draft = session.exec(
            select(ProposalDraft)
            .where(ProposalDraft.lead_id == lead_id)
            .order_by(ProposalDraft.version.desc())
        ).first()

        if not draft:
            console.print(f"[red]No draft found for Lead #{lead_id}.[/red]")
            raise typer.Exit(1)

        result = validate_draft(draft, lead)

    color = {"PASS": "green", "WARN": "yellow", "FAIL": "red"}.get(result.status, "white")
    console.print(f"Validation: [{color}]{result.status}[/{color}]")
    for flag in result.flags:
        console.print(f"  • {flag}")


@lead_app.command("review")
def lead_review_cmd() -> None:
    """Interactive review of scored leads."""
    from freelance_os.db import reset_engine, get_session
    from freelance_os.models import Lead, LeadStatus
    from sqlmodel import select

    db_path = _get_db_path()
    reset_engine()

    with get_session(db_path) as session:
        leads = session.exec(
            select(Lead).where(Lead.status == LeadStatus.SCORED).order_by(Lead.lead_score.desc())
        ).all()

    if not leads:
        console.print("No scored leads to review.")
        return

    for lead in leads:
        console.print(f"\n[bold]Lead #{lead.id}[/bold]")
        console.print(f"  Source: {lead.source}")
        console.print(f"  Title:  {lead.title or '(untitled)'}")
        console.print(f"  Score:  {lead.lead_score}")
        console.print(f"  Decision: {lead.decision.value if lead.decision else '—'}")
        console.print(f"  Reasons:  {', '.join(lead.get_reason_codes())}")
        if lead.source_url:
            console.print(f"  URL:    {lead.source_url}")


# ---------------------------------------------------------------------------
# Client commands
# ---------------------------------------------------------------------------

@client_app.command("init")
def client_init_cmd(
    lead_id: int = typer.Option(..., "--lead", help="Lead ID (must be WON)."),
    repo: str = typer.Option("", "--repo", help="Optional repo URL."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing workspace."),
) -> None:
    """Initialize a client project workspace from a won lead."""
    from freelance_os.db import reset_engine, get_session
    from freelance_os.models import Lead, LeadStatus
    from freelance_os.client.workspace import create_workspace

    db_path = _get_db_path()
    reset_engine()

    with get_session(db_path) as session:
        lead = session.get(Lead, lead_id)
        if not lead:
            console.print(f"[red]Lead #{lead_id} not found.[/red]")
            raise typer.Exit(1)
        if lead.status != LeadStatus.WON:
            console.print(f"[red]Lead #{lead_id} is not WON (current: {lead.status.value}).[/red]")
            raise typer.Exit(1)

        project = create_workspace(lead, session=session, repo_url=repo or None, force=force)
        session.commit()
        session.refresh(project)

    console.print(f"[green]Client project #{project.id} created:[/green] {project.workspace_path}")


@client_app.command("list")
def client_list_cmd() -> None:
    """List client projects."""
    from freelance_os.db import reset_engine, get_session
    from freelance_os.models import ClientProject
    from sqlmodel import select
    from rich.table import Table

    db_path = _get_db_path()
    reset_engine()

    with get_session(db_path) as session:
        projects = session.exec(select(ClientProject).order_by(ClientProject.id)).all()

    if not projects:
        console.print("No client projects.")
        return

    table = Table(title="Client Projects")
    table.add_column("ID", style="cyan")
    table.add_column("Client")
    table.add_column("Project")
    table.add_column("Status", style="yellow")
    table.add_column("Workspace")

    for p in projects:
        table.add_row(str(p.id), p.client_name, p.project_name, p.status.value, p.workspace_path or "—")
    console.print(table)


@client_app.command("show")
def client_show_cmd(project_id: int = typer.Argument(..., help="Project ID.")) -> None:
    """Show client project details."""
    from freelance_os.db import reset_engine, get_session
    from freelance_os.models import ClientProject

    db_path = _get_db_path()
    reset_engine()

    with get_session(db_path) as session:
        project = session.get(ClientProject, project_id)

    if not project:
        console.print(f"[red]Project #{project_id} not found.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Project #{project.id}[/bold]")
    console.print(f"  Client:    {project.client_name}")
    console.print(f"  Name:      {project.project_name}")
    console.print(f"  Status:    {project.status.value}")
    console.print(f"  Workspace: {project.workspace_path or '—'}")
    console.print(f"  Branch:    {project.branch_name or '—'}")
    console.print(f"  Repo:      {project.repo_url or '—'}")


@client_app.command("package")
def client_package_cmd(
    project: str = typer.Option(..., "--project", help="Project name or workspace path."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing delivery files."),
) -> None:
    """Generate delivery package for a client project."""
    from freelance_os.db import reset_engine, get_session
    from freelance_os.models import ClientProject
    from freelance_os.client.delivery import create_delivery_package
    from sqlmodel import select

    db_path = _get_db_path()
    reset_engine()

    with get_session(db_path) as session:
        cp = session.exec(
            select(ClientProject).where(ClientProject.project_name == project)
        ).first()

        if not cp:
            console.print(f"[red]Project '{project}' not found.[/red]")
            raise typer.Exit(1)

        create_delivery_package(cp, force=force)

    console.print(f"[green]Delivery package created for '{project}'.[/green]")
    if cp.workspace_path:
        console.print(f"  Files in: {cp.workspace_path}/02_delivery/")


@client_app.command("tmux")
def client_tmux_cmd(
    project: str = typer.Option(..., "--project", help="Project name."),
) -> None:
    """Generate tmux session startup script for a project."""
    from freelance_os.execution.tmux import generate_tmux_script

    script_path = generate_tmux_script(project)
    console.print(f"[green]Tmux script generated:[/green] {script_path}")
    console.print(f"  Run: bash {script_path} {project}")


@client_app.command("worktree")
def client_worktree_cmd(
    project: str = typer.Option(..., "--project", help="Project name."),
    repo: str = typer.Option(..., "--repo", help="Git repo URL."),
) -> None:
    """Dry-run: show worktree setup commands for a project."""
    from freelance_os.execution.worktree import show_worktree_commands

    show_worktree_commands(project, repo)


# ---------------------------------------------------------------------------
# Outcome commands
# ---------------------------------------------------------------------------

@outcome_app.command("add")
def outcome_add_cmd(
    lead_id: int = typer.Option(..., "--lead", help="Lead ID."),
) -> None:
    """Record an outcome for a lead."""
    from freelance_os.db import reset_engine, get_session
    from freelance_os.models import Lead, Outcome, OutcomeResult

    db_path = _get_db_path()
    reset_engine()

    with get_session(db_path) as session:
        lead = session.get(Lead, lead_id)
        if not lead:
            console.print(f"[red]Lead #{lead_id} not found.[/red]")
            raise typer.Exit(1)

        console.print(f"Recording outcome for Lead #{lead_id}: {lead.title or '(untitled)'}")

        result_str = typer.prompt(
            "Result",
            default="WON",
            show_default=True,
        ).upper()

        try:
            result = OutcomeResult(result_str)
        except ValueError:
            valid = [r.value for r in OutcomeResult]
            console.print(f"[red]Invalid result. Valid: {', '.join(valid)}[/red]")
            raise typer.Exit(1)

        reason = typer.prompt("Reason (optional)", default="", show_default=False) or None
        final_budget_str = typer.prompt("Final budget (optional)", default="", show_default=False)
        final_budget = float(final_budget_str) if final_budget_str else None
        hours_str = typer.prompt("Hours spent (optional)", default="", show_default=False)
        hours = float(hours_str) if hours_str else None
        lessons = typer.prompt("Lessons learned (optional)", default="", show_default=False) or None

        outcome = Outcome(
            lead_id=lead_id,
            result=result,
            reason=reason,
            final_budget=final_budget,
            time_spent_hours=hours,
            lessons=lessons,
        )
        session.add(outcome)
        session.commit()

    console.print(f"[green]Outcome recorded:[/green] {result.value}")


# ---------------------------------------------------------------------------
# Report commands
# ---------------------------------------------------------------------------

@report_app.command("weekly")
def report_weekly_cmd() -> None:
    """Generate a weekly performance report."""
    from freelance_os.db import reset_engine
    from freelance_os.reports.outcome_report import generate_weekly_report

    db_path = _get_db_path()
    reset_engine()

    report_text = generate_weekly_report(db_path=db_path)
    console.print(report_text)


if __name__ == "__main__":
    app()
