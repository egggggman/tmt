"""Bounded authenticated frozen-deck trace of Robot-token execution, not balance."""

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
OVERLAY = DOCS / "ISSUE_289_ROBOT_TOKEN_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_ROBOT_TOKEN_CALIBRATION_READINESS.json"
OUTPUT = DOCS / "ISSUE_289_ROBOT_TOKEN_SMOKE.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    overlay = json.loads(OVERLAY.read_text())
    readiness = json.loads(READINESS.read_text())
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    if (
        sha(MANIFEST) != overlay["baseline_manifest_sha256"]
        or sha(LEDGER) != overlay["base_ledger_sha256"]
        or sha(OVERLAY) != readiness["checkpoint_overlay_sha256"]
        or runtime != overlay["semantic_runtime_sha256"]
        or len(overlay["rows"]) != 172
    ):
        raise ValueError("frozen runtime or ledger lineage changed")
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
        raise ValueError("Baseline 005 is incomplete")

    games = []
    for opponent in ("donatello", "bebop_rocksteady", "shredder"):
        for seats in (
            (decks["casey_jones"], decks[opponent]),
            (decks[opponent], decks["casey_jones"]),
        ):
            spec = GameSpec(
                f"issue289-robot-token-{seats[0].display_id}-{seats[1].display_id}-326",
                "issue289-diagnostic-only",
                326,
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
            kinds = {e["event_id"]: e["rules_event"] for e in events if e["event"] == "rules_event"}
            triggers = [
                e
                for e in events
                if e["event"] == "trigger_pending"
                and e.get("source") in {"Mouser Foundry", "Ravenous Robots"}
                and "Robot artifact creature token" in e.get("oracle_fragment", "")
            ]
            source_to_kind = {
                e["destination_object_id"]: e["card"]
                for e in events
                if e["event"] == "zone_changed"
                and e.get("destination_zone") == "battlefield"
                and e.get("card") in {"Mouser Foundry", "Ravenous Robots"}
            }
            token_events = [
                e
                for e in events
                if e["event"] == "tokens_created"
                and e.get("source_card") in {"Mouser Foundry", "Ravenous Robots"}
            ]
            trigger_kind_counts = {}
            for trigger in triggers:
                kind = kinds[trigger["event_id"]]
                key = f"{trigger['source']}:{kind}"
                trigger_kind_counts[key] = trigger_kind_counts.get(key, 0) + 1
                if (
                    trigger["source"] == "Ravenous Robots"
                    and kind != "spell_cast"
                    or trigger["source"] == "Mouser Foundry"
                    and kind not in {"permanent_entered", "permanent_left"}
                ):
                    raise ValueError("token trigger has wrong event family")
            if len(token_events) > len(triggers):
                raise ValueError("more resolved tokens than pending triggers")
            if any(e["source_id"] not in source_to_kind for e in token_events):
                # Source may be a former incarnation, but its entry identity must remain recorded.
                raise ValueError("token source lacks permanent incarnation evidence")
            games.append(
                {
                    "game_id": spec.game_id,
                    "first_player": seats[0].display_id,
                    "second_player": seats[1].display_id,
                    "seed": 326,
                    "result_digest": stable_digest(first),
                    "replay_equal": True,
                    "ending_turn": first["turn"],
                    "event_count": len(events),
                    "foundry_casts": sum(
                        e["event"] == "spell_cast" and e.get("card") == "Mouser Foundry"
                        for e in events
                    ),
                    "robots_casts": sum(
                        e["event"] == "spell_cast" and e.get("card") == "Ravenous Robots"
                        for e in events
                    ),
                    "trigger_kind_counts": trigger_kind_counts,
                    "tokens_resolved": len(token_events),
                    "tokens_created": sum(e["quantity"] for e in token_events),
                    "runtime_error": None,
                }
            )
    report = {
        "schema": "issue289-robot-token-smoke-v1",
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
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "games": len(games),
                "replays": len(games),
                "triggers": sum(sum(g["trigger_kind_counts"].values()) for g in games),
                "tokens": sum(g["tokens_created"] for g in games),
                "runtime": runtime,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
