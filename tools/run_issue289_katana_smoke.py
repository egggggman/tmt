"""Small frozen-deck Equipment diagnostics, not balance games."""

from __future__ import annotations

import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_KATANA_SMOKE.json"
LEONARDO = DeckSpec("leonardo", "decks/leonardo/PROTOTYPE_0.1.txt")
RAPHAEL = DeckSpec("raphael", "decks/raphael/PROTOTYPE_0.1.txt")
SHREDDER = DeckSpec("shredder", "decks/shredder/PROTOTYPE_0.1.txt")


def main() -> None:
    games = []
    specs = []
    for opponent in (RAPHAEL, SHREDDER):
        for first, second in ((LEONARDO, opponent), (opponent, LEONARDO)):
            specs.append(
                GameSpec(
                    f"issue289-katana-{first.display_id}-{second.display_id}",
                    "issue289-katana-diagnostic",
                    3071,
                    f"{first.display_id}-first",
                    (first, second),
                )
            )
    # Bounded targeted seed search found actual printed-clause execution here.
    specs.append(
        GameSpec(
            "issue289-katana-leonardo-shredder-trigger-execution",
            "issue289-katana-diagnostic",
            3073,
            "leonardo-first",
            (LEONARDO, SHREDDER),
        )
    )
    for spec in specs:
        original = run_smoke_game(ROOT, spec)
        replay = run_smoke_game(ROOT, spec)
        digest = stable_digest(original)
        if original.get("error") or replay.get("error") or digest != stable_digest(replay):
            raise ValueError(f"diagnostic replay mismatch: {spec.game_id}")
        events = original["events"]
        games.append(
            {
                "game_id": spec.game_id,
                "seed": spec.seed,
                "first_player": spec.seats[0].display_id,
                "replay_equal": True,
                "result_digest": digest,
                "event_count": len(events),
                "optional_attach": [
                    {
                        key: event[key]
                        for key in (
                            "stack_object_id",
                            "event_id",
                            "source_id",
                            "recipient_id",
                            "chosen",
                            "attached",
                        )
                    }
                    for event in events
                    if event["event"] == "equipment_subtype_entry_attach_resolved"
                ],
                "granted_combat": [
                    {
                        key: event[key]
                        for key in (
                            "stack_object_id",
                            "event_id",
                            "grant_source_id",
                            "recipient_id",
                            "untapped",
                            "life_gained",
                        )
                    }
                    for event in events
                    if event["event"] == "equipment_granted_combat_resolved"
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
                "optional_attach": sum(len(game["optional_attach"]) for game in games),
                "granted_combat": sum(len(game["granted_combat"]) for game in games),
            }
        )
    )


if __name__ == "__main__":
    main()
