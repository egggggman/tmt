import sqlite3
from hashlib import sha256

import pytest
from typer.testing import CliRunner

from tmnt_design_studio import database
from tmnt_design_studio.cli import app
from tmnt_design_studio.database import connect, initialize_database, migration_scripts

EXPECTED_TABLES = {
    "schema_migrations",
    "metadata",
    "imports",
    "cards",
    "card_printings",
    "card_faces",
    "legalities",
    "keywords",
    "card_keywords",
    "types",
    "card_types",
    "subtypes",
    "card_subtypes",
    "capabilities",
    "capability_rules",
    "card_capabilities",
    "capability_overrides",
    "characters",
    "design_intents",
    "themes",
    "design_intent_themes",
    "theme_capabilities",
    "design_intent_capabilities",
    "experience_goals",
    "decks",
    "deck_versions",
    "deck_cards",
    "design_notes",
    "design_decisions",
    "card_relationships",
    "design_sessions",
    "playtest_sessions",
    "playtest_observations",
}


def test_fresh_database_initializes(tmp_path):
    path = tmp_path / "sewer-graph.db"

    applied = initialize_database(path)

    assert applied == [version for version, _ in migration_scripts()]
    with connect(path) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        recorded = connection.execute(
            "SELECT version, checksum FROM schema_migrations ORDER BY version"
        ).fetchall()
        assert [row[0] for row in recorded] == applied
        expected_checksums = {
            version: sha256(script.encode()).hexdigest()
            for version, script in migration_scripts()
        }
        assert {row[0]: row[1] for row in recorded} == expected_checksums
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert tables == EXPECTED_TABLES
        assert not tables & {"deck_profiles", "recommendations", "recommendation_scores"}


def test_initialization_is_idempotent(tmp_path):
    path = tmp_path / "sewer-graph.db"
    expected = initialize_database(path)

    assert initialize_database(path) == []
    with connect(path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
        assert count == len(expected)


def test_cli_init_is_idempotent(tmp_path):
    path = tmp_path / "nested" / "directory" / "cli.db"
    runner = CliRunner()

    first = runner.invoke(app, ["init", str(path)])
    second = runner.invoke(app, ["init", str(path)])

    assert first.exit_code == 0
    assert "9 migration(s) applied" in first.stdout
    assert second.exit_code == 0
    assert "already current" in second.stdout
    assert path.is_file()


def test_foreign_keys_reject_invalid_relationship(tmp_path):
    path = tmp_path / "foreign-keys.db"
    initialize_database(path)

    with connect(path) as connection, connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO design_intents(character_id, name, description) "
            "VALUES (999, 'Missing', 'Invalid')"
        )


def test_constraints_and_deck_version_history(tmp_path):
    path = tmp_path / "constraints.db"
    initialize_database(path)

    with connect(path) as connection, connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO imports(source, status, imported_count) VALUES ('scryfall', 'bad', 0)"
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO imports(source, status, imported_count) "
                "VALUES ('scryfall', 'running', -1)"
            )
        connection.execute(
            "INSERT INTO characters(id, name, kind) VALUES (1, 'Leonardo', 'character')"
        )
        connection.execute(
            "INSERT INTO design_intents(id, character_id, name, description) "
            "VALUES (1, 1, 'Leader', 'Lead with discipline')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO design_intents(character_id, name, description) "
                "VALUES (1, 'Leader', 'Duplicate')"
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO decks(design_intent_id, name, format) "
                "VALUES (1, 'Wrong format', 'modern')"
            )
        connection.execute(
            "INSERT INTO decks(id, design_intent_id, name) VALUES (1, 1, 'Sewer Deck')"
        )
        connection.execute(
            "INSERT INTO deck_versions(id, deck_id, version_label, status) "
            "VALUES (1, 1, 'v1', 'draft')"
        )
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute("UPDATE deck_versions SET notes = 'changed' WHERE id = 1")
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute("DELETE FROM deck_versions WHERE id = 1")


def test_failed_migration_rolls_back_and_is_not_recorded(tmp_path, monkeypatch):
    path = tmp_path / "rollback.db"
    original = migration_scripts()
    broken = original + [("010_broken", "CREATE TABLE should_rollback(id); INVALID SQL;")]
    monkeypatch.setattr(database, "migration_scripts", lambda: broken)

    with pytest.raises(sqlite3.OperationalError):
        initialize_database(path)

    with connect(path) as connection:
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='should_rollback'"
        ).fetchone() is None
        assert connection.execute(
            "SELECT 1 FROM schema_migrations WHERE version='010_broken'"
        ).fetchone() is None


def test_applied_migration_checksum_is_verified(tmp_path, monkeypatch):
    path = tmp_path / "checksum.db"
    initialize_database(path)
    scripts = migration_scripts()
    changed = [(scripts[0][0], scripts[0][1] + "\n-- modified")] + scripts[1:]
    monkeypatch.setattr(database, "migration_scripts", lambda: changed)

    with pytest.raises(RuntimeError, match="Applied migration was modified"):
        initialize_database(path)
