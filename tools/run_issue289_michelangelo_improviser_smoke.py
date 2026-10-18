"""Authenticated frozen-deck replay diagnostics for Michelangelo Improviser."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/cardcade"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
OVERLAY = DOCS / "ISSUE_289_MICHELANGELO_IMPROVISER_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_MICHELANGELO_IMPROVISER_CALIBRATION_READINESS.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest, overlay, readiness = (
        json.loads(path.read_text()) for path in (MANIFEST, OVERLAY, READINESS)
    )
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    if (
        runtime != overlay["semantic_runtime_sha256"]
        or sha(OVERLAY) != readiness["checkpoint_overlay_sha256"]
    ):
        raise ValueError("runtime or overlay lineage mismatch")
    decks = {
        deck["deck_key"]: DeckSpec(deck["deck_key"], deck["source_path"])
        for deck in manifest["decks"]
    }
    games = []
    for opponent, seed in (("raphael", 6011), ("shredder", 6012), ("casey_jones", 6013)):
        for seats in (
            (decks["michelangelo"], decks[opponent]),
            (decks[opponent], decks["michelangelo"]),
        ):
            spec = GameSpec(
                f"issue289-improviser-{seats[0].display_id}-{seats[1].display_id}-{seed}",
                "issue289-diagnostic-only",
                seed,
                f"{seats[0].display_id}-first",
                seats,
            )
            first, replay = run_smoke_game(ROOT, spec), run_smoke_game(ROOT, spec)
            if (
                first.get("error")
                or replay.get("error")
                or stable_digest(first) != stable_digest(replay)
            ):
                raise ValueError(f"deterministic replay failed: {spec.game_id}")
            events = first["events"]
            games.append(
                {
                    "game_id": spec.game_id,
                    "seed": seed,
                    "seats": [seat.display_id for seat in seats],
                    "result_sha256": stable_digest(first),
                    "damage_opportunities": [
                        event
                        for event in events
                        if event["event"] == "combat_damage_player"
                        and event.get("source") == "Michelangelo, Improviser"
                    ],
                    "trigger_events": [
                        event
                        for event in events
                        if event["event"] == "trigger_pending"
                        and event.get("source") == "Michelangelo, Improviser"
                    ],
                    "choices": [
                        event
                        for event in events
                        if event["event"] == "combat_hand_battlefield_entry_choice"
                    ],
                    "creature_entries": [
                        event
                        for event in events
                        if event["event"] == "combat_hand_battlefield_entry_resolved"
                        and event.get("creature_id") is not None
                    ],
                    "land_entries": [
                        event
                        for event in events
                        if event["event"] == "combat_hand_battlefield_entry_resolved"
                        and event.get("land_id") is not None
                    ],
                }
            )
    output = {
        "schema": "issue289-michelangelo-improviser-frozen-diagnostic-v1",
        "baseline_id": "OBL-BASELINE-005",
        "purpose": "mechanical_and_pilot_exposure_only_no_balance_inference",
        "semantic_runtime_sha256": runtime,
        "manifest_sha256": sha(MANIFEST),
        "ledger_sha256": sha(LEDGER),
        "overlay_sha256": sha(OVERLAY),
        "replay_count": len(games),
        "games": games,
    }
    path = DOCS / "ISSUE_289_MICHELANGELO_IMPROVISER_SMOKE.json"
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(
        json.dumps(
            {
                "games": len(games),
                "damage_opportunities": sum(len(game["damage_opportunities"]) for game in games),
                "triggers": sum(len(game["trigger_events"]) for game in games),
                "choices": sum(len(game["choices"]) for game in games),
                "creature_entries": sum(len(game["creature_entries"]) for game in games),
                "land_entries": sum(len(game["land_entries"]) for game in games),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
