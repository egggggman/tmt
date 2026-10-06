"""Authenticate accepted R6-C evidence; stale controls or altered games fail closed."""

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_objective_balance_lab_round6c_results as report  # noqa: E402
import run_objective_balance_lab_round6c as run  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402

pytestmark = pytest.mark.skipif(
    identity()["aggregate_semantic_runtime_sha256"]
    != "ccfa75ed8e817bc3af0a04f75ef048aaee54e5175c06abfc21feaad6515bb0ec",
    reason="archived R6-C evidence requires the Aura semantic runtime",
)


@pytest.fixture(scope="module")
def accepted():
    authority, manifest, schedule, _ = run.preflight()
    candidate_schedule = [r for r in schedule if "krang" in r["pair"]]
    expected = run.template(authority, manifest, candidate_schedule, candidate=True)
    return run.read(run.RESULT), expected, candidate_schedule


def test_saved_analysis_and_reports_derive_from_authenticated_complete_games():
    analysis = report.build()
    assert analysis == json.loads(report.ANALYSIS.read_text())
    assert report.REPORT.read_text() == report.report(analysis)
    assert report.CONTROL_REPORT.read_text() == report.control_report(analysis)
    assert analysis["mechanism_status"] == "EXECUTED_AND_TELEMETRY_VERIFIED"
    assert not analysis["combined_validation_run"] and not analysis["promotion_authorized"]


@pytest.mark.parametrize(
    "field",
    ["semantic_runtime_sha256", "control_sha256", "candidate_sha256", "schedule_sha256"],
)
def test_candidate_rejects_changed_runtime_control_deck_or_schedule(accepted, field):
    payload, expected, schedule = accepted
    altered = deepcopy(payload)
    altered[field] = "0" * 64
    with pytest.raises(AssertionError):
        run.verify(altered, expected, schedule, complete=True)


def test_aura_target_telemetry_mutation_breaks_cell_authentication(accepted):
    payload, expected, schedule = accepted
    altered = deepcopy(payload)
    event = next(
        e for game in altered["games"] for e in game["aura_events"] if e["event"] == "aura_resolved"
    )
    event["target_id"] = "fabricated-incarnation"
    with pytest.raises(AssertionError):
        run.verify(altered, expected, schedule, complete=True)


def test_missing_replay_and_changed_opponent_manifest_are_rejected(accepted):
    payload, expected, schedule = accepted
    altered = deepcopy(payload)
    altered["replays"].pop(next(iter(altered["replays"])))
    with pytest.raises(AssertionError):
        run.verify(altered, expected, schedule, complete=True)
    altered = deepcopy(payload)
    altered["opponent_manifest"][0]["source_path"] = run.CANDIDATE
    with pytest.raises(AssertionError):
        run.verify(altered, expected, schedule, complete=True)
