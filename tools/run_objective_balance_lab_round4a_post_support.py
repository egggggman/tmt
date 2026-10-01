"""Run the gated post-support Round 4A Raphael replay with utility telemetry."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402

from tmnt_design_studio.pilot07 import AcceptancePilot  # noqa: E402
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, run_game  # noqa: E402

OBL = ROOT / "docs/objective-balance-lab"
BASELINE_MANIFEST = OBL / "baselines/OBL_BASELINE_001_MANIFEST.json"
CANDIDATES = {
    "OBL-R4-RAPHAEL-A": "docs/objective-balance-lab/candidates/RAPHAEL_OBL_R4_A.txt",
    "OBL-R4-RAPHAEL-B": "docs/objective-balance-lab/candidates/RAPHAEL_OBL_R4_B.txt",
}
UTILITY = {"Skateboard", "Spicy Oatmeal Pizza"}


def utility_telemetry(
    snapshot: dict[str, object], player_name: str = "raphael"
) -> dict[str, dict[str, int]]:
    events = snapshot.get("events", [])
    players = snapshot.get("players", [])
    counts = {
        name: {
            "drawn": 0,
            "legal_opportunities": 0,
            "selected": 0,
            "casts": 0,
            "resolved": 0,
            "activations": 0,
            "equips": 0,
            "effect_used": 0,
        }
        for name in UTILITY
    }
    for event in events:
        event_player = event.get("player", event.get("controller"))
        if isinstance(event_player, int) and event_player < len(players):
            event_player = players[event_player].get("name")
        if event_player is None:
            event_player = event.get("owner")
        if str(event_player).lower() != player_name.lower():
            continue
        name = event.get("card") or event.get("source")
        if name not in UTILITY:
            continue
        kind = event.get("event")
        if kind == "utility_artifact_legal_opportunity":
            counts[name]["legal_opportunities"] += 1
        elif kind == "card_drawn":
            counts[name]["drawn"] += 1
        elif kind == "utility_artifact_action_selected":
            counts[name]["selected"] += 1
        elif kind == "spell_cast":
            counts[name]["casts"] += 1
        elif kind == "permanent_resolved":
            counts[name]["resolved"] += 1
        elif kind == "activation_announced":
            counts[name]["activations"] += 1
        elif kind == "equipment_attached":
            counts[name]["equips"] += 1
            counts[name]["effect_used"] += 1
        elif kind == "activated_ability_resolved":
            counts[name]["effect_used"] += int(
                name == "Spicy Oatmeal Pizza" and bool(event.get("delivered"))
            )
    return counts


def run_one(index: int, paths: dict[str, str], item: dict[str, object]) -> dict[str, object]:
    left, right = item["decks"]
    spec = GameSpec(
        f"obl-r4a-post-{index:05d}",
        f"{left}-vs-{right}",
        item["seed"],
        item["orientation"],
        (DeckSpec(left, paths[left]), DeckSpec(right, paths[right])),
    )
    snapshot = run_game(ROOT, spec, AcceptancePilot())
    metrics = r1.game_metrics(snapshot, (left, right), r1.catalog())
    metrics["utility_telemetry"] = utility_telemetry(snapshot, "raphael")
    metrics["schedule"] = item
    metrics["seats"] = [left, right]
    metrics["runtime_error"] = None
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games-per-opponent", type=int, default=20)
    parser.add_argument("--opponents", nargs="+", default=["shredder", "april_oneil"])
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--output", type=Path, default=OBL / "ROUND_4A_POST_SUPPORT_EVIDENCE.json")
    args = parser.parse_args()
    schedule = r1.schedule()
    by_opponent: dict[str, list[dict[str, object]]] = {opponent: [] for opponent in args.opponents}
    for item in schedule:
        if "raphael" not in item["pair"]:
            continue
        opponent = next(deck for deck in item["pair"] if deck != "raphael")
        if opponent in by_opponent:
            by_opponent[opponent].append(item)
    if args.full:
        selected = [item for item in schedule if "raphael" in item["pair"]]
    else:
        selected = [
            item
            for opponent in args.opponents
            for item in by_opponent[opponent][: args.games_per_opponent]
        ]
    baseline_manifest = json.loads(BASELINE_MANIFEST.read_text(encoding="utf-8"))
    baseline_paths = {item["deck_key"]: item["source_path"] for item in baseline_manifest["decks"]}
    payload = {
        "schema": "objective-balance-lab-round-4a-post-support-v1",
        "repository_sha": "cac68cfc3677e4ba3632b12ac232c44d7449fc3f",
        "parent_evidence_path": "docs/objective-balance-lab/ROUND_4A_RAPHAEL_EVIDENCE.json",
        "schedule_sha256": hashlib.sha256(
            json.dumps(schedule, sort_keys=True).encode()
        ).hexdigest(),
        "diagnostic": not args.full,
        "opponents": args.opponents,
        "games_per_opponent": len(selected) // len(args.opponents) if args.opponents else 0,
        "candidate_results": {},
        "counts": {"expected_candidates": 2, "completed_games": 0, "runtime_errors": 0},
    }
    for experiment_id, candidate_path in CANDIDATES.items():
        paths = dict(baseline_paths)
        paths["raphael"] = candidate_path
        results = []
        for index, item in enumerate(selected, 1):
            try:
                results.append(run_one(index, paths, item))
            except Exception as error:
                results.append(
                    {
                        "schedule": item,
                        "seats": item["decks"],
                        "runtime_error": f"{type(error).__name__}: {error}",
                    }
                )
        payload["candidate_results"][experiment_id] = results
        payload["counts"]["completed_games"] += len(results)
        payload["counts"]["runtime_errors"] += sum(
            bool(row.get("runtime_error")) for row in results
        )
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
