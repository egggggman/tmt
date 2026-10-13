"""Mirrored frozen-deck deterministic diagnostics, not balance evidence."""

from __future__ import annotations

import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_CREATURE_POWER_DAMAGE_SMOKE.json"
MIKEY = DeckSpec("michelangelo", "decks/michelangelo/PROTOTYPE_0.1.txt")
RAPHAEL = DeckSpec("raphael", "decks/raphael/PROTOTYPE_0.1.txt")
LEO = DeckSpec("leonardo", "decks/leonardo/PROTOTYPE_0.1.txt")


def main() -> None:
    games = []
    for opponent in (RAPHAEL, LEO):
        for first, second in ((MIKEY, opponent), (opponent, MIKEY)):
            spec = GameSpec(
                f"issue289-creature-power-damage-{first.display_id}-{second.display_id}",
                "issue289-creature-power-damage-diagnostic",
                3035,
                f"{first.display_id}-first",
                (first, second),
            )
            original = run_smoke_game(ROOT, spec)
            replay = run_smoke_game(ROOT, spec)
            digest = stable_digest(original)
            if original.get("error") or replay.get("error") or digest != stable_digest(replay):
                raise ValueError(f"diagnostic/replay mismatch: {spec.game_id}")
            events = original["events"]
            games.append(
                {
                    "game_id": spec.game_id,
                    "seed": spec.seed,
                    "first_player": first.display_id,
                    "replay_equal": True,
                    "result_digest": digest,
                    "event_count": len(events),
                    "creature_power_damage": [
                        {
                            key: event[key]
                            for key in (
                                "stack_object_id",
                                "source_target_id",
                                "target_id",
                                "damage_event_id",
                                "amount",
                            )
                        }
                        for event in events
                        if event["event"] == "creature_power_damage_resolved"
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
                "errors": 0,
                "creature_power_damage_resolutions": sum(
                    len(g["creature_power_damage"]) for g in games
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
