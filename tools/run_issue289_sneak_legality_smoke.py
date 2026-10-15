"""Authenticated bounded diagnostics for generic granted-Sneak action legality."""

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
OVERLAY = DOCS / "ISSUE_289_CLASS_ARTIFACT_ANIMATION_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_CLASS_ARTIFACT_ANIMATION_CALIBRATION_READINESS.json"
TRIAGE = DOCS / "ISSUE_289_FAMILY_TRIAGE.json"
OUTPUT = DOCS / "ISSUE_289_SNEAK_LEGALITY_SMOKE.json"
EXPECTED = {
    MANIFEST: "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac",
    LEDGER: "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100",
    OVERLAY: "01ccb63187e614cfeda064a8e1bd388f65df1210a745c9ee3345e76398ad815a",
    TRIAGE: "39e18d36dbfe179c41f8b7bb345b328e8312aae66637f5762a57cda0a70089d3",
}
RUNTIME = "2e140950578ddbfabf9fdb931a7edde800d9775c56c1e54bb438e09317c3ccf6"
PREDECESSOR_FAILURE_DIGEST = "ce34b19eddc71d3b8ffec271be328e7e5871db2213ef68c7c0b320e23f7e3490"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    for path, expected in EXPECTED.items():
        if sha(path) != expected:
            raise ValueError(f"frozen evidence changed: {path}")
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    if runtime != RUNTIME:
        raise ValueError("unexpected semantic runtime")
    overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))
    readiness = json.loads(READINESS.read_text(encoding="utf-8"))
    triage = json.loads(TRIAGE.read_text(encoding="utf-8"))
    failures = [g for g in triage["diagnostic_games"] if g["status"] == "failure"]
    if len(failures) != 1 or failures[0]["snapshot_digest"] != PREDECESSOR_FAILURE_DIGEST:
        raise ValueError("predecessor failure evidence changed")
    if (
        len(overlay["rows"]) != 172
        or overlay["counts"]["priority"].get("P1") != 35
        or readiness["important_blockers"] != 31
        or readiness["unbounded_residual_important"] != 4
        or readiness["checkpoint_overlay_sha256"] != sha(OVERLAY)
    ):
        raise ValueError("readiness lineage changed")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    decks = {}
    for deck in manifest["decks"]:
        raw = (ROOT / deck["source_path"]).read_bytes()
        crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        if deck["sha256"] not in {
            hashlib.sha256(raw).hexdigest(),
            hashlib.sha256(crlf).hexdigest(),
        }:
            raise ValueError(f"frozen deck changed: {deck['deck_key']}")
        decks[deck["deck_key"]] = DeckSpec(deck["deck_key"], deck["source_path"])
    if len(decks) != 10:
        raise ValueError("missing Baseline 005 deck")

    games = []
    for left, right, seed in (
        ("splinter", "shredder", 323),
        ("splinter", "shredder", 326),
        ("splinter", "michelangelo", 323),
    ):
        for seats in ((decks[left], decks[right]), (decks[right], decks[left])):
            game_id = f"issue289-sneak-legality-{seats[0].display_id}-{seats[1].display_id}-{seed}"
            if seed == 326 and seats[0].display_id == "splinter":
                game_id = "issue289-family-triage-splinter-shredder"
            spec = GameSpec(
                game_id,
                "issue289-diagnostic-only",
                seed,
                f"{seats[0].display_id}-first",
                seats,
            )
            first, replay = (run_smoke_game(ROOT, spec) for _ in range(2))
            digest = stable_digest(first)
            if first.get("error") or replay.get("error") or digest != stable_digest(replay):
                raise ValueError(f"failed deterministic frozen replay: {spec.game_id}")
            casts = {
                event.get("stack_object_id"): event
                for event in first["events"]
                if event["event"] == "spell_cast"
            }
            announcements = [
                event for event in first["events"] if event["event"] == "sneak_announced"
            ]
            illegal_grants = [
                event
                for event in announcements
                if event["oracle_fragment"].startswith(
                    "Creature cards in your graveyard have sneak"
                )
                and (
                    event["source_zone"] != "graveyard"
                    or "Creature" not in casts[event["stack_object_id"]]["card_types"]
                )
            ]
            if illegal_grants:
                raise ValueError(f"noncreature or wrong-zone granted Sneak: {spec.game_id}")
            games.append(
                {
                    "game_id": spec.game_id,
                    "first_player": seats[0].display_id,
                    "second_player": seats[1].display_id,
                    "seed": seed,
                    "result_digest": digest,
                    "replay_equal": True,
                    "ending_turn": first["turn"],
                    "event_count": len(first["events"]),
                    "level_three_advancements": sum(
                        e["event"] == "class_level_advanced" and e.get("to_level") == 3
                        for e in first["events"]
                    ),
                    "legal_graveyard_sneak_casts": sum(
                        e["source_zone"] == "graveyard" for e in announcements
                    ),
                    "illegal_granted_sneak_casts": len(illegal_grants),
                    "runtime_error": None,
                }
            )
    report = {
        "schema": "issue289-sneak-legality-diagnostic-v1",
        "kind": "diagnostic_only_not_balance_evidence",
        "baseline_id": "OBL-BASELINE-005",
        "manifest_sha256": sha(MANIFEST),
        "original_ledger_sha256": sha(LEDGER),
        "predecessor_overlay_sha256": sha(OVERLAY),
        "predecessor_triage_sha256": sha(TRIAGE),
        "predecessor_runtime_sha256": overlay["semantic_runtime_sha256"],
        "semantic_runtime_sha256": runtime,
        "row_delta": [],
        "row_count": len(overlay["rows"]),
        "coverage_counts": {"critical": 0, "important": 35, "blockers": 31, "unbounded": 4},
        "predecessor_failure": {
            "first_player": "splinter",
            "second_player": "shredder",
            "seed": 326,
            "snapshot_digest": PREDECESSOR_FAILURE_DIGEST,
            "exception": "noncreature Sneak evidence has a battlefield result",
        },
        "game_count": len(games),
        "deterministic_replay_count": len(games),
        "games": games,
        "calibration_readiness": "BLOCKED",
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "games": len(games),
                "replays": len(games),
                "graveyard_sneak_casts": sum(g["legal_graveyard_sneak_casts"] for g in games),
                "illegal_grant_casts": sum(g["illegal_granted_sneak_casts"] for g in games),
                "runtime": runtime,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
