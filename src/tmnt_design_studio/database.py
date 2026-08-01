import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import files
from pathlib import Path

MIGRATION_SUFFIX = ".sql"


def connect(path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with integrity settings enabled."""
    connection = sqlite3.connect(Path(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        connection.close()
        raise RuntimeError("SQLite foreign key enforcement could not be enabled")
    return connection


@contextmanager
def database_connection(path: str | Path) -> Iterator[sqlite3.Connection]:
    connection = connect(path)
    try:
        yield connection
    finally:
        connection.close()


def migration_scripts() -> list[tuple[str, str]]:
    root = files("tmnt_design_studio").joinpath("migrations")
    scripts = []
    for item in sorted(root.iterdir(), key=lambda entry: entry.name):
        if item.name.endswith(MIGRATION_SUFFIX):
            scripts.append((item.name.removesuffix(MIGRATION_SUFFIX), item.read_text("utf-8")))
    return scripts


def initialize_database(path: str | Path) -> list[str]:
    """Apply every pending migration exactly once and return applied versions."""
    database_path = Path(path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    applied_now: list[str] = []
    with database_connection(database_path) as connection:
        for version, script in migration_scripts():
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
            ).fetchone()
            if exists and connection.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?", (version,)
            ).fetchone():
                continue
            try:
                connection.executescript(f"BEGIN IMMEDIATE;\n{script}")
                connection.execute(
                    "INSERT INTO schema_migrations(version) VALUES (?)", (version,)
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            applied_now.append(version)
    return applied_now

