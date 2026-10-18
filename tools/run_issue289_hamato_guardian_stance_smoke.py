"""Authenticated frozen-deck replay diagnostics for Hamato Guardian Stance."""

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
OVERLAY = DOCS / "ISSUE_289_HAMATO_GUARDIAN_STANCE_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_HAMATO_GUARDIAN_STANCE_CALIBRATION_READINESS.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    manifest, overlay, readiness = (
        json.loads(p.read_text()) for p in (MANIFEST, OVERLAY, READINESS)
    )
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    if (
        runtime != overlay["semantic_runtime_sha256"]
        or sha(OVERLAY) != readiness["checkpoint_overlay_sha256"]
    ):
        raise ValueError("runtime or overlay lineage mismatch")
    decks = {d["deck_key"]: DeckSpec(d["deck_key"], d["source_path"]) for d in manifest["decks"]}
    games = []
    for opponent, seed in (("raphael", 5011), ("shredder", 5012), ("michelangelo", 5013)):
        for seats in ((decks["leonardo"], decks[opponent]), (decks[opponent], decks["leonardo"])):
            spec = GameSpec(
                f"issue289-hamato-{seats[0].display_id}-{seats[1].display_id}-{seed}",
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
                    "seats": [s.display_id for s in seats],
                    "result_sha256": stable_digest(first),
                    "stance_casts": [
                        e for e in events if e.get("card") == "Hamato Guardian Stance"
                    ],
                    "scry_resolutions": [
                        e for e in events if e.get("event") == "targeted_pump_flying_scry_resolved"
                    ],
                }
            )
    out = {
        "schema": "issue289-hamato-guardian-stance-frozen-diagnostic-v1",
        "baseline_id": "OBL-BASELINE-005",
        "purpose": "mechanical_and_pilot_exposure_only_no_balance_inference",
        "semantic_runtime_sha256": runtime,
        "manifest_sha256": sha(MANIFEST),
        "ledger_sha256": sha(LEDGER),
        "overlay_sha256": sha(OVERLAY),
        "replay_count": len(games),
        "games": games,
    }
    path = DOCS / "ISSUE_289_HAMATO_GUARDIAN_STANCE_SMOKE.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(
        json.dumps(
            {
                "games": len(games),
                "casts": sum(len(g["stance_casts"]) for g in games),
                "resolutions": sum(len(g["scry_resolutions"]) for g in games),
            }
        )
    )


if __name__ == "__main__":
    main()
