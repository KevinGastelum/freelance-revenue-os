import shutil
from pathlib import Path

import typer

from freelance_os.config import SafetyConfigError, load_config

app = typer.Typer(
    name="freelance-os",
    help="Freelance Revenue OS — AI prepares, human commits.",
    add_completion=False,
    no_args_is_help=True,
)

_DEFAULT_CONFIG_PATH = Path("config/settings.toml")
_EXAMPLE_CONFIG_PATH = Path("config/settings.example.toml")


@app.callback()
def _main() -> None:
    """Freelance Revenue OS — AI prepares, human commits."""


@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Overwrite existing settings.toml from example."),
) -> None:
    """Initialize the database and configuration for freelance-os."""
    try:
        cfg = load_config(_DEFAULT_CONFIG_PATH)
    except SafetyConfigError as exc:
        typer.echo(f"Safety error: {exc}", err=True)
        raise typer.Exit(code=1)

    db_path = Path(cfg["paths"]["database_path"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Copy example config only if absent (or forced)
    if not _DEFAULT_CONFIG_PATH.exists():
        if _EXAMPLE_CONFIG_PATH.exists():
            shutil.copy(_EXAMPLE_CONFIG_PATH, _DEFAULT_CONFIG_PATH)
            typer.echo(f"Created {_DEFAULT_CONFIG_PATH} from example.")
        else:
            typer.echo(f"Note: {_DEFAULT_CONFIG_PATH} not found — using safe defaults.")
    elif force:
        if _EXAMPLE_CONFIG_PATH.exists():
            shutil.copy(_EXAMPLE_CONFIG_PATH, _DEFAULT_CONFIG_PATH)
            typer.echo(f"Overwrote {_DEFAULT_CONFIG_PATH} from example (--force).")
        else:
            typer.echo(f"Note: {_EXAMPLE_CONFIG_PATH} not found; {_DEFAULT_CONFIG_PATH} unchanged.")

    from freelance_os.db import create_tables, get_engine

    engine = get_engine(str(db_path))
    table_count = create_tables(engine)

    typer.echo(f"Database : {db_path}")
    typer.echo(f"Tables   : {table_count}")
    typer.echo("Status   : OK")
