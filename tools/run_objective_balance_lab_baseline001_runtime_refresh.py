"""Refresh OBL-BASELINE-001 under the current semantic Cardcade runtime."""

# The runner emits compact checkpoint records; wide expressions are intentional.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402

from tmnt_design_studio.pilot07 import AcceptancePilot  # noqa: E402
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, run_game  # noqa: E402

OBL = ROOT / "docs/objective-balance-lab"
MANIFEST_PATH = OBL / "baselines/OBL_BASELINE_001_MANIFEST.json"
OUTPUT = OBL / "BASELINE_001_RUNTIME_REFRESH_EVIDENCE.json"
CHECKPOINT = OBL / "BASELINE_001_RUNTIME_REFRESH_CHECKPOINT.json"


def snapshot_utility(
    snapshot: dict[str, object], seats: tuple[str, str], cards: dict[str, dict[str, object]]
) -> dict[str, dict[str, dict[str, int]]]:
    utility = {name for name, card in cards.items() if "Artifact" in str(card.get("type_line", ""))}
    players = snapshot.get("players", [])
    result = {
        deck: {
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
            for name in utility
        }
        for deck in seats
    }
    for event in snapshot.get("events", []):
        owner = event.get("player", event.get("controller", event.get("owner")))
        if isinstance(owner, int) and owner < len(players):
            owner = players[owner].get("name")
        deck = seats[0] if str(owner).lower() in {"a", "0", seats[0].lower()} else seats[1]
        name = event.get("card") or event.get("source")
        if deck not in result or name not in utility:
            continue
        kind = event.get("event")
        counts = result[deck][name]
        if kind == "card_drawn":
            counts["drawn"] += 1
        elif kind == "utility_artifact_legal_opportunity":
            counts["legal_opportunities"] += 1
        elif kind == "utility_artifact_action_selected":
            counts["selected"] += 1
        elif kind == "spell_cast":
            counts["casts"] += 1
        elif kind == "permanent_resolved":
            counts["resolved"] += 1
        elif kind == "activation_announced":
            counts["activations"] += 1
        elif kind == "equipment_attached":
            counts["equips"] += 1
            counts["effect_used"] += 1
        elif kind == "activated_ability_resolved" and event.get("delivered"):
            counts["effect_used"] += 1
    return {
        deck: {card: counts for card, counts in cards_by_name.items() if any(counts.values())}
        for deck, cards_by_name in result.items()
        if any(any(counts.values()) for counts in cards_by_name.values())
    }


def run_one(
    index: int, paths: dict[str, str], item: dict[str, object], cards: dict[str, dict[str, object]]
) -> dict[str, object]:
    left, right = item["decks"]
    spec = GameSpec(
        f"obl-baseline001-refresh-{index:05d}",
        f"{left}-vs-{right}",
        item["seed"],
        item["orientation"],
        (DeckSpec(left, paths[left]), DeckSpec(right, paths[right])),
    )
    snapshot = run_game(ROOT, spec, AcceptancePilot())
    result = r1.game_metrics(snapshot, (left, right), cards)
    result["schedule"] = item
    result["seats"] = [left, right]
    result["utility_telemetry"] = snapshot_utility(snapshot, (left, right), cards)
    result["runtime_error"] = None
    return result


def run_payload(
    payload: tuple[int, dict[str, str], dict[str, object], dict[str, dict[str, object]]],
) -> dict[str, object]:
    index, paths, item, cards = payload
    try:
        return run_one(index, paths, item, cards)
    except Exception as error:
        return {
            "schedule": item,
            "seats": item["decks"],
            "runtime_error": f"{type(error).__name__}: {error}",
        }


def write_checkpoint(payload: dict[str, object]) -> None:
    CHECKPOINT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def normalized_sha(path: Path) -> str:
    logical = path.read_text(encoding="utf-8").encode("utf-8")
    return hashlib.sha256(logical).hexdigest()


def deck_hashes(path: Path) -> set[str]:
    raw = path.read_bytes()
    return {
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")).hexdigest(),
        normalized_sha(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    del args.workers  # Sequential execution makes checkpoint/replay state unambiguous.
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    cards = r1.catalog()
    paths = {row["deck_key"]: row["source_path"] for row in manifest["decks"]}
    for row in manifest["decks"]:
        r1.validate_deck(ROOT / row["source_path"], cards)
        if row["sha256"] not in deck_hashes(ROOT / row["source_path"]):
            raise SystemExit(f"baseline deck hash mismatch: {row['deck_key']}")
    schedule = r1.schedule()
    runtime = identity()
    payload = {
        "schema": "objective-balance-lab-baseline-001-runtime-refresh-v1",
        "environment_id": "OBL-BASELINE-001",
        "evidence_id": "OBL-BASELINE-001-RUNTIME-REFRESH-001",
        "state": "BASELINE_EVIDENCE_REFRESH",
        "repository_sha": runtime["repository_commit"],
        "semantic_runtime_identity": runtime,
        "baseline_manifest_path": MANIFEST_PATH.relative_to(ROOT).as_posix(),
        "schedule_sha256": hashlib.sha256(
            json.dumps(schedule, sort_keys=True).encode()
        ).hexdigest(),
        "schedule_games": len(schedule),
        "orientation_counts": Counter(row["orientation"] for row in schedule),
        "deck_manifest": manifest["decks"],
        "original_evidence_path": "docs/objective-balance-lab/COMBINED_001_EVIDENCE.json",
        "results": [],
        "counts": {"completed_games": 0, "runtime_errors": 0},
    }
    if CHECKPOINT.exists():
        prior = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        if (
            prior.get("semantic_runtime_identity", {}).get("aggregate_semantic_runtime_sha256")
            == runtime["aggregate_semantic_runtime_sha256"]
            and prior.get("schedule_sha256") == payload["schedule_sha256"]
        ):
            payload["results"] = prior.get("results", [])
    completed = {
        (
            row.get("schedule", {}).get("pair_index"),
            row.get("schedule", {}).get("block"),
            row.get("schedule", {}).get("orientation"),
        )
        for row in payload["results"]
    }
    pending = [
        (index, paths, item, cards)
        for index, item in enumerate(schedule, 1)
        if (item["pair_index"], item["block"], item["orientation"]) not in completed
    ]
    with ProcessPoolExecutor(max_workers=8) as executor:
        for batch_start in range(0, len(pending), 100):
            batch = pending[batch_start : batch_start + 100]
            payload["results"].extend(executor.map(run_payload, batch, chunksize=1))
            payload["results"].sort(
                key=lambda row: (
                    row.get("schedule", {}).get("pair_index", 0),
                    row.get("schedule", {}).get("block", 0),
                    row.get("schedule", {}).get("orientation", ""),
                )
            )
            payload["counts"] = {
                "completed_games": len(payload["results"]),
                "runtime_errors": sum(bool(row.get("runtime_error")) for row in payload["results"]),
            }
            write_checkpoint(payload)
            print(f"completed {len(payload['results'])}/{len(schedule)}", flush=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
