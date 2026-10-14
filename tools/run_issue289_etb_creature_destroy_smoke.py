"""Bounded frozen-deck targeted ETB removal diagnostics and replays."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_ETB_CREATURE_DESTROY_SMOKE.json"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
MANIFEST_SHA = "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac"


def frozen_decks() -> dict[str, DeckSpec]:
    if hashlib.sha256(MANIFEST.read_bytes()).hexdigest() != MANIFEST_SHA:
        raise ValueError("Baseline 005 manifest changed")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    decks = {}
    for entry in manifest["decks"]:
        if entry["deck_key"] not in {"shredder", "casey_jones", "leonardo"}:
            continue
        path = ROOT / entry["source_path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("Baseline 005 deck changed")
        decks[entry["deck_key"]] = DeckSpec(entry["deck_key"], entry["source_path"])
    if set(decks) != {"shredder", "casey_jones", "leonardo"}:
        raise ValueError("selected Baseline 005 decks missing")
    return decks


def main() -> None:
    decks = frozen_decks()
    shredder, casey, leonardo = (decks[key] for key in ("shredder", "casey_jones", "leonardo"))
    specs = []
    for opponent in (casey, leonardo):
        for seats in ((shredder, opponent), (opponent, shredder)):
            specs.append(
                GameSpec(
                    f"issue289-etb-creature-destroy-{seats[0].display_id}-{seats[1].display_id}",
                    "issue289-diagnostic",
                    3093,
                    f"{seats[0].display_id}-first",
                    seats,
                )
            )
    games = []
    for spec in specs:
        first = run_smoke_game(ROOT, spec)
        replay = run_smoke_game(ROOT, spec)
        digest = stable_digest(first)
        if first.get("error") or replay.get("error") or digest != stable_digest(replay):
            raise ValueError(f"diagnostic replay mismatch: {spec.game_id}")
        events = first["events"]
        chosen = [
            {
                key: event[key]
                for key in (
                    "stack_object_id",
                    "trigger_id",
                    "event_id",
                    "source_id",
                    "target_id",
                    "offered_ids",
                    "controller",
                )
            }
            for event in events
            if event["event"] == "etb_creature_destroy_target_selected"
        ]
        resolved = [
            {
                key: event[key]
                for key in (
                    "stack_object_id",
                    "trigger_id",
                    "event_id",
                    "source_id",
                    "target_id",
                    "legal_target",
                    "destroyed",
                )
            }
            for event in events
            if event["event"] == "etb_creature_destroy_resolved"
        ]
        games.append(
            {
                "game_id": spec.game_id,
                "seed": spec.seed,
                "first_player": spec.seats[0].display_id,
                "replay_equal": True,
                "result_digest": digest,
                "event_count": len(events),
                "frozen_source_casts": sum(
                    event["event"] == "spell_cast" and event.get("card") == "Anchovy & Banana Pizza"
                    for event in events
                ),
                "target_selection": chosen,
                "resolution": resolved,
                "runtime_error": None,
            }
        )
    if not any(game["resolution"] for game in games):
        raise ValueError("frozen diagnostic did not execute the selected clause")
    result = {
        "kind": "diagnostic_only_not_balance_evidence",
        "baseline_manifest_sha256": MANIFEST_SHA,
        "semantic_runtime_sha256": identity()["aggregate_semantic_runtime_sha256"],
        "game_count": len(games),
        "replay_count": len(games),
        "games": games,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "games": len(games),
                "replays": len(games),
                "casts": sum(game["frozen_source_casts"] for game in games),
                "selections": sum(len(game["target_selection"]) for game in games),
                "resolutions": sum(len(game["resolution"]) for game in games),
            }
        )
    )


if __name__ == "__main__":
    main()
