"""Authenticated frozen-deck diagnostics for artifact-entry self counters."""

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
OVERLAY = DOCS / "ISSUE_289_ARTIFACT_ENTRY_COUNTER_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_ARTIFACT_ENTRY_COUNTER_CALIBRATION_READINESS.json"
OUTPUT = DOCS / "ISSUE_289_ARTIFACT_ENTRY_COUNTER_SMOKE.json"
NAME = "Donatello, Way with Machines"
EFFECT = "Whenever an artifact you control enters, put a +1/+1 counter on Donatello."


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
    for left, right, seed in (
        ("donatello", "shredder", 3006),
        ("donatello", "raphael", 3021),
        ("donatello", "leonardo", 3034),
    ):
        for seats in ((decks[left], decks[right]), (decks[right], decks[left])):
            spec = GameSpec(
                f"issue289-artifact-entry-counter-{seats[0].display_id}-{seats[1].display_id}-{seed}",
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
            resolutions = [e for e in events if e["event"] == "artifact_entry_counter_resolved"]
            original_events = {e["event_id"]: e for e in events if e["event"] == "rules_event"}
            placements = [
                e
                for e in events
                if e["event"] == "counters_placed"
                and e.get("source") == NAME
                and e.get("oracle_fragment") == EFFECT
                and e.get("counter_type") == "+1/+1"
            ]
            battlefield_ids = {
                e["destination_object_id"]
                for e in events
                if e["event"] == "zone_changed"
                and e.get("destination_zone") == "battlefield"
                and e.get("card") == NAME
            }
            if any(
                e["source_id"] not in battlefield_ids
                or e["event_id"] not in original_events
                or original_events[e["event_id"]]["subject_ids"] != [e["entered_id"]]
                or original_events[e["event_id"]]["rules_event"]
                not in {"creature_entered", "permanent_entered"}
                or not any(
                    characteristic["object_id"] == e["entered_id"]
                    and "Artifact" in characteristic["type_line"]
                    for characteristic in original_events[e["event_id"]][
                        "battlefield_characteristics"
                    ]
                )
                or not any(
                    source["object_id"] == e["source_id"]
                    for source in original_events[e["event_id"]]["battlefield_authority"]
                )
                or e["counter_type"] != "+1/+1"
                or e["quantity"] != 1
                for e in resolutions
            ) or len(resolutions) != len(placements):
                raise ValueError("artifact-entry resolution lacks source/entry provenance")
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
                    "source_casts": sum(
                        e["event"] == "spell_cast" and e.get("card") == NAME for e in events
                    ),
                    "counter_resolutions": len(resolutions),
                    "entry_event_ids": [e["event_id"] for e in resolutions],
                    "source_absent_resolutions": sum(
                        e["event"] == "artifact_entry_counter_source_absent" for e in events
                    ),
                    "affected_creature_ids": sorted({e["source_id"] for e in resolutions}),
                    "runtime_error": None,
                }
            )
    OUTPUT.write_text(
        json.dumps(
            {
                "schema": "issue289-artifact-entry-counter-smoke-v1",
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
                "casts": sum(g["source_casts"] for g in games),
                "counter_resolutions": sum(g["counter_resolutions"] for g in games),
                "source_absent_resolutions": sum(g["source_absent_resolutions"] for g in games),
                "runtime": runtime,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
