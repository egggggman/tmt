"""Validate and run the eight targeted OBL Round 3 candidate slices."""

# Evidence-contract tables and hypotheses intentionally retain readable long lines.
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
BASELINE_MANIFEST = OBL / "baselines/OBL_BASELINE_001_MANIFEST.json"
OUTPUT = OBL / "ROUND_3_EVIDENCE.json"
CHECKPOINT = OBL / "ROUND_3_EVIDENCE.checkpoint.json"

TARGETS = {
    "raphael": {
        "display": "Raphael",
        "candidates": {
            "OBL-R3-RAPHAEL-A": "docs/objective-balance-lab/candidates/RAPHAEL_OBL_R3_A.txt",
            "OBL-R3-RAPHAEL-B": "docs/objective-balance-lab/candidates/RAPHAEL_OBL_R3_B.txt",
        },
    },
    "shredder": {
        "display": "Shredder",
        "candidates": {
            "OBL-R3-SHREDDER-A": "docs/objective-balance-lab/candidates/SHREDDER_OBL_R3_A.txt",
            "OBL-R3-SHREDDER-B": "docs/objective-balance-lab/candidates/SHREDDER_OBL_R3_B.txt",
        },
    },
    "april_oneil": {
        "display": "April O'Neil",
        "candidates": {
            "OBL-R3-APRIL_ONEIL-A": "docs/objective-balance-lab/candidates/APRIL_ONEIL_OBL_R3_A.txt",
            "OBL-R3-APRIL_ONEIL-B": "docs/objective-balance-lab/candidates/APRIL_ONEIL_OBL_R3_B.txt",
        },
    },
    "krang": {
        "display": "Krang",
        "candidates": {
            "OBL-R3-KRANG-A": "docs/objective-balance-lab/candidates/KRANG_OBL_R3_A.txt",
            "OBL-R3-KRANG-B": "docs/objective-balance-lab/candidates/KRANG_OBL_R3_B.txt",
        },
    },
}

HYPOTHESES = {
    "OBL-R3-RAPHAEL-A": "Removing Casey density for higher-mana Raphael threats preserves confrontation identity while lowering early efficiency and raw conversion.",
    "OBL-R3-RAPHAEL-B": "A narrower, high-cost Raphael combat-risk effect lowers generic rate while preserving Raphael-specific attack decisions.",
    "OBL-R3-SHREDDER-A": "Reducing the measurably active Squirrelanoids package lowers early development while slower villain cards preserve ruthless pressure.",
    "OBL-R3-SHREDDER-B": "Reducing active Shredder's Armor efficiency lowers conversion through a different pressure lever while preserving villain control identity.",
    "OBL-R3-APRIL_ONEIL-A": "Replacing interaction density with April-specific selection and end-step card advantage improves reliable resource generation.",
    "OBL-R3-APRIL_ONEIL-B": "Replacing disposable early artifacts with adaptive interaction improves April's ability to survive pressure and stabilize.",
    "OBL-R3-KRANG-A": "Artifact Food that draws a card and can become mana improves engine consistency without adding Does Machines.",
    "OBL-R3-KRANG-B": "Additional Krang copies convert an established artifact board into a larger affinity threat and hand refill payoff.",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_parent_manifest() -> dict[str, dict]:
    manifest = json.loads(BASELINE_MANIFEST.read_text(encoding="utf-8"))
    if manifest["environment_id"] != "OBL-BASELINE-001":
        raise SystemExit("unexpected official baseline environment")
    return {item["deck_key"]: item for item in manifest["decks"]}


def candidate_manifests(cards: dict[str, dict], parents: dict[str, dict]) -> dict[str, dict]:
    result = {}
    for deck, spec in TARGETS.items():
        parent_path = ROOT / parents[deck]["source_path"]
        parent = r1.validate_deck(parent_path, cards)
        if sha(parent_path) != parents[deck]["sha256"]:
            raise SystemExit(f"baseline manifest hash mismatch: {parent_path}")
        for experiment_id, relative in spec["candidates"].items():
            path = ROOT / relative
            candidate = r1.validate_deck(path, cards)
            changes = r1.diff(parent["cards"], candidate["cards"])
            slots = sum(abs(row["candidate"] - row["parent"]) for row in changes.values()) // 2
            if slots > 4:
                raise SystemExit(f"{experiment_id}: more than four changed slots")
            result[experiment_id] = {
                "experiment_id": experiment_id,
                "deck_key": deck,
                "deck": spec["display"],
                "parent_path": parents[deck]["source_path"],
                "parent_sha256": parents[deck]["sha256"],
                "candidate_path": relative,
                "candidate_sha256": sha(path),
                "parent_manifest": parent,
                "candidate_manifest": candidate,
                "exact_diff": changes,
                "hypothesis": HYPOTHESES[experiment_id],
                "semantic_gate": "PASSED_PRE_SCREEN",
            }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    cards = r1.catalog()
    parents = frozen_parent_manifest()
    manifests = candidate_manifests(cards, parents)
    schedule = r1.schedule()
    if len(schedule) != 4500:
        raise SystemExit("frozen schedule is not 4,500 games")
    baseline_evidence_path = OBL / "COMBINED_001_EVIDENCE.json"
    baseline_evidence = json.loads(baseline_evidence_path.read_text(encoding="utf-8"))
    if len(baseline_evidence.get("combined_results", [])) != 4500:
        raise SystemExit("banked OBL-BASELINE-001 evidence is incomplete")
    payload = {
        "schema": "objective-balance-lab-round-3-v1",
        "repository_sha": "59c4c36b1e4c0d834102749d5fe7924054734606",
        "environment_id": "OBL-BASELINE-001",
        "parent_evidence_path": "docs/objective-balance-lab/COMBINED_001_EVIDENCE.json",
        "parent_evidence_sha256": sha(baseline_evidence_path),
        "schedule_sha256": hashlib.sha256(
            json.dumps(schedule, sort_keys=True).encode()
        ).hexdigest(),
        "schedule_games": len(schedule),
        "candidate_manifests": manifests,
        "candidate_results": {},
        "counts": {
            "expected_candidates": 8,
            "expected_games": 7200,
            "completed_games": 0,
            "runtime_errors": 0,
        },
    }
    if args.validate_only:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 0
    for experiment_id, manifest in manifests.items():
        deck = manifest["deck_key"]
        games = [item for item in schedule if deck in item["pair"]]
        paths = {key: value["source_path"] for key, value in parents.items()}
        paths[deck] = manifest["candidate_path"]
        print(f"starting {experiment_id}: {len(games)} games", flush=True)
        results = r1.run_set(paths, games, cards, args.workers)
        payload["candidate_results"][experiment_id] = results
        payload["counts"]["completed_games"] = sum(
            len(rows) for rows in payload["candidate_results"].values()
        )
        payload["counts"]["runtime_errors"] = sum(
            bool(game.get("runtime_error"))
            for rows in payload["candidate_results"].values()
            for game in rows
        )
        CHECKPOINT.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
