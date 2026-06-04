"""Freelance Revenue OS CLI — AI prepares, human commits."""

import sys
import io
from typing import Optional

import typer
from rich import box as rich_box
from rich.console import Console

# Force UTF-8 stdout on Windows (cp1252 can't encode box-drawing or non-ASCII chars).
if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "utf-8").lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer") and getattr(sys.stderr, "encoding", "utf-8").lower() not in ("utf-8", "utf8"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

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
sources_app = typer.Typer(help="Platform source directory commands.", no_args_is_help=True)

app.add_typer(lead_app, name="lead")
app.add_typer(client_app, name="client")
app.add_typer(outcome_app, name="outcome")
app.add_typer(report_app, name="report")
app.add_typer(sources_app, name="sources")


# ---------------------------------------------------------------------------
# freelance-os init
# ---------------------------------------------------------------------------

@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Drop and recreate all tables."),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Initialize the data directory and SQLite database (idempotent)."""
    import shutil
    from pathlib import Path
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

    # Copy sources.example.yaml -> sources.yaml if absent.
    sources_example = Path("config/sources.example.yaml")
    sources_dest = Path("config/sources.yaml")
    if sources_example.exists() and not sources_dest.exists():
        shutil.copy2(sources_example, sources_dest)
        console.print(f"[green]Created:[/green] {sources_dest} (copied from example)")


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


@lead_app.command("ingest-email")
def lead_ingest_email(
    input: Optional[str] = typer.Option(None, "--input", "-i", help=".eml or .mbox file path"),
    text: Optional[str] = typer.Option(None, "--text", help="Raw email text (or use stdin)"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Override detected source platform"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Parse job-alert emails (.eml, .mbox, pasted text/stdin) into leads."""
    import sys
    from pathlib import Path as _Path
    from freelance_os.config import load_config, ConfigError
    from freelance_os.db import get_engine
    from freelance_os.ingestion.email_parser import parse_eml_file, parse_mbox_file, parse_raw_text
    from freelance_os.ingestion.classify import classify_lead
    from freelance_os.models import Lead, LeadStatus
    from sqlmodel import Session, select

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    raw_jobs = []
    if input is not None:
        p = _Path(input)
        if not p.exists():
            console.print(f"[red]File not found:[/red] {p}")
            raise typer.Exit(1)
        suffix = p.suffix.lower()
        if suffix == ".eml":
            raw_jobs = parse_eml_file(p, source_override=source)
        elif suffix == ".mbox":
            raw_jobs = parse_mbox_file(p, source_override=source)
        else:
            raw_jobs = parse_raw_text(p.read_text(encoding="utf-8", errors="replace"), source)
    else:
        if text is None:
            if sys.stdin.isatty():
                console.print("[yellow]Paste email text, then press Ctrl+D:[/yellow]")
            text = sys.stdin.read().strip()
        if not text:
            console.print("[red]No input provided. Use --input FILE or --text TEXT.[/red]")
            raise typer.Exit(1)
        raw_jobs = parse_raw_text(text, source)

    if not raw_jobs:
        console.print("[yellow]No job postings detected in input.[/yellow]")
        return

    engine = get_engine(cfg["paths"]["database_path"])
    created, skipped = _save_email_leads(raw_jobs, engine)
    console.print(f"[green]Created {created} lead(s)[/green], [dim]skipped {skipped} duplicate(s).[/dim]")


@lead_app.command("ingest-imap")
def lead_ingest_imap(
    max_emails: int = typer.Option(50, "--max", help="Max emails to scan"),
    source: Optional[str] = typer.Option(None, "--source", help="Override detected source platform"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Fetch job-alert emails via IMAP and import as leads (read-only).

    Requires [imap] host and user in settings.toml, and
    FREELANCE_OS_IMAP_PASSWORD env var set to an app-specific password.
    """
    from freelance_os.config import load_config, ConfigError
    from freelance_os.db import get_engine
    from freelance_os.ingestion.imap_fetch import fetch_job_alert_emails

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    try:
        raw_jobs = fetch_job_alert_emails(cfg, max_emails=max_emails, source_override=source)
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    if not raw_jobs:
        console.print("[dim]No job alerts found in the configured mailbox.[/dim]")
        return

    engine = get_engine(cfg["paths"]["database_path"])
    created, skipped = _save_email_leads(raw_jobs, engine)
    console.print(f"[green]Created {created} lead(s)[/green], [dim]skipped {skipped} duplicate(s).[/dim]")


def _save_email_leads(raw_jobs: list, engine) -> tuple:
    """Dedup-check and insert email-parsed job leads. Returns (created, skipped)."""
    from freelance_os.ingestion.classify import classify_lead
    from freelance_os.models import Lead, LeadStatus
    from sqlmodel import Session, select

    created, skipped = 0, 0
    with Session(engine) as session:
        for job in raw_jobs:
            if job.get("source_url"):
                if session.exec(select(Lead).where(Lead.source_url == job["source_url"])).first():
                    skipped += 1
                    continue
            elif job.get("source") and job.get("title"):
                if session.exec(
                    select(Lead)
                    .where(Lead.source == job["source"])
                    .where(Lead.title == job["title"])
                ).first():
                    skipped += 1
                    continue

            classify_text = " ".join(filter(None, [job.get("title"), job.get("description")]))
            lead = Lead(
                source=job.get("source", "email"),
                source_url=job.get("source_url"),
                title=job.get("title"),
                description=job.get("description"),
                budget_type=job.get("budget_type"),
                budget_min=job.get("budget_min"),
                budget_max=job.get("budget_max"),
                hourly_min=job.get("hourly_min"),
                hourly_max=job.get("hourly_max"),
                status=LeadStatus.NEW,
                category=classify_lead(classify_text),
            )
            session.add(lead)
            created += 1
        session.commit()
    return created, skipped


@lead_app.command("list")
def lead_list(
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    category: Optional[str] = typer.Option(None, "--category", help="Filter by category (e.g. WEB_APP)"),
    source: Optional[str] = typer.Option(None, "--source", help="Filter by source platform"),
    decision: Optional[str] = typer.Option(None, "--decision", help="Filter by decision (e.g. DRAFT_NOW)"),
    min_score: Optional[int] = typer.Option(None, "--min-score", help="Minimum lead score"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """List leads with optional filters."""
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
        if category:
            stmt = stmt.where(Lead.category == category.upper())
        if source:
            stmt = stmt.where(Lead.source == source)
        if decision:
            stmt = stmt.where(Lead.decision == decision.upper())
        leads = session.exec(stmt).all()

    if min_score is not None:
        leads = [l for l in leads if l.lead_score is not None and l.lead_score >= min_score]

    if not leads:
        console.print("[dim]No leads found.[/dim]")
        return

    table = Table(title="Leads", show_lines=False, box=rich_box.ASCII)
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Cat", width=14)
    table.add_column("Status", style="yellow", width=16)
    table.add_column("Score", width=6)
    table.add_column("Decision", width=12)
    table.add_column("Source", width=14)
    table.add_column("Title", style="white")

    for lead in leads:
        table.add_row(
            str(lead.id),
            lead.category or "OTHER",
            lead.status,
            str(lead.lead_score) if lead.lead_score is not None else "-",
            lead.decision or "-",
            lead.source,
            (lead.title or lead.source_url or "(no title)")[:55],
        )
    console.print(table)


@lead_app.command("recategorize")
def lead_recategorize(
    lead_id: Optional[int] = typer.Argument(None, help="Lead ID to recategorize"),
    all_leads: bool = typer.Option(False, "--all", help="Recategorize all leads"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Recategorize one lead or all leads using the keyword classifier."""
    from freelance_os.config import load_config, ConfigError
    from freelance_os.db import get_engine
    from freelance_os.models import Lead
    from freelance_os.ingestion.classify import classify_lead
    from sqlmodel import Session, select

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    engine = get_engine(cfg["paths"]["database_path"])

    with Session(engine) as session:
        if all_leads:
            leads = session.exec(select(Lead)).all()
        elif lead_id is not None:
            lead = session.get(Lead, lead_id)
            leads = [lead] if lead else []
        else:
            console.print("[red]Provide a LEAD_ID or --all.[/red]")
            raise typer.Exit(1)

        updated = 0
        for lead in leads:
            text = " ".join(filter(None, [lead.title, lead.description]))
            new_cat = classify_lead(text)
            if lead.category != new_cat:
                lead.category = new_cat
                session.add(lead)
                updated += 1
        session.commit()

    if all_leads:
        console.print(f"[green]Recategorized {updated} lead(s) (of {len(leads)} total).[/green]")
    else:
        console.print(f"[green]Lead #{lead_id} recategorized.[/green]")


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

    table = Table(title="Client Projects", box=rich_box.ASCII)
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

@app.command()
def tune(
    port: int = typer.Option(8765, "--port", "-p", help="Local port to bind (127.0.0.1 only)"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Do not open browser automatically"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Launch the metric-tuning web console on 127.0.0.1.

    Adjust scoring weights, penalties, and thresholds; see live impact on all leads.
    """
    import webbrowser
    import uvicorn  # type: ignore[import]
    from freelance_os.config import load_config, ConfigError
    from freelance_os.tuner.app import app as tuner_app, configure

    try:
        cfg = load_config(config or "config/settings.toml")
    except ConfigError as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1)

    db_path = cfg["paths"]["database_path"]
    scoring_rules_path = "config/scoring_rules.toml"

    configure(db_path=db_path, scoring_rules_path=scoring_rules_path)

    url = f"http://127.0.0.1:{port}"
    console.print(f"[green]Metric Tuning Console:[/green] {url}")
    console.print("[dim]Press Ctrl+C to stop.[/dim]")

    if not no_browser:
        import threading
        def _open():
            import time
            time.sleep(0.8)
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    uvicorn.run(tuner_app, host="127.0.0.1", port=port, log_level="warning")


@sources_app.command("list")
def sources_list(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by job category"),
    newcomer: bool = typer.Option(False, "--newcomer", help="Only newcomer-friendly platforms"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="Filter by region (global, us, eu, latam, ...)"),
    config_dir: str = typer.Option("config", "--config-dir", help="Config directory"),
):
    """List freelance platforms from the source directory."""
    from freelance_os.sources import load_sources, filter_sources
    from rich.table import Table

    sources = load_sources(config_dir)
    if not sources:
        console.print("[yellow]No sources found. Run 'freelance-os init' to create config/sources.yaml.[/yellow]")
        raise typer.Exit(0)

    filtered = filter_sources(sources, category=category, newcomer=newcomer, region=region)
    if not filtered:
        console.print("[dim]No platforms match the given filters.[/dim]")
        return

    table = Table(title="Freelance Platforms", box=rich_box.ASCII)
    table.add_column("Name", style="cyan", width=18)
    table.add_column("Region", width=8)
    table.add_column("Vetted", width=6)
    table.add_column("New-OK", width=6)
    table.add_column("Categories", width=42)
    table.add_column("Fee Notes")

    for s in filtered:
        cats = ", ".join(s.get("categories", []))
        table.add_row(
            s.get("name", ""),
            s.get("region", ""),
            "yes" if s.get("vetted") else "no",
            "yes" if s.get("newcomer_friendly") else "no",
            cats[:40],
            s.get("fee_notes", ""),
        )
    console.print(table)


@app.command()
def board(
    config: Optional[str] = typer.Option(None, "--config", help="Path to settings.toml"),
):
    """Show job board summary grouped by category and source."""
    from collections import defaultdict
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
        leads = session.exec(select(Lead)).all()

    if not leads:
        console.print("[dim]No leads in the database.[/dim]")
        return

    # Build category summary
    cat_data: dict = defaultdict(lambda: {"count": 0, "scores": [], "decisions": defaultdict(int)})
    src_data: dict = defaultdict(lambda: {"count": 0, "scores": [], "decisions": defaultdict(int)})

    for lead in leads:
        cat = lead.category or "OTHER"
        src = lead.source or "unknown"
        dec = lead.decision or "unset"

        cat_data[cat]["count"] += 1
        cat_data[cat]["decisions"][dec] += 1
        if lead.lead_score is not None:
            cat_data[cat]["scores"].append(lead.lead_score)

        key = (src, cat)
        src_data[key]["count"] += 1
        src_data[key]["decisions"][dec] += 1
        if lead.lead_score is not None:
            src_data[key]["scores"].append(lead.lead_score)

    console.print(f"\n[bold]Job Board Summary[/bold] — {len(leads)} lead(s) total\n")

    # Category table
    cat_table = Table(title="By Category", box=rich_box.ASCII)
    cat_table.add_column("Category", style="cyan", width=16)
    cat_table.add_column("Count", width=6)
    cat_table.add_column("Avg Score", width=10)
    cat_table.add_column("DRAFT_NOW", width=10)
    cat_table.add_column("WATCH", width=7)
    cat_table.add_column("MAYBE", width=7)
    cat_table.add_column("REJECT", width=7)
    cat_table.add_column("Unset", width=6)

    for cat in sorted(cat_data.keys()):
        d = cat_data[cat]
        avg = f"{sum(d['scores']) / len(d['scores']):.1f}" if d["scores"] else "--"
        decs = d["decisions"]
        cat_table.add_row(
            cat,
            str(d["count"]),
            avg,
            str(decs.get("DRAFT_NOW", 0)),
            str(decs.get("WATCH", 0)),
            str(decs.get("MAYBE", 0)),
            str(decs.get("REJECT", 0)),
            str(decs.get("unset", 0)),
        )
    console.print(cat_table)

    # Source x category table
    src_table = Table(title="By Source x Category", box=rich_box.ASCII)
    src_table.add_column("Source", style="yellow", width=16)
    src_table.add_column("Category", style="cyan", width=16)
    src_table.add_column("Count", width=6)
    src_table.add_column("Avg Score", width=10)
    src_table.add_column("DRAFT_NOW", width=10)
    src_table.add_column("WATCH", width=7)

    for (src, cat) in sorted(src_data.keys()):
        d = src_data[(src, cat)]
        avg = f"{sum(d['scores']) / len(d['scores']):.1f}" if d["scores"] else "--"
        decs = d["decisions"]
        src_table.add_row(
            src,
            cat,
            str(d["count"]),
            avg,
            str(decs.get("DRAFT_NOW", 0)),
            str(decs.get("WATCH", 0)),
        )
    console.print(src_table)


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
