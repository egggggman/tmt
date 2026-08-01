import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
from importlib.resources import files
from pathlib import Path

MIGRATION_SUFFIX = ".sql"
MIGRATION_PATTERN = re.compile(r"^(?P<number>\d{3})_[a-z0-9_]+\.sql$")


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
    scripts: list[tuple[int, str, str]] = []
    for item in root.iterdir():
        if item.name.endswith(MIGRATION_SUFFIX):
            match = MIGRATION_PATTERN.fullmatch(item.name)
            if match is None:
                raise RuntimeError(f"Invalid migration filename: {item.name}")
            scripts.append(
                (
                    int(match.group("number")),
                    item.name.removesuffix(MIGRATION_SUFFIX),
                    item.read_text("utf-8"),
                )
            )
    scripts.sort(key=lambda migration: migration[0])
    numbers = [number for number, _, _ in scripts]
    if numbers != list(range(1, len(scripts) + 1)):
        raise RuntimeError(f"Migration numbers must be unique and contiguous: {numbers}")
    return [(version, script) for _, version, script in scripts]


def initialize_database(path: str | Path) -> list[str]:
    """Apply every pending migration exactly once and return applied versions."""
    database_path = Path(path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    applied_now: list[str] = []
    with database_connection(database_path) as connection:
        for version, script in migration_scripts():
            checksum = sha256(script.encode()).hexdigest()
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
            ).fetchone()
            if exists:
                applied = connection.execute(
                    "SELECT checksum FROM schema_migrations WHERE version = ?", (version,)
                ).fetchone()
                if applied:
                    if applied["checksum"] != checksum:
                        raise RuntimeError(f"Applied migration was modified: {version}")
                    continue
            try:
                connection.executescript(f"BEGIN IMMEDIATE;\n{script}")
                connection.execute(
                    "INSERT INTO schema_migrations(version, checksum) VALUES (?, ?)",
                    (version, checksum),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            applied_now.append(version)
    return applied_now
