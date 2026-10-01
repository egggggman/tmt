"""Fail-closed validator for Round 4B Raphael evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs" / "objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round4b_raphael as runner  # noqa: E402


def main() -> int:
    evidence = json.loads((OBL / "ROUND_4B_RAPHAEL_EVIDENCE.json").read_text(encoding="utf-8"))
    diagnostic = json.loads((OBL / "ROUND_4B_RAPHAEL_DIAGNOSTIC.json").read_text(encoding="utf-8"))
    cards = r1.catalog()
    parent = r1.validate_deck(ROOT / "decks/raphael/PROTOTYPE_0.3.txt", cards)
    assert parent["sha256"] == "220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51"
    assert evidence["counts"] == {
        "expected_candidates": 2,
        "completed_games": 1800,
        "runtime_errors": 0,
    }
    assert diagnostic["counts"] == {
        "expected_candidates": 2,
        "completed_games": 80,
        "runtime_errors": 0,
    }
    assert evidence["schedule_sha256"] == diagnostic["schedule_sha256"]
    for experiment_id, candidate_path in runner.CANDIDATES.items():
        candidate = r1.validate_deck(ROOT / candidate_path, cards)
        manifest = evidence["candidate_manifests"][experiment_id]
        assert candidate["sha256"] == manifest["candidate_sha256"]
        assert manifest["parent_sha256"] == parent["sha256"]
        assert manifest["exact_diff"] == r1.diff(parent["cards"], candidate["cards"])
        rows = evidence["candidate_results"][experiment_id]
        assert len(rows) == 900
        assert not any(row["runtime_error"] for row in rows)
        assert sum(row["schedule"]["orientation"] == "canonical" for row in rows) == 450
        assert sum(row["schedule"]["orientation"] == "reversed" for row in rows) == 450
        for opponent in r1.DECKS:
            if opponent == "raphael":
                continue
            subset = [row for row in rows if opponent in row["seats"]]
            assert len(subset) == 100
            assert sum(row["schedule"]["orientation"] == "canonical" for row in subset) == 50
            assert sum(row["schedule"]["orientation"] == "reversed" for row in subset) == 50
        telemetry = evidence["reports"][experiment_id]["utility_telemetry"]
        assert telemetry["Skateboard"]["casts"] > 0
        assert telemetry["Spicy Oatmeal Pizza"]["casts"] > 0
        paths = json.loads(
            (OBL / "baselines/OBL_BASELINE_001_MANIFEST.json").read_text(encoding="utf-8")
        )
        deck_paths = {item["deck_key"]: item["source_path"] for item in paths["decks"]}
        deck_paths["raphael"] = candidate_path
        replay = runner.r4a.run_one(1, deck_paths, rows[0]["schedule"])
        assert replay["runtime_fingerprint"] == rows[0]["runtime_fingerprint"]
    print(
        "Round 4B validation passed: 1,800 games, 80-game preflight, "
        "balanced starts, semantic usage, deterministic replay."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
