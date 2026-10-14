"""Bounded frozen-deck combat-trigger diagnostics with exact replays."""

from __future__ import annotations

import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_COMBAT_DRAW_LIFE_SMOKE.json"
SHREDDER = DeckSpec("shredder", "decks/shredder/PROTOTYPE_0.1.txt")
APRIL = DeckSpec("april_oneil", "decks/april_oneil/PROTOTYPE_0.1.txt")
CASEY = DeckSpec("casey_jones", "decks/casey_jones/PROTOTYPE_0.1.txt")
LEONARDO = DeckSpec("leonardo", "decks/leonardo/PROTOTYPE_0.1.txt")


def main() -> None:
    specs = []
    for opponent in (APRIL, CASEY):
        for seats in ((SHREDDER, opponent), (opponent, SHREDDER)):
            specs.append(
                GameSpec(
                    f"issue289-combat-draw-life-{seats[0].display_id}-{seats[1].display_id}",
                    "issue289-diagnostic",
                    3087,
                    f"{seats[0].display_id}-first",
                    seats,
                )
            )
    specs.append(
        GameSpec(
            "issue289-combat-draw-life-blocked",
            "issue289-diagnostic",
            3081,
            "shredder-first",
            (SHREDDER, LEONARDO),
        )
    )
    games = []
    for spec in specs:
        first = run_smoke_game(ROOT, spec)
        second = run_smoke_game(ROOT, spec)
        digest = stable_digest(first)
        if first.get("error") or second.get("error") or digest != stable_digest(second):
            raise ValueError(f"diagnostic replay mismatch: {spec.game_id}")
        events = first["events"]
        games.append(
            {
                "game_id": spec.game_id,
                "seed": spec.seed,
                "first_player": spec.seats[0].display_id,
                "replay_equal": True,
                "result_digest": digest,
                "event_count": len(events),
                "frozen_source_casts": sum(
                    event["event"] == "spell_cast"
                    and event.get("card") == "Oroku Saki, Shredder Rising"
                    for event in events
                ),
                "resolved_trigger": [
                    {
                        key: event[key]
                        for key in (
                            "event_id",
                            "trigger_id",
                            "stack_object_id",
                            "source_id",
                            "controller",
                            "damage",
                            "draw_count",
                            "drawn_count",
                            "life_lost",
                            "life_before",
                            "life_after",
                            "failed_draw_pending",
                        )
                    }
                    for event in events
                    if event["event"] == "combat_draw_life_resolved"
                ],
                "runtime_error": None,
            }
        )
    if not any(game["resolved_trigger"] for game in games):
        raise ValueError("frozen diagnostic did not execute the selected clause")
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
                "casts": sum(game["frozen_source_casts"] for game in games),
                "triggers": sum(len(game["resolved_trigger"]) for game in games),
            }
        )
    )


if __name__ == "__main__":
    main()
