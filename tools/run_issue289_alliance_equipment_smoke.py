"""Exact Alliance failure replay and mirrored frozen Equipment diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_ALLIANCE_EQUIPMENT_SMOKE.json"
MICHELANGELO = DeckSpec("michelangelo", "decks/michelangelo/PROTOTYPE_0.1.txt")
RAPHAEL = DeckSpec("raphael", "decks/raphael/PROTOTYPE_0.1.txt")
CASEY = DeckSpec("casey_jones", "decks/casey_jones/PROTOTYPE_0.1.txt")
SHREDDER = DeckSpec("shredder", "decks/shredder/PROTOTYPE_0.1.txt")


def replay(spec: GameSpec) -> tuple[dict[str, object], str]:
    original = run_smoke_game(ROOT, spec)
    repeated = run_smoke_game(ROOT, spec)
    digest = stable_digest(original)
    if original.get("error") or repeated.get("error") or digest != stable_digest(repeated):
        raise ValueError(f"diagnostic/replay mismatch: {spec.game_id}")
    return original, digest


def main() -> None:
    alliance_spec = GameSpec(
        "issue289-alliance-repro-michelangelo-raphael",
        "issue289-alliance-equipment-diagnostic",
        3032,
        "michelangelo-first",
        (MICHELANGELO, RAPHAEL),
    )
    alliance_game, alliance_digest = replay(alliance_spec)
    event_kinds = {
        event["event_id"]: event["rules_event"]
        for event in alliance_game["events"]
        if event["event"] == "rules_event"
    }
    illegal = [
        event
        for event in alliance_game["events"]
        if event["event"] == "trigger_pending"
        and event.get("oracle_fragment", "").startswith("Alliance — ")
        and event_kinds.get(event["event_id"]) != "creature_entered"
    ]
    if illegal:
        raise ValueError("noncreature entry still queued the Wingnut Alliance trigger")
    games = []
    for opponent in (RAPHAEL, SHREDDER):
        for first, second in ((CASEY, opponent), (opponent, CASEY)):
            spec = GameSpec(
                f"issue289-equipment-{first.display_id}-{second.display_id}",
                "issue289-alliance-equipment-diagnostic",
                3045,
                f"{first.display_id}-first",
                (first, second),
            )
            original, digest = replay(spec)
            games.append(
                {
                    "game_id": spec.game_id,
                    "seed": spec.seed,
                    "first_player": first.display_id,
                    "replay_equal": True,
                    "result_digest": digest,
                    "event_count": len(original["events"]),
                    "equipment_attached": [
                        {key: event[key] for key in ("stack_object_id", "source_id", "target_id")}
                        for event in original["events"]
                        if event["event"] == "equipment_attached"
                        and event.get("card") == "Improvised Arsenal"
                    ],
                    "scaled_power": [
                        {
                            key: event[key]
                            for key in ("source_object_id", "target_object_id", "power")
                        }
                        for event in original["events"]
                        if event["event"] == "pt_static_team_modifier_changed"
                        and event.get("source") == "Improvised Arsenal"
                    ],
                    "runtime_error": None,
                }
            )
    result = {
        "kind": "diagnostic_only_not_balance_evidence",
        "semantic_runtime_sha256": identity()["aggregate_semantic_runtime_sha256"],
        "alliance_reproduction": {
            "game_id": alliance_spec.game_id,
            "seed": alliance_spec.seed,
            "historical_failure": "permanent_entered_noncreature_queued_creature_entered_alliance",
            "replay_equal": True,
            "result_digest": alliance_digest,
            "runtime_error": None,
            "invalid_noncreature_alliance_triggers": len(illegal),
        },
        "equipment_game_count": len(games),
        "total_replay_count": len(games) + 1,
        "games": games,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "games": len(games) + 1,
                "replays": len(games) + 1,
                "errors": 0,
                "equipment_attachments": sum(len(g["equipment_attached"]) for g in games),
                "scaled_power_events": sum(len(g["scaled_power"]) for g in games),
            }
        )
    )


if __name__ == "__main__":
    main()
