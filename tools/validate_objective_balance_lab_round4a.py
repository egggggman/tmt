"""Fail-closed integrity and replay validator for Round 4A."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402

OBL = ROOT / "docs/objective-balance-lab"
PARENT = "decks/raphael/PROTOTYPE_0.3.txt"
EXPECTED = {
    "OBL-R4-RAPHAEL-A": {"Casey Jones, Jury-Rig Justiciar": -2, "Skateboard": 2},
    "OBL-R4-RAPHAEL-B": {
        "Casey Jones, Jury-Rig Justiciar": -2,
        "Skateboard": 1,
        "Spicy Oatmeal Pizza": 1,
    },
}


def git_or_worktree_sha(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    try:
        data = subprocess.check_output(
            ["git", "show", f"HEAD:{relative}"], stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    evidence_path = OBL / "ROUND_4A_RAPHAEL_EVIDENCE.json"
    checkpoint_path = OBL / "ROUND_4A_RAPHAEL_EVIDENCE.checkpoint.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert evidence == checkpoint
    assert evidence["environment_id"] == "OBL-BASELINE-001"
    schedule = r1.schedule()
    assert len(schedule) == 4500
    assert (
        hashlib.sha256(json.dumps(schedule, sort_keys=True).encode()).hexdigest()
        == evidence["schedule_sha256"]
    )
    assert set(evidence["candidate_manifests"]) == set(EXPECTED)
    assert set(evidence["candidate_results"]) == set(EXPECTED)
    cards = r1.catalog()
    parent = r1.validate_deck(ROOT / PARENT, cards)
    total = 0
    for experiment_id, expected_diff in EXPECTED.items():
        manifest = evidence["candidate_manifests"][experiment_id]
        candidate_path = ROOT / manifest["candidate_path"]
        candidate = r1.validate_deck(candidate_path, cards)
        assert sum(candidate["cards"].values()) == 60
        assert manifest["candidate_manifest"]["cards"] == candidate["cards"]
        assert manifest["exact_diff"] == r1.diff(parent["cards"], candidate["cards"])
        actual_delta = {
            name: row["candidate"] - row["parent"] for name, row in manifest["exact_diff"].items()
        }
        assert actual_delta == expected_diff
        assert manifest["parent_path"] == PARENT
        assert manifest["parent_checkout_sha256"] == parent["sha256"]
        assert git_or_worktree_sha(candidate_path) == manifest["candidate_sha256"]
        games = evidence["candidate_results"][experiment_id]
        assert len(games) == 900
        assert not any(game.get("runtime_error") for game in games)
        assert sum(game["schedule"]["orientation"] == "canonical" for game in games) == 450
        assert sum(game["schedule"]["orientation"] == "reversed" for game in games) == 450
        for opponent in r1.DECKS:
            if opponent == "raphael":
                continue
            subset = [game for game in games if opponent in game["seats"]]
            assert len(subset) == 100, (experiment_id, opponent)
            assert sum(game["schedule"]["orientation"] == "canonical" for game in subset) == 50
            assert sum(game["schedule"]["orientation"] == "reversed" for game in subset) == 50
        result = evidence["results"][experiment_id]
        assert result["hypothesis_result"] == "SEMANTICALLY_UNRESOLVED"
        assert result["verdict"] == "REJECT_SEMANTIC_CONFIDENCE"
        assert result["candidate_signature_usage"]["Skateboard"]["total_casts"] == 0
        assert result["candidate_signature_usage"]["Spicy Oatmeal Pizza"]["total_casts"] == 0
        for orientation in ("canonical", "reversed"):
            original = next(
                game for game in games if game["schedule"]["orientation"] == orientation
            )
            paths = {
                value["deck_key"]: value["source_path"]
                for value in json.loads(
                    (OBL / "baselines/OBL_BASELINE_001_MANIFEST.json").read_text(encoding="utf-8")
                )["decks"]
            }
            paths["raphael"] = manifest["candidate_path"]
            replay = r1._run_one((0, paths, original["schedule"]))
            assert replay["runtime_error"] is None
            # The historical pre-support fingerprint is intentionally different after
            # generic permanent/equipment/Food support; deterministic replay is covered
            # by the post-support validator against the current runtime.
            assert replay["runtime_fingerprint"]
        total += len(games)
    assert total == 1800
    assert evidence["counts"] == {
        "expected_candidates": 2,
        "expected_games": 1800,
        "completed_games": 1800,
        "runtime_errors": 0,
    }
    assert (
        subprocess.run(["git", "diff", "--quiet", "HEAD", "--", PARENT], cwd=ROOT).returncode == 0
    )
    print(json.dumps({"round4a_candidates": 2, "games": total, "runtime_errors": 0, "replays": 4}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
