"""Run the two isolated Raphael utility-substitution candidates."""

# Evidence-contract tables intentionally retain compact long lines.
# ruff: noqa: E501, I001

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402

OBL = ROOT / "docs/objective-balance-lab"
PARENT_PATH = "decks/raphael/PROTOTYPE_0.3.txt"
CANDIDATES = {
    "OBL-R4-RAPHAEL-A": "docs/objective-balance-lab/candidates/RAPHAEL_OBL_R4_A.txt",
    "OBL-R4-RAPHAEL-B": "docs/objective-balance-lab/candidates/RAPHAEL_OBL_R4_B.txt",
}
HYPOTHESES = {
    "OBL-R4-RAPHAEL-A": "Replacing two efficient creatures with noncreature utility lowers Raphael’s board-pressure efficiency while preserving street-fighter / improvised-gear identity.",
    "OBL-R4-RAPHAEL-B": "Diversifying the replacement utility package lowers threat density without overconcentrating Raphael around one support card.",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def diff(parent: dict[str, int], candidate: dict[str, int]) -> dict[str, dict[str, int]]:
    names = sorted(set(parent) | set(candidate))
    return {
        name: {"parent": parent.get(name, 0), "candidate": candidate.get(name, 0)}
        for name in names
        if parent.get(name, 0) != candidate.get(name, 0)
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path, default=OBL / "ROUND_4A_RAPHAEL_EVIDENCE.json")
    args = parser.parse_args()
    cards = r1.catalog()
    parent_path = ROOT / PARENT_PATH
    parent = r1.validate_deck(parent_path, cards)
    schedule = r1.schedule()
    assert len(schedule) == 4500
    baseline_manifest = json.loads(
        (OBL / "baselines/OBL_BASELINE_001_MANIFEST.json").read_text(encoding="utf-8")
    )
    baseline_entry = next(
        item for item in baseline_manifest["decks"] if item["deck_key"] == "raphael"
    )
    manifests = {}
    for experiment_id, relative in CANDIDATES.items():
        candidate = r1.validate_deck(ROOT / relative, cards)
        changes = diff(parent["cards"], candidate["cards"])
        assert sum(abs(change["candidate"] - change["parent"]) for change in changes.values()) == 4
        manifests[experiment_id] = {
            "experiment_id": experiment_id,
            "deck": "Raphael",
            "deck_key": "raphael",
            "parent_path": PARENT_PATH,
            "parent_declared_sha256": baseline_entry["sha256"],
            "parent_checkout_sha256": parent["sha256"],
            "candidate_path": relative,
            "candidate_sha256": sha(ROOT / relative),
            "candidate_manifest": candidate,
            "exact_diff": changes,
            "hypothesis": HYPOTHESES[experiment_id],
            "semantic_gate": "PASSED_PRE_SCREEN",
        }
    payload = {
        "schema": "objective-balance-lab-round-4a-raphael-v1",
        "repository_sha": "d06e4cf36a202f56f95e100e99ff09a6ca43ae7f",
        "environment_id": "OBL-BASELINE-001",
        "parent_environment": "OBL-BASELINE-001",
        "parent_evidence_path": "docs/objective-balance-lab/COMBINED_001_EVIDENCE.json",
        "schedule_sha256": hashlib.sha256(
            json.dumps(schedule, sort_keys=True).encode()
        ).hexdigest(),
        "schedule_games": 4500,
        "candidate_manifests": manifests,
        "candidate_results": {},
        "counts": {
            "expected_candidates": 2,
            "expected_games": 1800,
            "completed_games": 0,
            "runtime_errors": 0,
        },
    }
    checkpoint = args.output.with_name(args.output.stem + ".checkpoint.json")
    baseline_paths = {item["deck_key"]: item["source_path"] for item in baseline_manifest["decks"]}
    for experiment_id, manifest in manifests.items():
        games = [item for item in schedule if "raphael" in item["pair"]]
        paths = dict(baseline_paths)
        paths["raphael"] = manifest["candidate_path"]
        results = r1.run_set(paths, games, cards, args.workers)
        assert len(results) == 900
        payload["candidate_results"][experiment_id] = results
        payload["counts"]["completed_games"] = sum(
            len(rows) for rows in payload["candidate_results"].values()
        )
        payload["counts"]["runtime_errors"] = sum(
            bool(game.get("runtime_error"))
            for rows in payload["candidate_results"].values()
            for game in rows
        )
        checkpoint.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
