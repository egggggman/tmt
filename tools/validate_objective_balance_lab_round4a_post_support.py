"""Validate Round 4A post-support evidence and preserved experiment lineage."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round4a_post_support as runner  # noqa: E402

OBL = ROOT / "docs" / "objective-balance-lab"
POST = OBL / "ROUND_4A_POST_SUPPORT_EVIDENCE.json"
DIAGNOSTIC = OBL / "ROUND_4A_POST_SUPPORT_DIAGNOSTIC.json"
PRE = OBL / "ROUND_4A_RAPHAEL_EVIDENCE.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    post = json.loads(POST.read_text(encoding="utf-8"))
    diagnostic = json.loads(DIAGNOSTIC.read_text(encoding="utf-8"))
    pre = json.loads(PRE.read_text(encoding="utf-8"))
    assert post["repository_sha"] == "cac68cfc3677e4ba3632b12ac232c44d7449fc3f"
    assert post["counts"] == {
        "expected_candidates": 2,
        "completed_games": 1800,
        "runtime_errors": 0,
    }
    assert diagnostic["counts"] == {
        "expected_candidates": 2,
        "completed_games": 80,
        "runtime_errors": 0,
    }
    assert sha(PRE) == post["pre_support_evidence_sha256"]
    assert post["schedule_sha256"] == pre["schedule_sha256"]
    assert set(post["candidate_results"]) == {"OBL-R4-RAPHAEL-A", "OBL-R4-RAPHAEL-B"}
    for experiment_id, rows in post["candidate_results"].items():
        assert len(rows) == 900, experiment_id
        assert not any(row["runtime_error"] for row in rows), experiment_id
        assert len({row["runtime_fingerprint"] for row in rows}) == 900, experiment_id
        for row in rows:
            assert row["schedule"]["orientation"] in {"canonical", "reversed"}
        assert sum(row["schedule"]["orientation"] == "canonical" for row in rows) == 450
        assert sum(row["schedule"]["orientation"] == "reversed" for row in rows) == 450
        telemetry = post["reports"][experiment_id]["utility_telemetry"]
        if experiment_id.endswith("-A"):
            assert telemetry["Skateboard"]["casts"] > 0
            assert telemetry["Spicy Oatmeal Pizza"]["casts"] == 0
        else:
            assert telemetry["Skateboard"]["casts"] > 0
            assert telemetry["Spicy Oatmeal Pizza"]["casts"] > 0
        manifest = json.loads(
            (OBL / "baselines/OBL_BASELINE_001_MANIFEST.json").read_text(encoding="utf-8")
        )
        paths = {item["deck_key"]: item["source_path"] for item in manifest["decks"]}
        paths["raphael"] = runner.CANDIDATES[experiment_id]
        replay = runner.run_one(1, paths, rows[0]["schedule"])
        assert replay["runtime_fingerprint"] == rows[0]["runtime_fingerprint"]
    print(
        "Round 4A post-support validation passed: 1,800 replay games, "
        "balanced orientations, zero runtime errors."
    )


if __name__ == "__main__":
    main()
