import sqlite3

# ruff: noqa: E501
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tmnt_design_studio.capabilities import (
    CATALOG,
    RULESET_VERSION,
    CapabilityError,
    derive_capabilities,
    effective_capabilities,
    engine_status,
    inspect_card,
)
from tmnt_design_studio.cli import app
from tmnt_design_studio.database import connect
from tmnt_design_studio.scryfall import import_scryfall

FIXTURE = Path(__file__).parent / "fixtures" / "capability-cards.json"


@pytest.fixture
def derived_database(tmp_path):
    database = tmp_path / "capabilities.db"
    import_scryfall(database, file=FIXTURE)
    derive_capabilities(database)
    return database


def snapshot(database):
    with connect(database) as connection:
        return [
            tuple(row)
            for row in connection.execute(
                "SELECT oracle_id,capability_id,rule_id,confidence FROM card_capabilities "
                "ORDER BY oracle_id,capability_id,rule_id"
            )
        ]


def capability_id(connection, identifier):
    return connection.execute(
        "SELECT id FROM capabilities WHERE identifier=?", (identifier,)
    ).fetchone()[0]


def test_catalog_is_complete_narrow_and_stable(derived_database):
    with connect(derived_database) as connection:
        rows = connection.execute(
            "SELECT identifier,name,description,category,status FROM capabilities ORDER BY identifier"
        ).fetchall()
    assert len(rows) == len(CATALOG) == 20
    assert all(
        row["identifier"] and row["description"] and row["status"] == "active" for row in rows
    )


def test_deterministic_idempotent_output_and_evidence(derived_database):
    first = snapshot(derived_database)
    first_status = engine_status(derived_database)
    second = derive_capabilities(derived_database)
    assert snapshot(derived_database) == first
    assert second["result_count"] == first_status["latest_run"]["result_count"]
    with connect(derived_database) as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM card_capabilities").fetchone()[0]
            == connection.execute(
                "SELECT COUNT(DISTINCT oracle_id || ':' || capability_id || ':' || rule_id) FROM capability_evidence"
            ).fetchone()[0]
        )


def test_multiface_and_keyword_evidence(derived_database):
    card = inspect_card(derived_database, "o-multi")
    identifiers = {item["identifier"] for item in card["capabilities"]}
    assert {"combat-support", "evasion"} <= identifiers
    combat = next(item for item in card["evidence"] if item["identifier"] == "combat-support")
    assert combat["evidence_type"] == "face"
    assert combat["face_number"] == 1


def test_negated_and_misleading_phrases_do_not_match(derived_database):
    assert inspect_card(derived_database, "o-negated")["capabilities"] == []


def test_include_exclude_and_confidence_adjustment_overrides(derived_database):
    with connect(derived_database) as connection, connection:
        ramp = capability_id(connection, "ramp")
        draw = capability_id(connection, "card-draw")
        connection.execute(
            "INSERT INTO capability_overrides(oracle_id,capability_id,action,confidence,rationale,"
            "evidence_context) VALUES ('o-token',?,'add',0.7,'Rules interaction','Mana ability confirmed')",
            (ramp,),
        )
        assert (
            next(
                x
                for x in effective_capabilities(connection, "o-token")
                if x["identifier"] == "ramp"
            )["confidence"]
            == 0.7
        )
        connection.execute(
            "INSERT INTO capability_overrides(oracle_id,capability_id,action,rationale,evidence_context) "
            "VALUES ('o-draw',?,'remove','False positive','Replacement effect applies')",
            (draw,),
        )
        assert effective_capabilities(connection, "o-draw") == []
        connection.execute("UPDATE capability_overrides SET active=0 WHERE oracle_id='o-draw'")
        connection.execute(
            "INSERT INTO capability_overrides(oracle_id,capability_id,action,rationale,evidence_context,"
            "confidence_delta) VALUES ('o-draw',?,'adjust','Edge interaction','Rules citation',-0.25)",
            (draw,),
        )
        adjusted = effective_capabilities(connection, "o-draw")[0]
        assert adjusted["confidence"] == pytest.approx(0.65)
        assert adjusted["source"] == "derived+override:adjust"


def test_conflicting_override_is_rejected_by_schema(derived_database):
    with connect(derived_database) as connection, connection:
        draw = capability_id(connection, "card-draw")
        connection.execute(
            "INSERT INTO capability_overrides(oracle_id,capability_id,action,rationale,evidence_context) "
            "VALUES ('o-draw',?,'remove','Reason','Evidence')",
            (draw,),
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO capability_overrides(oracle_id,capability_id,action,rationale,evidence_context) "
                "VALUES ('o-draw',?,'adjust','Reason','Evidence')",
                (draw,),
            )


def test_stale_results_are_replaced_after_rule_deactivation(derived_database, monkeypatch):
    import tmnt_design_studio.capabilities as module

    monkeypatch.setattr(
        module, "RULES", tuple(rule for rule in module.RULES if rule.key != "draw.instruction")
    )
    monkeypatch.setattr(module, "RULESET_VERSION", "2026.08.1-test")
    derive_capabilities(derived_database)
    assert inspect_card(derived_database, "o-draw")["capabilities"] == []


def test_failed_run_does_not_expose_partial_results(derived_database):
    before = snapshot(derived_database)
    with pytest.raises(CapabilityError, match="injected derivation failure"):
        derive_capabilities(derived_database, fail_after=2)
    assert snapshot(derived_database) == before
    assert engine_status(derived_database)["latest_run"]["status"] == "failed"


def test_status_links_ruleset_and_source_import(derived_database):
    status = engine_status(derived_database)
    assert status["ruleset_version"] == RULESET_VERSION
    assert status["latest_run"]["import_id"] == 1
    assert status["latest_run"]["import_checksum"]


def test_cli_derive_inspect_and_status(tmp_path):
    database = tmp_path / "cli.db"
    import_scryfall(database, file=FIXTURE)
    runner = CliRunner()
    derived = runner.invoke(app, ["capabilities", "derive", "--database", str(database)])
    inspected = runner.invoke(
        app, ["capabilities", "inspect", "o-wipe", "--database", str(database)]
    )
    status = runner.invoke(app, ["capabilities", "status", "--database", str(database)])
    assert derived.exit_code == inspected.exit_code == status.exit_code == 0
    assert "Scryfall import #1" in derived.stdout
    assert "board wipe" in inspected.stdout and "wipe.destroy-all" in inspected.stdout
    assert f"Rule set: {RULESET_VERSION}" in status.stdout


def test_no_forbidden_analysis_storage(derived_database):
    with connect(derived_database) as connection:
        schema = " ".join(
            row[0]
            for row in connection.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL")
        ).lower()
        assert "recommendation_score" not in schema
        assert "deck_profile" not in schema
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
