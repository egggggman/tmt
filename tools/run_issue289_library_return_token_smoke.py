"""Run bounded frozen-deck removal diagnostics and deterministic replays."""

from __future__ import annotations

import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity
from run_issue289_temporary_animation_draw_smoke import MANIFEST_SHA, frozen_decks

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_LIBRARY_RETURN_TOKEN_SMOKE.json"


def main() -> None:
    decks = frozen_decks()
    april, raphael, donatello = (decks[key] for key in ("april_oneil", "raphael", "donatello"))
    specs = [
        GameSpec(
            f"issue289-library-return-{seed}-{seats[0].display_id}-{seats[1].display_id}",
            "issue289-diagnostic",
            seed,
            f"{seats[0].display_id}-first",
            seats,
        )
        for seed, opponent in ((3129, raphael), (3130, raphael), (3130, donatello))
        for seats in ((april, opponent), (opponent, april))
    ]
    games = []
    for spec in specs:
        first, replay = (run_smoke_game(ROOT, spec) for _ in range(2))
        digest = stable_digest(first)
        if first.get("error") or replay.get("error") or digest != stable_digest(replay):
            raise ValueError(f"diagnostic replay mismatch: {spec.game_id}")
        events = first["events"]
        casts = sum(
            e["event"] == "spell_cast" and e.get("card") == "Return to the Sewers" for e in events
        )
        payment = [
            {key: e[key] for key in ("card", "generic", "colored", "source_ids")}
            for e in events
            if e["event"] == "cost_paid" and e.get("card") == "Return to the Sewers"
        ]
        resolution = [
            {
                key: e[key]
                for key in (
                    "stack_object_id",
                    "target_id",
                    "target_owner",
                    "chosen_position",
                    "destination_id",
                    "token_ids",
                )
            }
            for e in events
            if e["event"] == "targeted_library_return_token_resolved"
        ]
        movements = [
            {
                key: e[key]
                for key in (
                    "source_object_id",
                    "destination_object_id",
                    "library_position",
                    "destination_zone",
                )
            }
            for e in events
            if e["event"] == "zone_changed" and e.get("reason") == "targeted_library_return"
        ]
        if casts != len(payment) or len(movements) != len(resolution):
            raise ValueError(f"incomplete event provenance: {spec.game_id}")
        for result in resolution:
            if not any(
                move["source_object_id"] == result["target_id"]
                and move["destination_object_id"] == result["destination_id"]
                and move["library_position"] == result["chosen_position"]
                for move in movements
            ):
                raise ValueError(f"unlinked zone transition: {spec.game_id}")
        games.append(
            {
                "game_id": spec.game_id,
                "seed": spec.seed,
                "first_player": spec.seats[0].display_id,
                "replay_equal": True,
                "result_digest": digest,
                "event_count": len(events),
                "frozen_source_casts": casts,
                "payment": payment,
                "resolution": resolution,
                "target_movement": movements,
                "runtime_error": None,
            }
        )
    if not any(game["resolution"] for game in games):
        raise ValueError("frozen diagnostic did not execute the selected family")
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
                "resolutions": sum(len(game["resolution"]) for game in games),
            }
        )
    )


if __name__ == "__main__":
    main()
