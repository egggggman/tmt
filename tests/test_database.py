import sqlite3

import pytest
from typer.testing import CliRunner

from tmnt_design_studio.cli import app
from tmnt_design_studio.database import connect, initialize_database, migration_scripts


def test_fresh_database_initializes(tmp_path):
    path = tmp_path / "sewer-graph.db"

    applied = initialize_database(path)

    assert applied == [version for version, _ in migration_scripts()]
    with connect(path) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        recorded = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        assert [row[0] for row in recorded] == applied
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert {"characters", "design_intents", "decks", "deck_versions"} <= tables


def test_initialization_is_idempotent(tmp_path):
    path = tmp_path / "sewer-graph.db"
    expected = initialize_database(path)

    assert initialize_database(path) == []
    with connect(path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
        assert count == len(expected)


def test_cli_init_is_idempotent(tmp_path):
    path = tmp_path / "cli.db"
    runner = CliRunner()

    first = runner.invoke(app, ["init", str(path)])
    second = runner.invoke(app, ["init", str(path)])

    assert first.exit_code == 0
    assert "9 migration(s) applied" in first.stdout
    assert second.exit_code == 0
    assert "already current" in second.stdout


def test_foreign_keys_reject_invalid_relationship(tmp_path):
    path = tmp_path / "foreign-keys.db"
    initialize_database(path)

    with connect(path) as connection, connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO design_intents(character_id, name, description) "
            "VALUES (999, 'Missing', 'Invalid')"
        )
