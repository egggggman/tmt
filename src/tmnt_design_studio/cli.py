from pathlib import Path
from typing import Annotated

import typer

from tmnt_design_studio.capabilities import (
    CapabilityError,
    derive_capabilities,
    engine_status,
    inspect_card,
)
from tmnt_design_studio.database import connect, initialize_database, migration_scripts
from tmnt_design_studio.scryfall import ScryfallImportError, import_scryfall

app = typer.Typer(no_args_is_help=True, help="TMNT Design Studio tools.")
import_app = typer.Typer(no_args_is_help=True, help="Import objective source facts.")
database_app = typer.Typer(no_args_is_help=True, help="Inspect SewerGraph.")
capability_app = typer.Typer(no_args_is_help=True, help="Derive and inspect card capabilities.")
app.add_typer(import_app, name="import")
app.add_typer(database_app, name="database")
app.add_typer(capability_app, name="capabilities")


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


@import_app.command("scryfall")
def import_scryfall_command(
    database: Annotated[
        Path, typer.Option("--database", "-d", help="SewerGraph database path.")
    ] = Path("tmnt-design-studio.db"),
    file: Annotated[
        Path | None, typer.Option("--file", help="Local JSON, gzip, or ZIP fixture/bulk file.")
    ] = None,
    bulk_type: Annotated[
        str, typer.Option("--bulk-type", help="Scryfall bulk data type when downloading.")
    ] = "default_cards",
) -> None:
    """Import objective card facts from Scryfall bulk data."""
    try:
        summary = import_scryfall(database, file=file, bulk_type=bulk_type)
    except ScryfallImportError as error:
        typer.echo(f"Scryfall import failed: {error}", err=True)
        raise typer.Exit(1) from error
    typer.echo(
        f"Scryfall import #{summary.import_id} succeeded: "
        f"{summary.oracle_count} Oracle cards, {summary.printing_count} printings, "
        f"{summary.standard_legal_count} Standard-legal cards; "
        f"checksum {summary.checksum[:12]}…, {summary.warning_count} warning(s)."
    )


@database_app.command("status")
def database_status(
    database: Annotated[
        Path, typer.Option("--database", "-d", help="SewerGraph database path.")
    ] = Path("tmnt-design-studio.db"),
) -> None:
    """Report schema and latest Scryfall import status."""
    if not database.is_file():
        typer.echo(f"Database does not exist: {database}", err=True)
        raise typer.Exit(1)
    with connect(database) as connection:
        applied = connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
        latest = connection.execute(
            "SELECT id, status, imported_count, processed_count, checksum, completed_at, error "
            "FROM imports WHERE source='scryfall' ORDER BY id DESC LIMIT 1"
        ).fetchone()
    typer.echo(f"SewerGraph: {database}")
    typer.echo(f"Schema: {applied}/{len(migration_scripts())} migrations applied")
    if latest is None:
        typer.echo("Latest Scryfall import: none")
    else:
        checksum = latest["checksum"][:12] + "…" if latest["checksum"] else "unavailable"
        typer.echo(
            f"Latest Scryfall import: #{latest['id']} {latest['status']}; "
            f"{latest['imported_count']} Oracle cards/{latest['processed_count']} printings; "
            f"checksum {checksum}; completed {latest['completed_at'] or 'not completed'}"
        )
        if latest["error"]:
            typer.echo(f"Error: {latest['error']}")


@capability_app.command("derive")
def capability_derive(
    database: Annotated[Path, typer.Option("--database", "-d")] = Path("tmnt-design-studio.db"),
) -> None:
    """Replace current derived results using the active versioned rule set."""
    try:
        summary = derive_capabilities(database)
    except CapabilityError as error:
        typer.echo(f"Capability derivation failed: {error}", err=True)
        raise typer.Exit(1) from error
    typer.echo(
        f"Capability run #{summary['run_id']} succeeded: {summary['card_count']} cards, "
        f"{summary['result_count']} rule results, {summary['evidence_count']} evidence records; "
        f"rules {summary['ruleset_version']}, Scryfall import #{summary['import_id']}."
    )


@capability_app.command("inspect")
def capability_inspect(
    card: Annotated[str, typer.Argument(help="Oracle ID or exact card name.")],
    database: Annotated[Path, typer.Option("--database", "-d")] = Path("tmnt-design-studio.db"),
) -> None:
    """Explain the effective capabilities and evidence for one Oracle card."""
    try:
        result = inspect_card(database, card)
    except CapabilityError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    typer.echo(f"{result['name']} ({result['oracle_id']})")
    for capability in result["capabilities"]:
        typer.echo(
            f"- {capability['name']}: {capability['confidence']:.2f} ({capability['source']})"
        )
    for evidence in result["evidence"]:
        face = f" face {evidence['face_number']}" if evidence["face_number"] is not None else ""
        typer.echo(
            f"  evidence {evidence['rule_key']}{face}: {evidence['source_field']} "
            f"matched {evidence['matched_value']!r}"
        )


@capability_app.command("status")
def capability_status(
    database: Annotated[Path, typer.Option("--database", "-d")] = Path("tmnt-design-studio.db"),
) -> None:
    """Report the active rules and latest source-linked derivation run."""
    status = engine_status(database)
    typer.echo(f"Rule set: {status['ruleset_version']} ({status['rules_checksum'][:12]}...)")
    run = status["latest_run"]
    if run is None:
        typer.echo("Latest capability run: none")
        return
    typer.echo(
        f"Latest capability run: #{run['id']} {run['status']}; Scryfall import "
        f"#{run['import_id']} checksum {(run['import_checksum'] or 'unavailable')[:12]}; "
        f"{run['card_count']} cards/{run['result_count']} results"
    )
    for capability, count in status["counts"].items():
        typer.echo(f"- {capability}: {count}")
