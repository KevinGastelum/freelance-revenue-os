"""Freelance Revenue OS CLI — AI prepares, human commits."""

from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="freelance-os",
    help="Freelance Revenue OS — AI prepares. Human commits.",
    no_args_is_help=True,
)
console = Console()

# Sub-command groups
lead_app = typer.Typer(help="Lead management commands.", no_args_is_help=True)
client_app = typer.Typer(help="Client workspace commands.", no_args_is_help=True)
outcome_app = typer.Typer(help="Outcome tracking commands.", no_args_is_help=True)
report_app = typer.Typer(help="Report commands.", no_args_is_help=True)

app.add_typer(lead_app, name="lead")
app.add_typer(client_app, name="client")
app.add_typer(outcome_app, name="outcome")
app.add_typer(report_app, name="report")


# ---------------------------------------------------------------------------
# freelance-os init
# ---------------------------------------------------------------------------

@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Drop and recreate all tables."),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Initialize the data directory and SQLite database (idempotent)."""
    from freelance_os.config import ConfigError, load_config
    from freelance_os.db import create_tables, drop_tables, get_engine

    cfg_path = config or "config/settings.toml"
    try:
        cfg = load_config(cfg_path)
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    db_path = cfg["paths"]["database_path"]
    engine = get_engine(db_path)

    if force:
        drop_tables(engine)
        console.print("[yellow]Dropped existing tables (--force).[/yellow]")

    create_tables(engine, db_path)
    console.print(f"[green]Database initialized:[/green] {db_path}")
    console.print("[green]All tables ready (idempotent).[/green]")


# ---------------------------------------------------------------------------
# lead sub-commands
# ---------------------------------------------------------------------------

@lead_app.command("add-url")
def lead_add_url(
    url: str = typer.Argument(..., help="Job posting URL"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Paste job description"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Add a lead by URL (manual intake)."""
    from freelance_os.ingestion.manual import add_lead_url
    from freelance_os.config import load_config, ConfigError

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    lead = add_lead_url(url=url, description=description, cfg=cfg)
    console.print(f"[green]Lead #{lead.id} created:[/green] {url}")


@lead_app.command("add-text")
def lead_add_text(
    source: str = typer.Option(..., "--source", "-s", help="Source platform (e.g. upwork)"),
    text: Optional[str] = typer.Option(None, "--text", help="Job description text"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Add a lead by pasting text (reads stdin if --text not provided)."""
    import sys
    from freelance_os.ingestion.manual import add_lead_text
    from freelance_os.config import load_config, ConfigError

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    if text is None:
        if sys.stdin.isatty():
            console.print("[yellow]Paste job description, then press Ctrl+D:[/yellow]")
        text = sys.stdin.read().strip()

    if not text:
        console.print("[red]No text provided.[/red]")
        raise typer.Exit(1)

    lead = add_lead_text(source=source, text=text, cfg=cfg)
    console.print(f"[green]Lead #{lead.id} created from {source}[/green]")


@lead_app.command("list")
def lead_list(
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """List all leads."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.db import get_engine
    from freelance_os.models import Lead
    from sqlmodel import Session, select
    from rich.table import Table

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    engine = get_engine(cfg["paths"]["database_path"])
    with Session(engine) as session:
        stmt = select(Lead)
        if status:
            stmt = stmt.where(Lead.status == status.upper())
        leads = session.exec(stmt).all()

    if not leads:
        console.print("[dim]No leads found.[/dim]")
        return

    table = Table(title="Leads", show_lines=False)
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Status", style="yellow", width=18)
    table.add_column("Score", width=6)
    table.add_column("Decision", width=12)
    table.add_column("Source", width=14)
    table.add_column("Title", style="white")

    for lead in leads:
        table.add_row(
            str(lead.id),
            lead.status,
            str(lead.lead_score) if lead.lead_score is not None else "-",
            lead.decision or "-",
            lead.source,
            (lead.title or lead.source_url or "(no title)")[:60],
        )
    console.print(table)


@lead_app.command("show")
def lead_show(
    lead_id: int = typer.Argument(..., help="Lead ID"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Show full details for a lead."""
    import json as _json
    from freelance_os.config import load_config, ConfigError
    from freelance_os.db import get_engine
    from freelance_os.models import Lead
    from sqlmodel import Session

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    engine = get_engine(cfg["paths"]["database_path"])
    with Session(engine) as session:
        lead = session.get(Lead, lead_id)

    if lead is None:
        console.print(f"[red]Lead #{lead_id} not found.[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]Lead #{lead.id}[/bold cyan]")
    console.print(f"  Source:      {lead.source}")
    console.print(f"  URL:         {lead.source_url or '-'}")
    console.print(f"  Title:       {lead.title or '-'}")
    console.print(f"  Status:      {lead.status}")
    console.print(f"  Decision:    {lead.decision or '-'}")
    console.print(f"  Score:       {lead.lead_score if lead.lead_score is not None else '-'}")
    console.print(f"  Risk Score:  {lead.risk_score if lead.risk_score is not None else '-'}")
    if lead.reason_codes:
        codes = _json.loads(lead.reason_codes)
        console.print(f"  Reasons:     {', '.join(codes)}")
    console.print(f"  Imported:    {lead.imported_at}")
    if lead.description:
        console.print(f"\n  Description:\n{lead.description[:500]}")


@lead_app.command("status")
def lead_status(
    lead_id: int = typer.Argument(..., help="Lead ID"),
    new_status: str = typer.Argument(..., help="New status value"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Set lead status manually."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.db import get_engine
    from freelance_os.models import Lead, LeadStatus
    from sqlmodel import Session

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    try:
        status_val = LeadStatus(new_status.upper())
    except ValueError:
        valid = ", ".join(s.value for s in LeadStatus)
        console.print(f"[red]Invalid status '{new_status}'. Valid: {valid}[/red]")
        raise typer.Exit(1)

    engine = get_engine(cfg["paths"]["database_path"])
    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        if lead is None:
            console.print(f"[red]Lead #{lead_id} not found.[/red]")
            raise typer.Exit(1)
        lead.status = status_val
        session.add(lead)
        session.commit()

    console.print(f"[green]Lead #{lead_id} status set to {status_val.value}[/green]")


@lead_app.command("score")
def lead_score(
    lead_id: Optional[int] = typer.Argument(None, help="Lead ID to score"),
    all_new: bool = typer.Option(False, "--all-new", help="Score all NEW leads"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Score one lead or all NEW leads."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.db import get_engine
    from freelance_os.models import Lead, LeadStatus
    from freelance_os.scoring.lead_scorer import score_lead
    from sqlmodel import Session, select

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    engine = get_engine(cfg["paths"]["database_path"])

    if all_new:
        with Session(engine) as session:
            leads = session.exec(select(Lead).where(Lead.status == LeadStatus.NEW)).all()
        if not leads:
            console.print("[dim]No NEW leads to score.[/dim]")
            return
        for lead in leads:
            _do_score(lead.id, engine, cfg)
    elif lead_id is not None:
        _do_score(lead_id, engine, cfg)
    else:
        console.print("[red]Provide a LEAD_ID or --all-new.[/red]")
        raise typer.Exit(1)


def _do_score(lead_id: int, engine, cfg: dict) -> None:
    import json as _json
    from freelance_os.models import Lead, LeadStatus
    from freelance_os.scoring.lead_scorer import score_lead
    from sqlmodel import Session

    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        if lead is None:
            console.print(f"[red]Lead #{lead_id} not found.[/red]")
            return
        result = score_lead(lead, cfg)
        lead.lead_score = result["lead_score"]
        lead.risk_score = result["risk_score"]
        lead.decision = result["decision"]
        lead.reason_codes = _json.dumps(result["reason_codes"])
        lead.status = LeadStatus.SCORED
        session.add(lead)
        session.commit()

    console.print(
        f"[green]Lead #{lead_id}[/green] score={result['lead_score']} "
        f"risk={result['risk_score']} decision={result['decision']} "
        f"reasons={result['reason_codes']}"
    )


@lead_app.command("draft")
def lead_draft(
    lead_id: int = typer.Argument(..., help="Lead ID"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Generate a proposal draft for a lead."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.db import get_engine
    from freelance_os.models import Lead, ProposalDraft, LeadStatus
    from freelance_os.proposal.draft_generator import generate_draft
    from sqlmodel import Session
    import json as _json

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    engine = get_engine(cfg["paths"]["database_path"])
    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        if lead is None:
            console.print(f"[red]Lead #{lead_id} not found.[/red]")
            raise typer.Exit(1)

        draft_data = generate_draft(lead, cfg)
        draft = ProposalDraft(
            lead_id=lead_id,
            draft_text=draft_data["draft_text"],
            technical_diagnosis=draft_data["technical_diagnosis"],
            portfolio_matches=_json.dumps(draft_data.get("portfolio_matches", [])),
            clarifying_questions=_json.dumps(draft_data.get("clarifying_questions", [])),
            price_recommendation=draft_data.get("price_recommendation"),
        )
        session.add(draft)
        lead.status = LeadStatus.DRAFTED
        session.add(lead)
        session.commit()
        session.refresh(draft)
        draft_id = draft.id

    console.print(f"[green]ProposalDraft #{draft_id} created for Lead #{lead_id}[/green]")
    console.print("\n[bold]Draft:[/bold]")
    console.print(draft_data["draft_text"])


@lead_app.command("validate-draft")
def lead_validate_draft(
    lead_id: int = typer.Argument(..., help="Lead ID"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Validate the latest proposal draft for a lead."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.db import get_engine
    from freelance_os.models import ProposalDraft
    from freelance_os.proposal.proposal_validator import validate_draft
    from sqlmodel import Session, select

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    engine = get_engine(cfg["paths"]["database_path"])
    with Session(engine) as session:
        draft = session.exec(
            select(ProposalDraft)
            .where(ProposalDraft.lead_id == lead_id)
            .order_by(ProposalDraft.version.desc())
        ).first()

        if draft is None:
            console.print(f"[red]No draft found for Lead #{lead_id}. Run 'lead draft {lead_id}' first.[/red]")
            raise typer.Exit(1)

        result = validate_draft(draft, cfg)
        status_color = {"PASS": "green", "WARN": "yellow", "FAIL": "red"}.get(result["status"], "white")
        console.print(f"\n[{status_color}]Validation: {result['status']}[/{status_color}]")
        if result.get("reasons"):
            for r in result["reasons"]:
                console.print(f"  - {r}")

        import json as _json
        draft.validator_flags = _json.dumps(result)
        session.add(draft)
        session.commit()


@lead_app.command("review")
def lead_review(
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Interactive review queue for scored leads."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.db import get_engine
    from freelance_os.models import Lead, LeadStatus, Decision
    from sqlmodel import Session, select
    import json as _json

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    engine = get_engine(cfg["paths"]["database_path"])
    with Session(engine) as session:
        leads = session.exec(
            select(Lead).where(Lead.status == LeadStatus.SCORED)
        ).all()

    if not leads:
        console.print("[dim]No SCORED leads to review.[/dim]")
        return

    for lead in leads:
        console.print(f"\n[bold cyan]Lead #{lead.id}[/bold cyan]")
        console.print(f"  Source: {lead.source}")
        console.print(f"  Title:  {lead.title or lead.source_url or '(no title)'}")
        console.print(f"  Score:  {lead.lead_score}  Decision: {lead.decision}")
        if lead.reason_codes:
            codes = _json.loads(lead.reason_codes)
            console.print(f"  Why:    {', '.join(codes)}")
        console.print("\n  [a]pprove  [r]eject  [w]atch  [s]kip  [q]uit")
        choice = input("  > ").strip().lower()
        if choice == "q":
            break
        elif choice == "a":
            with Session(engine) as session:
                l = session.get(Lead, lead.id)
                l.status = LeadStatus.APPROVED_TO_APPLY
                session.add(l)
                session.commit()
            console.print(f"[green]Lead #{lead.id} approved.[/green]")
        elif choice == "r":
            with Session(engine) as session:
                l = session.get(Lead, lead.id)
                l.status = LeadStatus.REJECTED
                session.add(l)
                session.commit()
            console.print(f"[yellow]Lead #{lead.id} rejected.[/yellow]")
        elif choice == "w":
            with Session(engine) as session:
                l = session.get(Lead, lead.id)
                l.decision = Decision.WATCH
                session.add(l)
                session.commit()
            console.print(f"[dim]Lead #{lead.id} set to WATCH.[/dim]")


# ---------------------------------------------------------------------------
# client sub-commands
# ---------------------------------------------------------------------------

@client_app.command("init")
def client_init(
    lead_id: int = typer.Option(..., "--lead", help="Lead ID (must be WON)"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Git repo URL"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing workspace"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Convert a WON lead into a client project workspace."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.client.workspace import init_workspace

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    project = init_workspace(lead_id=lead_id, cfg=cfg, repo_url=repo, force=force)
    console.print(f"[green]Client workspace created:[/green] {project.workspace_path}")


@client_app.command("list")
def client_list(
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """List all client projects."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.db import get_engine
    from freelance_os.models import ClientProject
    from sqlmodel import Session, select
    from rich.table import Table

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    engine = get_engine(cfg["paths"]["database_path"])
    with Session(engine) as session:
        projects = session.exec(select(ClientProject)).all()

    if not projects:
        console.print("[dim]No client projects.[/dim]")
        return

    table = Table(title="Client Projects")
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Client", width=16)
    table.add_column("Project", width=20)
    table.add_column("Status", width=18)
    table.add_column("Path")

    for p in projects:
        table.add_row(str(p.id), p.client_name, p.project_name, p.status, p.workspace_path or "-")
    console.print(table)


@client_app.command("show")
def client_show(
    project_id: int = typer.Argument(..., help="Client project ID"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Show client project details."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.db import get_engine
    from freelance_os.models import ClientProject
    from sqlmodel import Session

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    engine = get_engine(cfg["paths"]["database_path"])
    with Session(engine) as session:
        project = session.get(ClientProject, project_id)

    if project is None:
        console.print(f"[red]Project #{project_id} not found.[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]Project #{project.id}[/bold cyan]")
    console.print(f"  Client:    {project.client_name}")
    console.print(f"  Project:   {project.project_name}")
    console.print(f"  Platform:  {project.platform or '-'}")
    console.print(f"  Status:    {project.status}")
    console.print(f"  Workspace: {project.workspace_path or '-'}")
    console.print(f"  Repo:      {project.repo_url or '-'}")
    console.print(f"  Branch:    {project.branch_name or '-'}")


@client_app.command("package")
def client_package(
    project_name: str = typer.Option(..., "--project", help="Project folder name"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing delivery files"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Generate delivery package for a client project."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.client.delivery import generate_delivery_package

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    path = generate_delivery_package(project_name=project_name, cfg=cfg, force=force)
    console.print(f"[green]Delivery package created:[/green] {path}")


@client_app.command("tmux")
def client_tmux(
    project_name: str = typer.Option(..., "--project", help="Project folder name"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Generate tmux session launch script for a project."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.execution.tmux import generate_tmux_script

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    script_path = generate_tmux_script(project_name=project_name, cfg=cfg)
    console.print(f"[green]Tmux script generated:[/green] {script_path}")
    console.print(f"[dim]Run:[/dim] bash {script_path}")


@client_app.command("worktree")
def client_worktree(
    project_name: str = typer.Option(..., "--project", help="Project folder name"),
    repo: str = typer.Option(..., "--repo", help="Git repo URL"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Dry run (default on)"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Generate worktree setup commands (dry-run by default)."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.execution.worktree import generate_worktree_commands

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    cmds = generate_worktree_commands(project_name=project_name, repo_url=repo, cfg=cfg)
    console.print("[bold]Worktree commands (dry-run):[/bold]")
    for cmd in cmds:
        console.print(f"  [cyan]{cmd}[/cyan]")
    if dry_run:
        console.print("\n[dim]Dry-run mode: no commands executed. Remove --dry-run to generate a script.[/dim]")


# ---------------------------------------------------------------------------
# outcome sub-commands
# ---------------------------------------------------------------------------

@outcome_app.command("add")
def outcome_add(
    lead_id: int = typer.Option(..., "--lead", help="Lead ID"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Record the outcome for a lead interactively."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.db import get_engine
    from freelance_os.models import Lead, Outcome, OutcomeResult
    from sqlmodel import Session

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    engine = get_engine(cfg["paths"]["database_path"])
    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        if lead is None:
            console.print(f"[red]Lead #{lead_id} not found.[/red]")
            raise typer.Exit(1)

    valid_results = [r.value for r in OutcomeResult]
    console.print(f"Outcome result ({'/'.join(valid_results)}): ", end="")
    result_str = input().strip().upper()
    try:
        result_val = OutcomeResult(result_str)
    except ValueError:
        console.print(f"[red]Invalid result. Valid: {', '.join(valid_results)}[/red]")
        raise typer.Exit(1)

    console.print("Reason (optional): ", end="")
    reason = input().strip() or None
    console.print("Final budget (optional, number): ", end="")
    budget_str = input().strip()
    final_budget = float(budget_str) if budget_str else None
    console.print("Hours spent (optional, number): ", end="")
    hours_str = input().strip()
    time_spent = float(hours_str) if hours_str else None
    console.print("Lessons learned (optional): ", end="")
    lessons = input().strip() or None

    with Session(engine) as session:
        outcome = Outcome(
            lead_id=lead_id,
            result=result_val,
            reason=reason,
            final_budget=final_budget,
            time_spent_hours=time_spent,
            lessons=lessons,
        )
        session.add(outcome)
        session.commit()
        session.refresh(outcome)
        console.print(f"[green]Outcome #{outcome.id} recorded.[/green]")


# ---------------------------------------------------------------------------
# report sub-commands
# ---------------------------------------------------------------------------

@report_app.command("weekly")
def report_weekly(
    export: Optional[str] = typer.Option(None, "--export", help="Export to markdown file"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Generate weekly performance report."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.reports.outcome_report import generate_weekly_report

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    report = generate_weekly_report(cfg=cfg, export_path=export)
    console.print(report)
