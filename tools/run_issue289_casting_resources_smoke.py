"""Small mirrored frozen-deck resource diagnostics with exact deterministic replay."""

from __future__ import annotations

import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_CASTING_RESOURCES_SMOKE.json"
KRANG = DeckSpec("krang", "docs/objective-balance-lab/baselines/KRANG_OBL_BASELINE_004.txt")
MICHELANGELO = DeckSpec("michelangelo", "decks/michelangelo/PROTOTYPE_0.1.txt")
CASEY = DeckSpec("casey_jones", "docs/objective-balance-lab/candidates/CASEY_JONES_OBL_R2_B.txt")


def main() -> None:
    games = []
    for pair in ((KRANG, MICHELANGELO), (KRANG, CASEY)):
        for first, second in (pair, pair[::-1]):
            spec = GameSpec(
                f"issue289-casting-resources-{first.display_id}-{second.display_id}",
                "issue289-casting-resources-diagnostic",
                3021,
                f"{first.display_id}-first",
                (first, second),
            )
            original = run_smoke_game(ROOT, spec)
            replay = run_smoke_game(ROOT, spec)
            digest = stable_digest(original)
            if original.get("error") or replay.get("error") or digest != stable_digest(replay):
                raise ValueError(f"diagnostic or replay failed: {spec.game_id}")
            events = original["events"]
            discounts = [e for e in events if e["event"] == "casting_cost_reduced"]
            games.append(
                {
                    "game_id": spec.game_id,
                    "seed": spec.seed,
                    "first_player": first.display_id,
                    "replay_equal": True,
                    "result_digest": digest,
                    "event_count": len(events),
                    "cost_reductions": [
                        {
                            "card": e["card"],
                            "printed_generic": e["printed_generic"],
                            "paid_generic": e["paid_generic"],
                            "qualifying_source_count": sum(
                                len(row["qualifying_source_ids"]) for row in e["reductions"]
                            ),
                        }
                        for e in discounts
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
    print(json.dumps({"games": len(games), "replays": len(games), "errors": 0}))


if __name__ == "__main__":
    main()
