import json

# ruff: noqa: E501
from pathlib import Path

import pytest
from typer.testing import CliRunner

import tmnt_design_studio.deck_analysis as module
from tmnt_design_studio.capabilities import derive_capabilities
from tmnt_design_studio.cli import app
from tmnt_design_studio.database import connect
from tmnt_design_studio.deck_analysis import (
    DeckAnalysisError,
    analysis_status,
    analyze_deck,
    inspect_deck,
)
from tmnt_design_studio.scryfall import import_scryfall

FIXTURE = Path(__file__).parent / "fixtures" / "deck-analysis-cards.json"


@pytest.fixture
def deck_database(tmp_path):
    database = tmp_path / "deck-analysis.db"
    import_scryfall(database, file=FIXTURE)
    derive_capabilities(database)
    with connect(database) as connection, connection:
        connection.execute(
            "INSERT INTO characters(id,name,kind,description) VALUES (1,'Fixture Subject','character','Test fixture only')"
        )
        connection.execute(
            "INSERT INTO design_intents(id,character_id,name,description) VALUES (1,1,'Fixture Intent','Schema prerequisite only')"
        )
        connection.execute(
            "INSERT INTO decks(id,design_intent_id,name) VALUES (1,1,'Neutral Fixture Deck')"
        )
        connection.execute(
            "INSERT INTO deck_versions(id,deck_id,version_label,status) VALUES (1,1,'v1','testing')"
        )
        quantities = {"o-plains": 12, "o-island": 12}
        quantities.update(
            {
                oracle_id: 4
                for oracle_id in (
                    "o-draw",
                    "o-negated",
                    "o-wipe",
                    "o-removal",
                    "o-multi",
                    "o-token",
                    "o-rock",
                    "o-guard",
                    "o-finish",
                )
            }
        )
        connection.executemany(
            "INSERT INTO deck_cards(deck_version_id,oracle_id,section,quantity) VALUES (1,?,'main',?)",
            quantities.items(),
        )
    return database


def _metric(result, key):
    return result["metrics"][key]["value"]


def test_metrics_are_deterministic_complete_and_evidence_backed(deck_database):
    first = analyze_deck(deck_database, 1)
    first_result = inspect_deck(deck_database, 1)
    second = analyze_deck(deck_database, 1)
    second_result = inspect_deck(deck_database, 1)

    assert first["run_id"] != second["run_id"]
    assert first["deck_checksum"] == second["deck_checksum"]
    assert first_result["metrics"] == second_result["metrics"]
    assert _metric(second_result, "total_card_count") == 60
    assert _metric(second_result, "unique_oracle_card_count") == 11
    assert _metric(second_result, "land_count") == 24
    assert set(_metric(second_result, "capability_totals")) == set(module.CAPABILITY_IDS)
    assert _metric(second_result, "capability_totals")["card-draw"]["copy_count"] == 4
    assert _metric(second_result, "capability_totals")["board-wipe"]["copy_count"] == 4
    assert all(finding["metric_key"] for finding in second_result["findings"])
    assert all(finding["threshold_json"] for finding in second_result["findings"])


def test_multiface_negated_text_and_conservative_mana_sources(deck_database):
    analyze_deck(deck_database, 1)
    result = inspect_deck(deck_database, 1)
    capabilities = _metric(result, "capability_totals")
    assert capabilities["card-draw"]["copy_count"] == 4
    assert capabilities["evasion"]["copy_count"] == 4
    assert capabilities["combat-support"]["copy_count"] == 4
    production = _metric(result, "land_color_production")
    assert production["W"]["unrestricted"] == 12
    assert production["U"]["unrestricted"] == 12
    availability = _metric(result, "mana_source_availability")
    assert availability["W"]["nonland_fixing_copies"] == 4


def test_strict_validation_and_diagnostic_mode(deck_database):
    with connect(deck_database) as connection, connection:
        connection.execute(
            "INSERT INTO deck_versions(id,deck_id,version_label,status) VALUES (2,1,'v2','draft')"
        )
        connection.execute("INSERT INTO deck_cards VALUES (2,'o-plains','main',59)")
    with pytest.raises(DeckAnalysisError, match="exactly 60"):
        analyze_deck(deck_database, 2)
    result = analyze_deck(deck_database, 2, diagnostic=True)
    assert result["warnings"] == ["Main deck has 59 cards; Version 1 requires exactly 60"]

    with connect(deck_database) as connection, connection:
        connection.execute(
            "INSERT INTO deck_versions(id,deck_id,version_label,status) VALUES (3,1,'v3','draft')"
        )
        connection.execute("INSERT INTO deck_cards VALUES (3,'o-plains','main',8)")
    result = analyze_deck(deck_database, 3, diagnostic=True)
    assert result["warnings"] == ["Main deck has 8 cards; Version 1 requires exactly 60"]


def test_rejects_stale_capability_data(deck_database):
    import_scryfall(deck_database, file=FIXTURE)
    with pytest.raises(DeckAnalysisError, match="stale"):
        analyze_deck(deck_database, 1)


def test_failed_run_is_audited_without_partial_or_current_replacement(deck_database):
    successful = analyze_deck(deck_database, 1)
    with pytest.raises(DeckAnalysisError, match="injected"):
        analyze_deck(deck_database, 1, fail_after_metrics=True)
    with connect(deck_database) as connection:
        failed = connection.execute(
            "SELECT * FROM deck_analysis_runs WHERE status='failed' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert failed["error"] == "injected deck analysis failure"
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM deck_analysis_metrics WHERE run_id=?", (failed["id"],)
            ).fetchone()[0]
            == 0
        )
        assert (
            connection.execute(
                "SELECT run_id FROM current_deck_analyses WHERE deck_version_id=1"
            ).fetchone()[0]
            == successful["run_id"]
        )


def test_engine_change_replaces_stale_current_result(deck_database, monkeypatch):
    old = analyze_deck(deck_database, 1)
    monkeypatch.setattr(module, "ENGINE_VERSION", "2026.08.1")
    new = analyze_deck(deck_database, 1)
    assert new["run_id"] != old["run_id"]
    assert new["engine_checksum"] != old["engine_checksum"]
    with connect(deck_database) as connection:
        assert (
            connection.execute(
                "SELECT run_id FROM current_deck_analyses WHERE deck_version_id=1"
            ).fetchone()[0]
            == new["run_id"]
        )


def test_status_and_cli_identify_all_provenance(deck_database):
    result = analyze_deck(deck_database, 1)
    status = analysis_status(deck_database)
    assert status["latest_run"]["import_id"] == result["import_id"]
    assert status["latest_run"]["capability_run_id"] == result["capability_run_id"]
    runner = CliRunner()
    inspected = runner.invoke(app, ["deck", "inspect", "1", "-d", str(deck_database)])
    reported = runner.invoke(app, ["deck", "status", "-d", str(deck_database)])
    assert inspected.exit_code == reported.exit_code == 0
    assert "Scryfall import" in inspected.stdout and "Capability run" in inspected.stdout
    assert module.ENGINE_VERSION in reported.stdout


def test_analysis_layer_contains_no_character_or_recommendation_logic():
    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    prohibited = ("character_id", "design_intent", "deck profile", "recommendation", "theme score")
    assert not any(term in source for term in prohibited)


def test_persisted_json_and_foreign_keys(deck_database):
    analyze_deck(deck_database, 1)
    with connect(deck_database) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        rows = connection.execute(
            "SELECT value_json,evidence_json FROM deck_analysis_metrics"
        ).fetchall()
    assert all(json.loads(row["value_json"]) is not None for row in rows)
    assert all(json.loads(row["evidence_json"]) is not None for row in rows)
