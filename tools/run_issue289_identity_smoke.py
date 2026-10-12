"""Frozen-deck identity diagnostics only; mirrored starts and exact deterministic replays."""

from __future__ import annotations

import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_IDENTITY_SMOKE.json"
RAPHAEL = DeckSpec("raphael", "docs/objective-balance-lab/baselines/RAPHAEL_OBL_BASELINE_002.txt")
BEPOP = DeckSpec(
    "bebop_rocksteady", "docs/objective-balance-lab/baselines/BEBOP_ROCKSTEADY_OBL_BASELINE_005.txt"
)
APRIL = DeckSpec("april_oneil", "decks/april_oneil/PROTOTYPE_0.1.txt")
PAIRS = ((BEPOP, RAPHAEL), (APRIL, RAPHAEL))


def main() -> None:
    games = []
    for pair in PAIRS:
        for first, second in (pair, pair[::-1]):
            spec = GameSpec(
                f"issue289-identity-{first.display_id}-{second.display_id}",
                "issue289-identity-diagnostic",
                2981,
                f"{first.display_id}-first",
                (first, second),
            )
            original = run_smoke_game(ROOT, spec)
            replay = run_smoke_game(ROOT, spec)
            digest = stable_digest(original)
            if original.get("error") or replay.get("error") or digest != stable_digest(replay):
                raise ValueError(f"diagnostic game or replay failed: {spec.game_id}")
            events = original["events"]
            games.append(
                {
                    "game_id": spec.game_id,
                    "first_player": first.display_id,
                    "seed": spec.seed,
                    "replay_equal": True,
                    "result_digest": digest,
                    "event_count": len(events),
                    "combat_choice_resolutions": sum(
                        e["event"] == "combat_discard_or_sacrifice_resolved" for e in events
                    ),
                    "linked_exile_events": sum(
                        e["event"] == "raphael_linked_exile" for e in events
                    ),
                    "linked_permission_events": sum(
                        e["event"] == "raphael_play_permission_created" for e in events
                    ),
                    "end_step_draw_resolutions": sum(
                        e["event"] == "end_step_spell_types_draw_resolved" for e in events
                    ),
                    "runtime_error": None,
                }
            )
    OUTPUT.write_text(
        json.dumps(
            {
                "kind": "diagnostic_only_not_balance_evidence",
                "semantic_runtime_sha256": identity()["aggregate_semantic_runtime_sha256"],
                "game_count": len(games),
                "replay_count": len(games),
                "games": games,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"game_count": len(games), "replay_count": len(games), "runtime_errors": 0}))


if __name__ == "__main__":
    main()
