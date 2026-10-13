"""Mirrored unchanged Baseline 005 diagnostics with exact deterministic replays."""

from __future__ import annotations

import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_TARGETED_REMOVAL_SMOKE.json"
SHREDDER = DeckSpec(
    "shredder", "docs/objective-balance-lab/baselines/SHREDDER_OBL_BASELINE_003.txt"
)
SPLINTER = DeckSpec("splinter", "decks/splinter/PROTOTYPE_0.1.txt")
APRIL = DeckSpec("april_oneil", "decks/april_oneil/PROTOTYPE_0.1.txt")


def main() -> None:
    games = []
    for pair in ((SPLINTER, SHREDDER), (APRIL, SHREDDER)):
        for first, second in (pair, pair[::-1]):
            spec = GameSpec(
                f"issue289-targeted-removal-{first.display_id}-{second.display_id}",
                "issue289-targeted-removal-diagnostic",
                3031,
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
                    "targeted_exile": sum(
                        e["event"] == "zone_changed" and e.get("reason") == "targeted_removal_exile"
                        for e in events
                    ),
                    "direct_removal_casts": sum(
                        e["event"] == "spell_cast"
                        and e.get("card") in {"Death in the Family", "Shredder's Technique"}
                        for e in events
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
