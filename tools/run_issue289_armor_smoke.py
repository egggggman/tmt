"""Small frozen-deck Equipment diagnostics; never a balance comparison."""

from __future__ import annotations

import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_ARMOR_SMOKE.json"
SHREDDER = DeckSpec("shredder", "decks/shredder/PROTOTYPE_0.1.txt")
RAPHAEL = DeckSpec("raphael", "decks/raphael/PROTOTYPE_0.1.txt")
LEONARDO = DeckSpec("leonardo", "decks/leonardo/PROTOTYPE_0.1.txt")


def main() -> None:
    games = []
    for opponent in (RAPHAEL, LEONARDO):
        for first, second in ((SHREDDER, opponent), (opponent, SHREDDER)):
            spec = GameSpec(
                f"issue289-armor-{first.display_id}-{second.display_id}",
                "issue289-armor-diagnostic",
                3061,
                f"{first.display_id}-first",
                (first, second),
            )
            original = run_smoke_game(ROOT, spec)
            replay = run_smoke_game(ROOT, spec)
            digest = stable_digest(original)
            if original.get("error") or replay.get("error") or digest != stable_digest(replay):
                raise ValueError(f"deterministic diagnostic failed: {spec.game_id}")
            events = original["events"]
            games.append(
                {
                    "game_id": spec.game_id,
                    "seed": spec.seed,
                    "first_player": first.display_id,
                    "replay_equal": True,
                    "result_digest": digest,
                    "event_count": len(events),
                    "entry_targets": [
                        {key: event[key] for key in ("stack_object_id", "event_id", "target_id")}
                        for event in events
                        if event["event"] == "equipment_entry_target_selected"
                    ],
                    "entry_resolutions": [
                        {
                            key: event[key]
                            for key in ("stack_object_id", "source_id", "target_id", "attached")
                        }
                        for event in events
                        if event["event"] == "equipment_entry_attach_resolved"
                    ],
                    "equip_sacrifices": [
                        {
                            key: event[key]
                            for key in (
                                "stack_object_id",
                                "source_id",
                                "cost_object_id",
                                "destination_object_id",
                            )
                        }
                        for event in events
                        if event["event"] == "activation_other_sacrifice_paid"
                    ],
                    "runtime_error": None,
                }
            )
    result = {
        "kind": "diagnostic_only_not_balance_evidence",
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
                "entry_resolutions": sum(len(game["entry_resolutions"]) for game in games),
                "equip_sacrifices": sum(len(game["equip_sacrifices"]) for game in games),
            }
        )
    )


if __name__ == "__main__":
    main()
