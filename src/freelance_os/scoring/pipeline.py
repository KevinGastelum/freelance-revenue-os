"""Shared score → filter → rank → render → draft → persist pipeline.

Used by both `pull` (public API fetch) and `ingest` (operator-sourced file).
"""

import json as _json
import sys
from typing import Any, Dict, List, Optional

import typer
from rich.table import Table


def score_rank_render(
    leads: List[Dict[str, Any]],
    *,
    reputation_mode: bool = True,
    min_margin: float = 0.0,
    limit: int = 20,
    emit_json: bool = False,
    draft_top: int = 3,
    persist: bool = False,
    config: Optional[str] = None,
    console,
) -> None:
    """Score, filter, rank, render (table or JSON), draft, and optionally persist a lead list.

    Raises typer.Exit(0) when the filtered list is empty or after JSON output — callers
    should not perform further work after this function returns.
    """
    from freelance_os.scoring.margin import score_lead as margin_score

    scored = []
    for lead in leads:
        s = margin_score(lead, reputation_mode=reputation_mode)
        scored.append({**lead, **s})

    if min_margin > 0:
        scored = [l for l in scored if l["margin"] >= min_margin]

    scored.sort(key=lambda l: l["final_score"], reverse=True)
    scored = scored[:limit]

    if not scored:
        console.print("[yellow]No leads passed the filter.[/yellow]")
        raise typer.Exit(0)

    if emit_json:
        sys.stdout.write(_json.dumps(scored, indent=2, ensure_ascii=False) + "\n")
        raise typer.Exit(0)

    tbl = Table(
        title=(
            f"Quick-Buck Shortlist ({len(scored)} leads, "
            f"reputation-mode={'ON' if reputation_mode else 'OFF'})"
        ),
        show_lines=False,
    )
    tbl.add_column("#", width=3, style="dim")
    tbl.add_column("Title", max_width=38)
    tbl.add_column("Source", width=12)
    tbl.add_column("$", width=8)
    tbl.add_column("~hrs", width=5)
    tbl.add_column("$/hr", width=7)
    tbl.add_column("Score", width=6)
    tbl.add_column("Verdict", max_width=40)
    tbl.add_column("URL", max_width=50, style="blue")

    for i, lead in enumerate(scored, 1):
        budget_str = f"${lead['budget_usd']:.0f}" if lead["budget_usd"] > 0 else "?"
        margin_str = f"{lead['margin']:.0f}" if lead["margin"] > 0 else "?"
        tbl.add_row(
            str(i),
            (lead.get("title") or "")[:38],
            lead.get("source", ""),
            budget_str,
            f"{lead['effort_hours']:.0f}",
            margin_str,
            f"{lead['final_score']:.2f}",
            lead.get("verdict", ""),
            lead.get("url", "")[:50],
        )

    console.print(tbl)

    if draft_top > 0 and scored:
        top = scored[:draft_top]
        console.print(f"\n[bold]Draft proposals for top {min(draft_top, len(top))} leads:[/bold]")
        try:
            cfg_path = config or "config/settings.toml"
            from freelance_os.config import load_config, ConfigError
            try:
                cfg = load_config(cfg_path)
            except ConfigError:
                cfg = {
                    "scoring": {"target_hourly_rate": 75, "minimum_project_value": 300},
                    "paths": {"portfolio_file": "config/portfolio.yaml"},
                }

            from freelance_os.models import Lead as LeadModel
            from freelance_os.proposal.draft_generator import generate_draft

            for i, lead in enumerate(top, 1):
                stub = LeadModel(
                    source=lead.get("source", "pull"),
                    source_url=lead.get("url"),
                    title=lead.get("title"),
                    description=(lead.get("description") or "")[:4000],
                )
                draft = generate_draft(stub, cfg)
                console.print(
                    f"\n[bold cyan]--- Draft #{i}: {lead.get('title', '')[:60]} ---[/bold cyan]"
                )
                console.print(draft["draft_text"])
        except Exception as exc:
            console.print(f"[yellow]Draft generation skipped:[/yellow] {exc}")

    if persist:
        try:
            cfg_path = config or "config/settings.toml"
            from freelance_os.config import load_config, ConfigError
            from freelance_os.db import get_engine, create_tables
            from freelance_os.models import Lead as LeadModel
            from sqlmodel import Session, select

            try:
                cfg = load_config(cfg_path)
            except ConfigError:
                cfg = {"paths": {"database_path": "data/freelance_os.sqlite"}}

            db_path = cfg["paths"]["database_path"]
            engine = get_engine(db_path)
            create_tables(engine, db_path)

            saved = 0
            with Session(engine) as session:
                for lead in scored:
                    url = lead.get("url") or ""
                    if url:
                        existing = session.exec(
                            select(LeadModel).where(LeadModel.source_url == url)
                        ).first()
                        if existing:
                            continue
                    stub = LeadModel(
                        source=lead.get("source", "pull"),
                        source_url=url or None,
                        title=lead.get("title"),
                        description=(lead.get("description") or "")[:4000],
                        budget_min=lead.get("budget_usd") or None,
                        notes=lead.get("verdict"),
                    )
                    session.add(stub)
                    saved += 1
                session.commit()
            console.print(f"[green]Persisted {saved} new leads to {db_path}[/green]")
        except Exception as exc:
            console.print(f"[yellow]Persist skipped:[/yellow] {exc}")
