"""Four bounded Baseline 005 games and replays for combat graveyard trigger telemetry."""

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
OVERLAY = DOCS / "ISSUE_289_COMBAT_GRAVEYARD_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_COMBAT_GRAVEYARD_CALIBRATION_READINESS.json"
OUTPUT = DOCS / "ISSUE_289_COMBAT_GRAVEYARD_SMOKE.json"
NAME = "Shark Shredder, Killer Clone"


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
    decks = {}
    for deck in manifest["decks"]:
        raw = (ROOT / deck["source_path"]).read_bytes()
        crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        if deck["sha256"] not in {
            hashlib.sha256(raw).hexdigest(),
            hashlib.sha256(crlf).hexdigest(),
        }:
            raise ValueError("frozen deck differs from authenticated manifest")
        decks[deck["deck_key"]] = DeckSpec(deck["deck_key"], deck["source_path"])
    if len(decks) != 10:
        raise ValueError("Baseline 005 is incomplete")
    games = []
    for left, right, seed in (("shredder", "splinter", 326), ("splinter", "bebop_rocksteady", 333)):
        for seats in ((decks[left], decks[right]), (decks[right], decks[left])):
            spec = GameSpec(
                f"issue289-combat-graveyard-{seats[0].display_id}-{seats[1].display_id}-{seed}",
                "issue289-diagnostic-only",
                seed,
                f"{seats[0].display_id}-first",
                seats,
            )
            first, replay = (run_smoke_game(ROOT, spec) for _ in range(2))
            if (
                first.get("error")
                or replay.get("error")
                or stable_digest(first) != stable_digest(replay)
            ):
                raise ValueError(f"frozen replay failed: {spec.game_id}: {first.get('error')}")
            events = first["events"]
            combat = [e for e in events if e["event"] == "combat_graveyard_target_selected"]
            resolved = [e for e in events if e["event"] == "combat_graveyard_attacker_resolved"]
            if len(resolved) > len(combat):
                raise ValueError("resolution lacks trigger target-selection provenance")
            if any(e["event_id"] not in {c["event_id"] for c in combat} for e in resolved):
                raise ValueError("resolution lacks authenticated combat event")
            games.append(
                {
                    "game_id": spec.game_id,
                    "first_player": seats[0].display_id,
                    "second_player": seats[1].display_id,
                    "seed": seed,
                    "result_digest": stable_digest(first),
                    "replay_equal": True,
                    "ending_turn": first["turn"],
                    "event_count": len(events),
                    "shark_casts": sum(
                        e["event"] == "spell_cast" and e.get("card") == NAME for e in events
                    ),
                    "combat_player_hits": sum(
                        e["event"] == "combat_damage_player" and e.get("source") == NAME
                        for e in events
                    ),
                    "graveyard_targets": len(combat),
                    "graveyard_resolutions": len(resolved),
                    "attacking_entries": sum(bool(e["attacking"]) for e in resolved),
                    "runtime_error": None,
                }
            )
    OUTPUT.write_text(
        json.dumps(
            {
                "schema": "issue289-combat-graveyard-smoke-v1",
                "kind": "diagnostic_only_not_balance_evidence",
                "baseline_id": "OBL-BASELINE-005",
                "manifest_sha256": sha(MANIFEST),
                "original_ledger_sha256": sha(LEDGER),
                "checkpoint_overlay_sha256": sha(OVERLAY),
                "semantic_runtime_sha256": runtime,
                "game_count": len(games),
                "deterministic_replay_count": len(games),
                "games": games,
                "calibration_readiness": "BLOCKED",
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "games": len(games),
                "replays": len(games),
                "casts": sum(g["shark_casts"] for g in games),
                "hits": sum(g["combat_player_hits"] for g in games),
                "entries": sum(g["attacking_entries"] for g in games),
                "runtime": runtime,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
