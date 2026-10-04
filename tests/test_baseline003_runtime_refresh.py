"""Fail-closed identity and schedule checks for the new-runtime control refresh."""

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_baseline003_runtime_refresh_report as report  # noqa: E402
import run_objective_balance_lab_baseline003_runtime_refresh as run  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402


def test_preflight_keeps_exact_baseline003_decks_and_frozen_schedule():
    # The Chrome-Dome-era gate remains closed after the Aura runtime change.
    with pytest.raises(AssertionError):
        run.preflight()
    manifest = json.loads(run.MANIFEST.read_text())
    schedule = run.r1.schedule()
    paths = {row["deck_key"]: row["source_path"] for row in manifest["decks"]}
    runtime = run.identity(run.BASE)
    for row in manifest["decks"]:
        run.verify_deck(row)
    assert manifest["environment_id"] == "OBL-BASELINE-003"
    assert len(paths) == 10 and all("R6_B" not in path for path in paths.values())
    assert len(schedule) == 4500
    assert runtime["aggregate_semantic_runtime_sha256"] == run.RUNTIME != run.OLD_RUNTIME


def test_checkpoint_fails_closed_on_runtime_manifest_and_schedule_drift():
    manifest = json.loads(run.MANIFEST.read_text())
    schedule, runtime = run.r1.schedule(), run.identity(run.BASE)
    expected = run.checkpoint_template(manifest, runtime)
    run.verify_checkpoint(expected, expected, schedule)
    for field, bad in (
        ("semantic_runtime_sha256", run.OLD_RUNTIME),
        ("schedule_sha256", "0" * 64),
        ("baseline_manifest_sha256", "0" * 64),
        ("evidence_id", "OTHER"),
    ):
        altered = deepcopy(expected)
        altered[field] = bad
        with pytest.raises(AssertionError):
            run.verify_checkpoint(altered, expected, schedule)


def test_historical_matrix_self_comparison_has_no_cell_change():
    historical = json.loads(run.HISTORICAL.read_text(encoding="utf-8"))
    games = historical["combined_games"]
    rows = report.compare_cells(games, games)
    assert len(rows) == 45
    assert all(not row["cell_result_changed"] for row in rows)
    assert all(row["outcome_changed_games"] == 0 for row in rows)


def test_cell_fingerprint_survives_json_integer_turn_key_round_trip():
    raw = [{"battlefield_presence": {"krang": {1: 2, 3: 1, 11: 4}}, "winner": "krang"}]
    loaded = json.loads(json.dumps(raw))
    assert r5.digest(raw) != r5.digest(loaded)
    assert run.original_cell_fingerprint(loaded) == r5.digest(raw)
