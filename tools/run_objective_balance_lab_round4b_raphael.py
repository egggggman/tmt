"""Run the gated Round 4B Raphael utility refinement replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import run_objective_balance_lab_round1 as r1
import run_objective_balance_lab_round4a_post_support as r4a

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs" / "objective-balance-lab"
CANDIDATES = {
    "OBL-R4-RAPHAEL-C": "docs/objective-balance-lab/candidates/RAPHAEL_OBL_R4_C.txt",
    "OBL-R4-RAPHAEL-D": "docs/objective-balance-lab/candidates/RAPHAEL_OBL_R4_D.txt",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games-per-opponent", type=int, default=20)
    parser.add_argument("--opponents", nargs="+", default=["shredder", "april_oneil"])
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    schedule = r1.schedule()
    if args.full:
        selected = [item for item in schedule if "raphael" in item["pair"]]
    else:
        selected = []
        for opponent in args.opponents:
            matches = [
                item for item in schedule if opponent in item["pair"] and "raphael" in item["pair"]
            ]
            selected.extend(matches[: args.games_per_opponent])
    manifest = json.loads(
        (OBL / "baselines/OBL_BASELINE_001_MANIFEST.json").read_text(encoding="utf-8")
    )
    baseline_paths = {item["deck_key"]: item["source_path"] for item in manifest["decks"]}
    payload = {
        "schema": "objective-balance-lab-round-4b-raphael-v1",
        "repository_sha": "8b8a3b353d4aac9f00704adf57383101d9c1e048",
        "parent_environment": "OBL-BASELINE-001",
        "parent_evidence_path": "docs/objective-balance-lab/ROUND_4A_POST_SUPPORT_EVIDENCE.json",
        "schedule_sha256": hashlib.sha256(
            json.dumps(schedule, sort_keys=True).encode()
        ).hexdigest(),
        "diagnostic": not args.full,
        "opponents": args.opponents,
        "games_per_opponent": args.games_per_opponent if not args.full else 100,
        "candidate_results": {},
        "counts": {"expected_candidates": 2, "completed_games": 0, "runtime_errors": 0},
    }
    for experiment_id, candidate_path in CANDIDATES.items():
        paths = dict(baseline_paths)
        paths["raphael"] = candidate_path
        rows = []
        for index, item in enumerate(selected, 1):
            try:
                rows.append(r4a.run_one(index, paths, item))
            except Exception as error:
                rows.append(
                    {
                        "schedule": item,
                        "seats": item["decks"],
                        "runtime_error": f"{type(error).__name__}: {error}",
                    }
                )
        payload["candidate_results"][experiment_id] = rows
        payload["counts"]["completed_games"] += len(rows)
        payload["counts"]["runtime_errors"] += sum(bool(row.get("runtime_error")) for row in rows)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
