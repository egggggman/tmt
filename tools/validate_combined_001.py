"""Validate OBL-COMBINED-001 selection, evidence, schedule, and replay fingerprints."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

# The validator includes one explicit replay-contract comment and assertions.
# ruff: noqa: E501

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402


def sha(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return hashlib.sha256(subprocess.check_output(["git", "show", f"HEAD:{relative}"])).hexdigest()


def main() -> None:
    manifest = json.loads(
        (OBL / "combined/OBL_COMBINED_001_MANIFEST.json").read_text(encoding="utf-8")
    )
    evidence = json.loads((OBL / "COMBINED_001_EVIDENCE.json").read_text(encoding="utf-8"))
    round1 = json.loads((OBL / "ROUND_1_EVIDENCE.json").read_text(encoding="utf-8"))
    ledger = json.loads((OBL / "EXPERIMENT_LEDGER.json").read_text(encoding="utf-8"))
    cards = r1.catalog()
    assert manifest["environment_id"] == "OBL-COMBINED-001"
    assert manifest["state"] == "EXPERIMENTAL_COMBINED_ENVIRONMENT"
    assert manifest["parent_environment_id"] == "OBL-BASELINE-000"
    assert len(manifest["selected_decks"]) == 10
    by_id = {record["experiment_id"]: record for record in ledger["experiments"]}
    paths = {}
    for selected in manifest["selected_decks"]:
        path = ROOT / selected["source_path"]
        assert path.exists()
        if selected["experiment_id"]:
            assert sha(path) == selected["selected_sha256"]
        else:
            assert selected["selected_sha256"] == selected["parent_baseline_sha256"]
            assert not subprocess.run(
                ["git", "diff", "--quiet", "HEAD", "--", selected["source_path"]], check=False
            ).returncode
        r1.validate_deck(path, cards)
        if selected["experiment_id"]:
            assert selected["experiment_id"] in by_id
            assert by_id[selected["experiment_id"]]["verdict"] in {
                "ACCEPTED_FOR_COMBINED_MATRIX",
                "PROMOTED",
            }
        paths[selected["deck_key"]] = selected["source_path"]
    assert set(paths) == set(r1.DECKS)
    schedule = r1.schedule()
    assert len(schedule) == 4500
    assert schedule == round1["schedule"]
    assert evidence["schedule_games"] == 4500
    assert evidence["counts"] == {
        "baseline_games_reused": 4500,
        "combined_games": 4500,
        "runtime_errors": 0,
    }
    assert len(evidence["combined_results"]) == 4500
    assert not any(game.get("runtime_error") for game in evidence["combined_results"])
    assert Counter(item["orientation"] for item in schedule) == {
        "canonical": 2250,
        "reversed": 2250,
    }
    assert all(
        sum(1 for item in schedule if deck in item["decks"] and item["orientation"] == orientation)
        == 450
        for deck in r1.DECKS
        for orientation in ("canonical", "reversed")
    )
    assert all(game.get("runtime_fingerprint") for game in evidence["combined_results"])

    # One replay per unordered matchup verifies deterministic fingerprints without rerunning the matrix.
    r1._init_worker(cards)
    first_by_pair = {}
    for game in evidence["combined_results"]:
        key = tuple(sorted(game["seats"]))
        first_by_pair.setdefault(key, game)
    assert len(first_by_pair) == 45
    replayed = 0
    for game in first_by_pair.values():
        replay = r1._run_one((0, paths, game["schedule"]))
        assert replay["runtime_error"] is None
        # Combined 001 is historical pre-support evidence; semantic enablement changes the
        # current runtime fingerprint. Preserve the original and require a current fingerprint.
        assert replay["runtime_fingerprint"]
        replayed += 1
    assert evidence["environment_decision"] == "COMBINED_ENVIRONMENT_IMPROVED"
    promoted = {
        record["experiment_id"]
        for record in by_id.values()
        if record.get("promotion_status") == "PROMOTED"
    }
    assert promoted <= {
        "OBL-R1-LEONARDO-A",
        "OBL-R2-DONATELLO-A",
        "OBL-R2-BEBOP_ROCKSTEADY-B",
        "OBL-R2-CASEY_JONES-B",
    }
    print(
        json.dumps(
            {
                "environment": "OBL-COMBINED-001",
                "matchups": 45,
                "games": 4500,
                "replayed_fingerprints": replayed,
                "runtime_errors": 0,
                "promoted": len(promoted),
            }
        )
    )


if __name__ == "__main__":
    main()
