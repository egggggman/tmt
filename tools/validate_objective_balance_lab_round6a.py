"""Fail-closed validation of the Design Studio-owned Krang R6-A experiment."""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import build_objective_balance_lab_round5_results as r5  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round6a as r6  # noqa: E402


def validate() -> None:
    _manifest, schedule, _paths, baseline_games = r6.preflight()
    evidence = json.loads(r6.EVIDENCE.read_text(encoding="utf-8"))
    checkpoint = json.loads(r6.CHECKPOINT.read_text(encoding="utf-8"))
    assert evidence == checkpoint
    r6.verify(evidence, schedule)
    assert evidence["completed_games"] == 900
    assert evidence["effect_replay_verified_games"] == 900
    assert evidence["stage1_decision"] == "CONTINUE"
    assert len(evidence["cells"]) == 9
    assert set(evidence["cells"]) == set(r1.DECKS) - {"krang"}
    assert (
        sum(game["first_player"] == "krang" for cell in evidence["cells"].values() for game in cell)
        == 450
    )
    results = evidence["results"]
    assert results["runtime_errors"] == 0
    assert results["hypothesis_result"] == "PARTIALLY_SUPPORTED"
    assert results["cardcade_verdict"] == "RETURN_TO_DESIGN_STUDIO_REJECT_POLARIZATION"
    assert results["identity_classification"] == "IDENTITY_PRESERVED"
    for opponent, cell in evidence["cells"].items():
        assert r6.digest(cell) == results["cell_fingerprints"][opponent]
        assert all(game["runtime_fingerprint"] and not game["runtime_error"] for game in cell)
        assert all(
            set(game["turtle_techie_effects"]) == {"resolved", "condition_met", "cards_drawn"}
            for game in cell
        )
    all_games = [game for cell in evidence["cells"].values() for game in cell]
    candidate = r5.summarize(all_games, "krang")
    parent = r5.summarize(baseline_games, "krang")
    comparison = r5.comparison(parent, candidate)
    assert results["comparison"] == comparison
    assert results["stage1"]["shredder"]["candidate_win_rate"] == 0.17
    assert results["stage1"]["raphael"]["candidate_win_rate"] == 0.14
    for opponent in r6.STAGE1:
        stage = results["stage1"][opponent]
        assert stage["games"] == 100
        assert stage["candidate_first_games"] == stage["opponent_first_games"] == 50
        for turn in (3, 5, 7):
            observed = [
                game["battlefield_presence"]["krang"][str(turn)]
                for game in evidence["cells"][opponent]
                if str(turn) in game["battlefield_presence"].get("krang", {})
            ]
            proxy = stage["battlefield_presence_proxy"][str(turn)]
            assert proxy["observed_games"] == len(observed)
            assert proxy["mean_creatures_if_observed"] == (
                round(statistics.mean(observed), 4) if observed else None
            )
            assert proxy["positive_games"] == sum(value > 0 for value in observed)
    assert (
        results["turtle_techie_casts"] == candidate["signature_casts"]["Donatello, Turtle Techie"]
    )
    assert results["turtle_techie_effect_events"] == {
        key: sum(game["turtle_techie_effects"][key] for game in all_games)
        for key in ("resolved", "condition_met", "cards_drawn")
    }
    ledger = json.loads((OBL / "EXPERIMENT_LEDGER.json").read_text(encoding="utf-8"))
    entries = [row for row in ledger["experiments"] if row.get("experiment_id") == r6.EXPERIMENT]
    assert len(entries) == 1
    assert entries[0]["parent"]["sha256"] == r6.PARENT_SHA
    assert entries[0]["candidate"]["sha256"] == r6.CANDIDATE_SHA
    assert entries[0]["promotion_status"] == "EXPERIMENTAL"
    role = json.loads((OBL / "CARD_ROLE_EVIDENCE.json").read_text(encoding="utf-8"))
    observations = [row for row in role["records"] if row.get("experiment_id") == r6.EXPERIMENT]
    assert len(observations) == 2
    assert {row["card"] for row in observations} == {"Negate", "Donatello, Turtle Techie"}
    report = (OBL / "ROUND_6_A_RESULTS.md").read_text(encoding="utf-8")
    assert r6.CANDIDATE_SHA in report
    assert results["cardcade_verdict"] in report
    print(
        json.dumps(
            {
                "status": "PASS",
                "games": 900,
                "replayed": 900,
                "runtime_errors": 0,
                "candidate_sha256": r6.CANDIDATE_SHA,
            }
        )
    )


if __name__ == "__main__":
    validate()
