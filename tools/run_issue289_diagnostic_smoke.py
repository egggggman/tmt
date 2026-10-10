"""Two mirrored Baseline 005 diagnostic games and exact deterministic replays."""

from __future__ import annotations

import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_DEATHTOUCH_DIAGNOSTIC_SMOKE.json"
DECKS = (
    DeckSpec(
        "bebop_rocksteady",
        "docs/objective-balance-lab/baselines/BEBOP_ROCKSTEADY_OBL_BASELINE_005.txt",
    ),
    DeckSpec("shredder", "docs/objective-balance-lab/baselines/SHREDDER_OBL_BASELINE_003.txt"),
)


def main() -> None:
    games = []
    for first, second in (DECKS, DECKS[::-1]):
        spec = GameSpec(
            f"issue289-deathtouch-{first.display_id}-first",
            "issue289-deathtouch-diagnostic",
            289,
            f"{first.display_id}-first",
            (first, second),
        )
        original = run_smoke_game(ROOT, spec)
        replay = run_smoke_game(ROOT, spec)
        digest = stable_digest(original)
        if original.get("error") or replay.get("error") or digest != stable_digest(replay):
            raise ValueError(f"diagnostic game failed or replay diverged: {spec.game_id}")
        games.append(
            {
                "game_id": spec.game_id,
                "first_player": first.display_id,
                "seed": spec.seed,
                "replay_equal": True,
                "result_digest": digest,
                "event_count": len(original["events"]),
                "runtime_error": None,
            }
        )
    output = {
        "kind": "diagnostic_only_not_balance_evidence",
        "semantic_runtime_sha256": identity()["aggregate_semantic_runtime_sha256"],
        "game_count": 2,
        "replay_count": 2,
        "games": games,
    }
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"game_count": 2, "replay_count": 2, "runtime_errors": 0}))


if __name__ == "__main__":
    main()
