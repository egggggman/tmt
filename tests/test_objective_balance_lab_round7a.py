"""Authenticate saved R7-A evidence and reject altered control or replay records."""

import copy
import json

import pytest

from tools import build_objective_balance_lab_round7a_results as report
from tools import run_objective_balance_lab_round7a as run


@pytest.fixture(scope="module")
def accepted():
    authority, manifest, schedule, _ = run.preflight()
    control = run.read(run.CONTROL)
    selected = [row for row in schedule if "krang" in row["pair"]]
    candidate = run.read(run.RESULT)
    return authority, manifest, schedule, selected, control, candidate


def test_frozen_runtime_control_candidate_and_reports_match(accepted):
    authority, manifest, schedule, selected, control, candidate = accepted
    run.verify(control, run.template(authority, manifest, schedule), schedule, complete=True)
    run.verify(
        candidate,
        run.template(authority, manifest, selected, candidate=True),
        selected,
        complete=True,
    )
    analysis = report.build()
    assert analysis == json.loads(report.ANALYSIS.read_text())
    assert report.report(analysis) == report.REPORT.read_text()
    assert report.control_report(analysis) == report.CONTROL_REPORT.read_text()
    assert analysis["validation"]["candidate_replays_matched"] == 900
    assert analysis["mechanism"]["candidate"]["mutagen_counters_placed"] > 0
    assert analysis["mechanism"]["candidate"]["islandcycling_reveals"] > 0


def test_runtime_or_replay_tampering_fails_closed(accepted):
    authority, manifest, _schedule, selected, _control, candidate = accepted
    expected = run.template(authority, manifest, selected, candidate=True)
    changed = copy.deepcopy(candidate)
    changed["semantic_runtime_sha256"] = "0" * 64
    with pytest.raises(AssertionError):
        run.verify(changed, expected, selected, complete=True)
    changed = copy.deepcopy(candidate)
    key = next(iter(changed["replays"]))
    changed["replays"][key] = "0" * 64
    with pytest.raises(AssertionError):
        run.verify(changed, expected, selected, complete=True)
