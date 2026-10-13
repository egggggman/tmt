"""Mirrored frozen-deck diagnostics and byte-stable deterministic replays."""

from __future__ import annotations

import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_RESTRICTED_MANA_SMOKE.json"
CASEY = DeckSpec("casey_jones", "docs/objective-balance-lab/candidates/CASEY_JONES_OBL_R2_B.txt")
KRANG = DeckSpec("krang", "docs/objective-balance-lab/baselines/KRANG_OBL_BASELINE_004.txt")
RAPHAEL = DeckSpec("raphael", "decks/raphael/PROTOTYPE_0.1.txt")


def main() -> None:
    games = []
    for opponent in (KRANG, RAPHAEL):
        for first, second in ((CASEY, opponent), (opponent, CASEY)):
            spec = GameSpec(
                f"issue289-restricted-mana-{first.display_id}-{second.display_id}",
                "issue289-restricted-mana-diagnostic",
                3022,
                f"{first.display_id}-first",
                (first, second),
            )
            original = run_smoke_game(ROOT, spec)
            replay = run_smoke_game(ROOT, spec)
            digest = stable_digest(original)
            if original.get("error") or replay.get("error") or digest != stable_digest(replay):
                raise ValueError(f"diagnostic/replay mismatch: {spec.game_id}")
            events = original["events"]
            productions = [event for event in events if event["event"] == "floating_mana_produced"]
            games.append(
                {
                    "game_id": spec.game_id,
                    "seed": spec.seed,
                    "first_player": first.display_id,
                    "replay_equal": True,
                    "result_digest": digest,
                    "event_count": len(events),
                    "restricted_productions": [
                        {
                            key: event[key]
                            for key in (
                                "source_id",
                                "event_id",
                                "color",
                                "quantity",
                                "allowed_spending",
                            )
                        }
                        for event in productions
                        if event["allowed_spending"]
                    ],
                    "mana_payment_events": [
                        {"event": event["event"], "floating_event_ids": event["floating_event_ids"]}
                        for event in events
                        if event["event"] in {"cost_paid", "activation_cost_paid"}
                        and event.get("floating_event_ids")
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
                "restricted_productions": sum(len(g["restricted_productions"]) for g in games),
            }
        )
    )


if __name__ == "__main__":
    main()
