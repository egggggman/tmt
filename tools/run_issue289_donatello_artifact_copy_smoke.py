"""Authenticated Donatello combat-damage artifact-copy diagnostics."""

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
OVERLAY = DOCS / "ISSUE_289_DONATELLO_ARTIFACT_COPY_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_DONATELLO_ARTIFACT_COPY_CALIBRATION_READINESS.json"
OUTPUT = DOCS / "ISSUE_289_DONATELLO_ARTIFACT_COPY_SMOKE.json"
NAME = "Donatello, Gadget Master"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest, overlay, readiness = (
        json.loads(path.read_text()) for path in (MANIFEST, OVERLAY, READINESS)
    )
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    if (
        sha(MANIFEST) != overlay["baseline_manifest_sha256"]
        or sha(LEDGER) != overlay["base_ledger_sha256"]
        or sha(OVERLAY) != readiness["checkpoint_overlay_sha256"]
        or runtime != overlay["semantic_runtime_sha256"]
        or len(overlay["rows"]) != 172
    ):
        raise ValueError("frozen runtime, manifest or ledger lineage changed")
    decks = {
        deck["deck_key"]: DeckSpec(deck["deck_key"], deck["source_path"])
        for deck in manifest["decks"]
    }
    games = []
    for opponent, seed in (("raphael", 4011), ("shredder", 4012), ("casey_jones", 4013)):
        for seats in ((decks["donatello"], decks[opponent]), (decks[opponent], decks["donatello"])):
            spec = GameSpec(
                f"issue289-donatello-artifact-copy-{seats[0].display_id}-{seats[1].display_id}-{seed}",
                "issue289-diagnostic-only",
                seed,
                f"{seats[0].display_id}-first",
                seats,
            )
            first = run_smoke_game(ROOT, spec)
            replay = run_smoke_game(ROOT, spec)
            if (
                first.get("error")
                or replay.get("error")
                or stable_digest(first) != stable_digest(replay)
            ):
                raise ValueError(f"frozen replay failed: {spec.game_id}: {first.get('error')}")
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
                        if event["event"] == "combat_damage_player" and event.get("source") == NAME
                    ],
                    "triggers": [
                        event
                        for event in events
                        if event["event"] == "trigger_pending" and event.get("source") == NAME
                    ],
                    "target_choices": [
                        event
                        for event in events
                        if event["event"] == "combat_artifact_copy_target_selected"
                    ],
                    "resolutions": [
                        event
                        for event in events
                        if event["event"] == "combat_artifact_copy_resolved"
                    ],
                    "copied_tokens": [
                        event
                        for event in events
                        if event["event"] == "copied_artifact_token_created"
                        and event.get("oracle_fragment", "").startswith("Whenever Donatello")
                    ],
                }
            )
    artifact = {
        "schema": "issue289-donatello-artifact-copy-frozen-diagnostic-v1",
        "baseline_id": "OBL-BASELINE-005",
        "purpose": "mechanical_and_pilot_exposure_only_no_balance_inference",
        "semantic_runtime_sha256": runtime,
        "manifest_sha256": sha(MANIFEST),
        "ledger_sha256": sha(LEDGER),
        "overlay_sha256": sha(OVERLAY),
        "replay_count": len(games),
        "games": games,
    }
    OUTPUT.write_text(json.dumps(artifact, indent=2) + "\n")
    print(
        json.dumps(
            {
                "games": len(games),
                "damage_opportunities": sum(len(game["damage_opportunities"]) for game in games),
                "triggers": sum(len(game["triggers"]) for game in games),
                "target_choices": sum(len(game["target_choices"]) for game in games),
                "resolutions": sum(len(game["resolutions"]) for game in games),
                "copied_tokens": sum(len(game["copied_tokens"]) for game in games),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
