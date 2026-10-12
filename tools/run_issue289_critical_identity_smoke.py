"""Four mirrored frozen-deck diagnostics with deterministic exact replays."""

from __future__ import annotations

import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_CRITICAL_IDENTITY_SMOKE.json"
RAPHAEL = DeckSpec("raphael", "docs/objective-balance-lab/baselines/RAPHAEL_OBL_BASELINE_002.txt")
BEBOP = DeckSpec(
    "bebop_rocksteady", "docs/objective-balance-lab/baselines/BEBOP_ROCKSTEADY_OBL_BASELINE_005.txt"
)
APRIL = DeckSpec("april_oneil", "decks/april_oneil/PROTOTYPE_0.1.txt")


def main() -> None:
    games = []
    for pair in ((BEBOP, RAPHAEL), (APRIL, RAPHAEL)):
        for first, second in (pair, pair[::-1]):
            spec = GameSpec(
                f"issue289-critical-identity-{first.display_id}-{second.display_id}",
                "issue289-critical-identity-diagnostic",
                2991,
                f"{first.display_id}-first",
                (first, second),
            )
            original = run_smoke_game(ROOT, spec)
            replay = run_smoke_game(ROOT, spec)
            digest = stable_digest(original)
            if original.get("error") or replay.get("error") or digest != stable_digest(replay):
                raise ValueError(f"diagnostic or replay failed: {spec.game_id}")
            events = original["events"]
            games.append(
                {
                    "game_id": spec.game_id,
                    "seed": spec.seed,
                    "first_player": first.display_id,
                    "replay_equal": True,
                    "result_digest": digest,
                    "event_count": len(events),
                    "linked_exile": sum(e["event"] == "raphael_linked_exile" for e in events),
                    "linked_permission": sum(
                        e["event"] == "raphael_play_permission_created" for e in events
                    ),
                    "class_discard_damage": sum(
                        e["event"] == "class_discard_damage_resolved" for e in events
                    ),
                    "class_search": sum(e["event"] == "class_card_searched" for e in events),
                    "conditional_removal": sum(
                        e["event"] == "conditional_removal_resolved" for e in events
                    ),
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
    print(json.dumps({"games": len(games), "replays": len(games), "errors": 0}))


if __name__ == "__main__":
    main()
