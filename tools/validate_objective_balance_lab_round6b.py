"""Fail-closed validation of Krang R6-B and its new-runtime control."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import build_objective_balance_lab_round5_results as summarize  # noqa: E402
import build_objective_balance_lab_round6b_results as report  # noqa: E402
import run_objective_balance_lab_round6b as r6b  # noqa: E402


def validate() -> dict:
    manifest, isolated, _paths, control = r6b.preflight()
    checkpoint = json.loads(r6b.CHECKPOINT.read_text(encoding="utf-8"))
    evidence = json.loads(r6b.EVIDENCE.read_text(encoding="utf-8"))
    assert checkpoint == evidence
    r6b.verify(evidence, r6b.template(manifest, isolated), isolated)
    assert evidence["completed_games"] == evidence["replayed_games"] == 900
    assert evidence["runtime_errors"] == 0
    assert len(evidence["cells"]) == 9
    assert set(evidence["cells"]) == set(summarize.r1.DECKS) - {"krang"}
    assert (
        sum(game["first_player"] == "krang" for cell in evidence["cells"].values() for game in cell)
        == 450
    )
    games = [game for cell in evidence["cells"].values() for game in cell]
    assert all(game["seats"][0] == "krang" or game["seats"][1] == "krang" for game in games)
    assert all(not game["runtime_error"] and game["runtime_fingerprint"] for game in games)
    assert all(game["schedule"]["seed"] is not None for game in games)
    results = evidence["results"]
    assert results["runtime_errors"] == 0
    assert results["replay_verified_games"] == 900
    assert results["promotion_authorized"] is False
    assert results["hypothesis_result"] == report.HYPOTHESIS
    assert results["cardcade_verdict"] == report.VERDICT
    assert results["identity_classification"] == report.IDENTITY
    assert results["comparison"] == summarize.comparison(
        summarize.summarize(control["games"], "krang"),
        summarize.summarize(games, "krang"),
    )
    assert results["chrome_dome_telemetry"] == report.chrome_telemetry(games)
    assert results["chrome_dome_telemetry"]["casts"] > 0
    assert results["chrome_dome_telemetry"]["games_with_modifier_impact"] > 0
    assert results["chrome_dome_telemetry"]["activated_copy_ability"] == (
        "UNSUPPORTED_NOT_CREDITED"
    )
    ledger = json.loads((OBL / "EXPERIMENT_LEDGER.json").read_text(encoding="utf-8"))
    matches = [row for row in ledger["experiments"] if row["experiment_id"] == r6b.EXPERIMENT]
    assert len(matches) == 1
    assert matches[0]["parent"]["sha256"] == r6b.PARENT_SHA
    assert matches[0]["candidate"]["sha256"] == r6b.CANDIDATE_SHA
    assert matches[0]["promotion_status"] == "EXPERIMENTAL"
    assert matches[0]["source_evidence"] == r6b.EVIDENCE.relative_to(ROOT).as_posix()
    role = json.loads((OBL / "CARD_ROLE_EVIDENCE.json").read_text(encoding="utf-8"))
    observations = [row for row in role["records"] if row.get("experiment_id") == r6b.EXPERIMENT]
    assert len(observations) == 2
    assert {row["card"] for row in observations} == {"Negate", "Chrome Dome"}
    assert report.VERDICT in report.REPORT.read_text(encoding="utf-8")
    outcome = {
        "status": "PASS",
        "candidate_sha256": r6b.CANDIDATE_SHA,
        "control_evidence_id": evidence["control_evidence_id"],
        "games": 900,
        "replayed": 900,
        "runtime_errors": 0,
    }
    print(json.dumps(outcome))
    return outcome


if __name__ == "__main__":
    validate()
