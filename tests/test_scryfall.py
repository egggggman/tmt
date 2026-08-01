import json
import os
from hashlib import sha256
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tmnt_design_studio.cli import app
from tmnt_design_studio.database import connect
from tmnt_design_studio.scryfall import ScryfallImportError, import_scryfall

FIXTURE = Path(__file__).parent / "fixtures" / "scryfall-default-cards.json"


def counts(database):
    with connect(database) as connection:
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
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
            )
        }


def test_fresh_fixture_import_normalizes_facts_and_audit(tmp_path):
    database = tmp_path / "sewer-graph.db"

    summary = import_scryfall(database, file=FIXTURE)

    assert summary.processed_count == 4
    assert summary.oracle_count == 3
    assert summary.printing_count == 4
    assert summary.standard_legal_count == 2
    assert summary.checksum == sha256(FIXTURE.read_bytes()).hexdigest()
    assert counts(database) == {
        "cards": 3,
        "card_printings": 4,
        "card_faces": 2,
        "legalities": 3,
        "keywords": 2,
        "card_keywords": 2,
        "types": 2,
        "card_types": 3,
        "subtypes": 3,
        "card_subtypes": 3,
    }
    with connect(database) as connection:
        faces = connection.execute(
            "SELECT face_number, name FROM card_faces WHERE oracle_id='oracle-gamma' "
            "ORDER BY face_number"
        ).fetchall()
        assert [tuple(row) for row in faces] == [(0, "Mutate"), (1, "Mobilize")]
        legality_counts = dict(
            connection.execute(
                "SELECT legality, COUNT(*) FROM legalities GROUP BY legality ORDER BY legality"
            )
        )
        assert legality_counts == {"legal": 2, "not_legal": 1}
        audit = connection.execute(
            "SELECT * FROM imports WHERE id=?", (summary.import_id,)
        ).fetchone()
        assert audit["status"] == "succeeded"
        assert audit["processed_count"] == 4
        assert audit["imported_count"] == 3
        assert audit["checksum"] == summary.checksum
        assert audit["completed_at"]
        assert json.loads(audit["source_metadata"])["type"] == "local_fixture"


def test_repeated_import_is_idempotent(tmp_path):
    database = tmp_path / "sewer-graph.db"
    first = import_scryfall(database, file=FIXTURE)
    expected_counts = counts(database)

    second = import_scryfall(database, file=FIXTURE)

    assert counts(database) == expected_counts
    assert first.checksum == second.checksum
    with connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM imports").fetchone()[0] == 2


def test_changed_source_updates_canonical_facts_and_relationships(tmp_path):
    database = tmp_path / "sewer-graph.db"
    changed_file = tmp_path / "changed.json"
    records = json.loads(FIXTURE.read_text("utf-8"))
    records[0]["name"] = records[1]["name"] = "Sewer Pathfinder"
    records[0]["keywords"] = records[1]["keywords"] = ["Reach"]
    records[0]["legalities"]["standard"] = "banned"
    records[1]["legalities"]["standard"] = "banned"
    changed_file.write_text(json.dumps(records), "utf-8")
    import_scryfall(database, file=FIXTURE)

    import_scryfall(database, file=changed_file)

    with connect(database) as connection:
        assert (
            connection.execute("SELECT name FROM cards WHERE oracle_id='oracle-alpha'").fetchone()[
                0
            ]
            == "Sewer Pathfinder"
        )
        assert (
            connection.execute(
                "SELECT legality FROM legalities WHERE oracle_id='oracle-alpha'"
            ).fetchone()[0]
            == "banned"
        )
        keywords = connection.execute(
            "SELECT k.name FROM keywords k JOIN card_keywords ck ON ck.keyword_id=k.id "
            "WHERE ck.oracle_id='oracle-alpha'"
        ).fetchall()
        assert [row[0] for row in keywords] == ["Reach"]


@pytest.mark.parametrize(
    "payload, message",
    [
        (b"not json", "Malformed Scryfall JSON"),
        (b"[]", "contains no records"),
        (
            json.dumps(
                [
                    {
                        "id": "duplicate",
                        "oracle_id": "one",
                        "name": "One",
                        "type_line": "Instant",
                        "set": "tst",
                        "collector_number": "1",
                        "rarity": "common",
                        "legalities": {"standard": "legal"},
                    },
                    {
                        "id": "duplicate",
                        "oracle_id": "two",
                        "name": "Two",
                        "type_line": "Instant",
                        "set": "tst",
                        "collector_number": "2",
                        "rarity": "common",
                        "legalities": {"standard": "legal"},
                    },
                ]
            ).encode(),
            "Duplicate Scryfall id",
        ),
    ],
)
def test_malformed_input_fails_clearly_and_records_failure(tmp_path, payload, message):
    database = tmp_path / "sewer-graph.db"
    source = tmp_path / "bad.json"
    source.write_bytes(payload)

    with pytest.raises(ScryfallImportError, match=message):
        import_scryfall(database, file=source)

    assert counts(database)["cards"] == 0
    with connect(database) as connection:
        audit = connection.execute("SELECT status, error, error_count FROM imports").fetchone()
        assert audit["status"] == "failed"
        assert message in audit["error"]
        assert audit["error_count"] == 1


def test_failed_fact_transaction_leaves_previous_snapshot_consistent(tmp_path, monkeypatch):
    database = tmp_path / "sewer-graph.db"
    import_scryfall(database, file=FIXTURE)
    before = counts(database)

    import tmnt_design_studio.scryfall as module

    original = module._upsert_vocabulary

    def fail_on_types(connection, table, relationship, oracle_id, values):
        if table == "types":
            raise RuntimeError("injected transactional failure")
        return original(connection, table, relationship, oracle_id, values)

    monkeypatch.setattr(module, "_upsert_vocabulary", fail_on_types)
    with pytest.raises(ScryfallImportError, match="injected transactional failure"):
        import_scryfall(database, file=FIXTURE)

    assert counts(database) == before
    with connect(database) as connection:
        assert (
            connection.execute("SELECT status FROM imports ORDER BY id DESC LIMIT 1").fetchone()[0]
            == "failed"
        )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_cli_import_and_database_status(tmp_path):
    database = tmp_path / "cli.db"
    runner = CliRunner()

    imported = runner.invoke(
        app, ["import", "scryfall", "--database", str(database), "--file", str(FIXTURE)]
    )
    status = runner.invoke(app, ["database", "status", "--database", str(database)])

    assert imported.exit_code == 0, imported.stdout
    assert "3 Oracle cards, 4 printings, 2 Standard-legal cards" in imported.stdout
    assert status.exit_code == 0, status.stdout
    assert "Schema: 10/10 migrations applied" in status.stdout
    assert "Latest Scryfall import: #1 succeeded" in status.stdout


@pytest.mark.skipif(
    os.environ.get("TMNT_SCRYFALL_SMOKE") != "1",
    reason="set TMNT_SCRYFALL_SMOKE=1 for opt-in live endpoint validation",
)
def test_live_scryfall_bulk_metadata_compatibility():
    from tmnt_design_studio.scryfall import BULK_DATA_URL, _request_json

    metadata = _request_json(BULK_DATA_URL)
    default_cards = next(entry for entry in metadata["data"] if entry["type"] == "default_cards")
    assert default_cards["download_uri"].startswith("https://")
    assert default_cards["updated_at"]
