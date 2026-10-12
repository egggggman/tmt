"""Four mirrored Baseline 005 diagnostic executions with deterministic replays."""

from __future__ import annotations

import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_SHARED_REMOVAL_SMOKE.json"
PAIRS = (
    (
        DeckSpec("raphael", "docs/objective-balance-lab/baselines/RAPHAEL_OBL_BASELINE_002.txt"),
        DeckSpec("casey_jones", "docs/objective-balance-lab/candidates/CASEY_JONES_OBL_R2_B.txt"),
    ),
    (
        DeckSpec(
            "bebop_rocksteady",
            "docs/objective-balance-lab/baselines/BEBOP_ROCKSTEADY_OBL_BASELINE_005.txt",
        ),
        DeckSpec("michelangelo", "decks/michelangelo/PROTOTYPE_0.1.txt"),
    ),
)


def main() -> None:
    games = []
    for pair in PAIRS:
        for first, second in (pair, pair[::-1]):
            spec = GameSpec(
                f"issue289-removal-{first.display_id}-first",
                "issue289-shared-removal-diagnostic",
                2907,
                f"{first.display_id}-first",
                (first, second),
            )
            original = run_smoke_game(ROOT, spec)
            replay = run_smoke_game(ROOT, spec)
            digest = stable_digest(original)
            if original.get("error") or replay.get("error") or digest != stable_digest(replay):
                raise ValueError(f"diagnostic game or replay failed: {spec.game_id}")
            games.append(
                {
                    "game_id": spec.game_id,
                    "first_player": first.display_id,
                    "seed": spec.seed,
                    "replay_equal": True,
                    "result_digest": digest,
                    "event_count": len(original["events"]),
                    "pizza_entry_resolutions": sum(
                        e["event"] == "entry_damage_resolved" for e in original["events"]
                    ),
                    "optional_removal_resolutions": sum(
                        e["event"] == "optional_removal_resolved" for e in original["events"]
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
