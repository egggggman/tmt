"""Fail-closed integrity and replay validator for OBL Round 3."""

# Replay assertions intentionally retain compact evidence-contract lines.
# ruff: noqa: E501, I001

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round3 as r3  # noqa: E402

OBL = ROOT / "docs/objective-balance-lab"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    evidence = json.loads((OBL / "ROUND_3_EVIDENCE.json").read_text(encoding="utf-8"))
    checkpoint = json.loads((OBL / "ROUND_3_EVIDENCE.checkpoint.json").read_text(encoding="utf-8"))
    assert evidence == checkpoint, "final evidence and checkpoint differ"
    assert evidence["environment_id"] == "OBL-BASELINE-001"
    assert evidence["schedule_games"] == 4500
    schedule = r1.schedule()
    assert (
        hashlib.sha256(json.dumps(schedule, sort_keys=True).encode()).hexdigest()
        == evidence["schedule_sha256"]
    )
    assert len(evidence["candidate_manifests"]) == 8
    assert set(evidence["candidate_results"]) == set(evidence["candidate_manifests"])
    cards = r1.catalog()
    parents = r3.frozen_parent_manifest()
    all_paths = {key: value["source_path"] for key, value in parents.items()}
    total = 0
    for experiment_id, manifest in evidence["candidate_manifests"].items():
        deck = manifest["deck_key"]
        assert deck in r3.TARGETS
        parent = parents[deck]
        assert manifest["parent_path"] == parent["source_path"]
        assert manifest["parent_sha256"] == parent["sha256"]
        candidate_path = ROOT / manifest["candidate_path"]
        assert sha(candidate_path) == manifest["candidate_sha256"], experiment_id
        parent_validation = r1.validate_deck(ROOT / parent["source_path"], cards)
        candidate_validation = r1.validate_deck(candidate_path, cards)
        assert candidate_validation["cards"] == manifest["candidate_manifest"]["cards"]
        assert (
            r1.diff(parent_validation["cards"], candidate_validation["cards"])
            == manifest["exact_diff"]
        )
        games = evidence["candidate_results"][experiment_id]
        assert len(games) == 900, experiment_id
        assert sum(deck in game["seats"] for game in games) == 900
        assert not any(game.get("runtime_error") for game in games), experiment_id
        assert sum(game["schedule"]["orientation"] == "canonical" for game in games) == 450
        assert sum(game["schedule"]["orientation"] == "reversed" for game in games) == 450
        for opponent in r1.DECKS:
            if opponent == deck:
                continue
            subset = [g for g in games if opponent in g["seats"]]
            assert len(subset) == 100, (experiment_id, opponent, len(subset))
            assert sum(g["schedule"]["orientation"] == "canonical" for g in subset) == 50
            assert sum(g["schedule"]["orientation"] == "reversed" for g in subset) == 50
        total += len(games)
        # Replay one canonical and one reversed game per candidate.
        paths = dict(all_paths)
        paths[deck] = manifest["candidate_path"]
        for wanted in ("canonical", "reversed"):
            original = next(g for g in games if g["schedule"]["orientation"] == wanted)
            replay = r1._run_one((0, paths, original["schedule"]))
            assert replay["runtime_error"] is None
            assert replay["runtime_fingerprint"] == original["runtime_fingerprint"], experiment_id
    assert total == 7200
    assert evidence["counts"] == {
        "expected_candidates": 8,
        "expected_games": 7200,
        "completed_games": 7200,
        "runtime_errors": 0,
    }
    assert len(evidence["results"]) == 8
    assert len(evidence["synthesis"]) == 4
    print(json.dumps({"round3_candidates": 8, "games": total, "runtime_errors": 0, "replays": 16}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
