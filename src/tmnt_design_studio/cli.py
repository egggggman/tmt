from pathlib import Path
from typing import Annotated

import typer

from tmnt_design_studio.database import initialize_database

app = typer.Typer(no_args_is_help=True, help="TMNT Design Studio tools.")


@app.callback()
def main() -> None:
    """Store facts, compute intelligence, and preserve decisions."""


@app.command()
def init(
    database: Annotated[
        Path,
        typer.Argument(help="SQLite database to initialize."),
    ] = Path("tmnt-design-studio.db"),
) -> None:
    """Initialize or update a SewerGraph database."""
    applied = initialize_database(database)
    if applied:
        typer.echo(f"Initialized {database} ({len(applied)} migration(s) applied).")
    else:
        typer.echo(f"Database {database} is already current.")
