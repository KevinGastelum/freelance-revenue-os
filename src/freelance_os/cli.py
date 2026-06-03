import sys
from typing import Optional

import typer

from .schemas import LeadStatus

app = typer.Typer(name="freelance-os", help="Freelance Revenue OS — AI prepares, human commits.")
lead_app = typer.Typer(name="lead", help="Manage leads.")
app.add_typer(lead_app, name="lead")


@app.command()
def init() -> None:
    """Initialize the database and config directory."""
    from .db import create_all

    create_all()
    typer.echo("freelance-os initialized.")


# ---------------------------------------------------------------------------
# Lead commands
# ---------------------------------------------------------------------------


@lead_app.command("add-url")
def lead_add_url(
    url: str = typer.Argument(..., help="Source URL of the job posting"),
    description: str = typer.Option("", "--description", "-d", help="Optional description"),
) -> None:
    """Create a new lead from a URL. Prints the new lead id."""
    from .db import get_session
    from .models import Lead

    lead = Lead(
        source="manual_url",
        source_url=url,
        description=description or None,
        status=LeadStatus.NEW,
    )
    with get_session() as s:
        s.add(lead)
        s.commit()
        s.refresh(lead)
        typer.echo(lead.id)


@lead_app.command("add-text")
def lead_add_text(
    source: str = typer.Option(..., "--source", help="Source name (e.g. upwork, fiverr, direct)"),
    text: Optional[str] = typer.Option(None, "--text", help="Job text (reads stdin if omitted)"),
) -> None:
    """Create a lead from pasted job text. Prints the new lead id."""
    from .db import get_session
    from .ingestion.manual import (
        extract_budget_from_text,
        extract_client_from_text,
        extract_title_from_text,
    )
    from .models import Lead

    if text is None:
        if sys.stdin.isatty():
            typer.echo("Paste job text, then press Ctrl+D:", err=True)
        text = sys.stdin.read()

    title = extract_title_from_text(text)
    budget_min, budget_max = extract_budget_from_text(text)
    client_name = extract_client_from_text(text)

    lead = Lead(
        source=source,
        description=text or None,
        title=title,
        budget_min=budget_min,
        budget_max=budget_max,
        client_name=client_name,
        status=LeadStatus.NEW,
    )
    with get_session() as s:
        s.add(lead)
        s.commit()
        s.refresh(lead)
        typer.echo(lead.id)


@lead_app.command("list")
def lead_list() -> None:
    """List all leads in a readable table."""
    from sqlmodel import select

    from .db import get_session
    from .models import Lead

    with get_session() as s:
        leads = s.exec(select(Lead)).all()

    if not leads:
        typer.echo("No leads found.")
        return

    typer.echo(f"{'ID':<6} {'Source':<16} {'Title':<38} {'Status':<22} Score")
    typer.echo("-" * 90)
    for lead in leads:
        title = (lead.title or "")[:36]
        score = f"{lead.lead_score:.1f}" if lead.lead_score is not None else "-"
        typer.echo(f"{lead.id:<6} {lead.source:<16} {title:<38} {lead.status.value:<22} {score}")


@lead_app.command("show")
def lead_show(lead_id: int = typer.Argument(..., help="Lead ID")) -> None:
    """Print all stored fields for a lead."""
    from .db import get_session
    from .models import Lead

    with get_session() as s:
        lead = s.get(Lead, lead_id)

    if lead is None:
        typer.echo(f"Lead {lead_id} not found.", err=True)
        raise typer.Exit(code=1)

    for field, value in lead.model_dump().items():
        typer.echo(f"{field}: {value}")


@lead_app.command("status")
def lead_set_status(
    lead_id: int = typer.Argument(..., help="Lead ID"),
    status: str = typer.Argument(..., help="New status value"),
) -> None:
    """Set the status of a lead. Rejects invalid values with a non-zero exit."""
    from .db import get_session
    from .models import Lead

    try:
        new_status = LeadStatus(status.upper())
    except ValueError:
        valid = ", ".join(s.value for s in LeadStatus)
        typer.echo(f"Invalid status '{status}'. Valid values: {valid}", err=True)
        raise typer.Exit(code=1)

    with get_session() as s:
        lead = s.get(Lead, lead_id)
        if lead is None:
            typer.echo(f"Lead {lead_id} not found.", err=True)
            raise typer.Exit(code=1)
        lead.status = new_status
        s.add(lead)
        s.commit()

    typer.echo(f"Lead {lead_id} status → {new_status.value}")
