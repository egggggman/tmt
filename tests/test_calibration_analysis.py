import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "docs/cardcade/CALIBRATION_V1_20260923T141649Z_3f838930291e"
SPEC = importlib.util.spec_from_file_location(
    "calibration_analysis", ROOT / "scripts/analyze_calibration_v1.py"
)
ANALYSIS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ANALYSIS)
DECKS = ANALYSIS.DECKS
wilson = ANALYSIS.wilson


def test_calibration_analysis_artifact_is_sealed_and_complete():
    artifact = RUN / "CALIBRATION_ANALYSIS_V1.json"
    sidecar = RUN / "CALIBRATION_ANALYSIS_V1.json.sha256"
    report = json.loads(artifact.read_text(encoding="utf-8"))
    expected = sidecar.read_text(encoding="ascii").split()[0]

    committed = subprocess.check_output(
        ["git", "show", f"HEAD:{artifact.relative_to(ROOT).as_posix()}"]
    )
    assert hashlib.sha256(committed).hexdigest().upper() == expected
    assert report["sample"] == {
        "authenticated_executions": 368640,
        "blocks": 2048,
        "distinct_games": 184320,
        "evidence_files": 184320,
    }
    assert set(report["deck_results"]) == set(DECKS)
    assert all(report["deck_results"][name]["draws"] == 0 for name in DECKS)
    assert report["audited_completion_audit_sha256"]
    assert report["prototype_0_3_authorized"] is False


def test_calibration_analysis_has_complete_ordered_matrix():
    report = json.loads((RUN / "CALIBRATION_ANALYSIS_V1.json").read_text(encoding="utf-8"))
    matrix = report["matchup_matrix"]

    assert set(matrix) == set(DECKS)
    assert all(set(matrix[name]) == set(DECKS) for name in DECKS)
    assert all(
        matrix[left][right]["games"] == 4096 for left in DECKS for right in DECKS if left != right
    )


def test_wilson_interval_is_bounded():
    interval = wilson(50, 100)

    assert 0 < interval["low"] < 0.5 < interval["high"] < 1


def test_canonical_reversed_aggregate_is_not_a_seat_effect_estimate():
    report = json.loads((RUN / "CALIBRATION_ANALYSIS_V1.json").read_text(encoding="utf-8"))

    assert report["orientation_interpretation"] == (
        "DECK-IDENTITY CONFOUNDED — NOT A SEAT-EFFECT ESTIMATE"
    )
    assert report["overall_first_player"]["win_rate"] == pytest.approx(0.5063856336805556)
    assert report["paired_seat_effect"]["unordered_matchup_pairs"] == 92160
    assert len(report["paired_matchup_seat_effects"]) == 45
