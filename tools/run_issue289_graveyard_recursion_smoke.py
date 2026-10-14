"""Four authenticated frozen-deck diagnostics with exact replay verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_GRAVEYARD_RECURSION_SMOKE.json"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
MANIFEST_SHA = "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac"


def frozen_decks() -> dict[str, DeckSpec]:
    if hashlib.sha256(MANIFEST.read_bytes()).hexdigest() != MANIFEST_SHA:
        raise ValueError("Baseline 005 manifest changed")
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))["decks"]
    decks = {}
    for entry in entries:
        if entry["deck_key"] not in {"leonardo", "raphael", "april_oneil"}:
            continue
        source = (ROOT / entry["source_path"]).read_bytes()
        raw_matches = hashlib.sha256(source).hexdigest() == entry["sha256"]
        # Accept only exact historical line-ending conversion where needed.
        crlf_matches = (
            hashlib.sha256(source.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()
            == entry["sha256"]
        )
        if not (raw_matches or crlf_matches):
            raise ValueError("Baseline 005 deck changed")
        decks[entry["deck_key"]] = DeckSpec(entry["deck_key"], entry["source_path"])
    if set(decks) != {"leonardo", "raphael", "april_oneil"}:
        raise ValueError("frozen diagnostic deck missing")
    return decks


def main() -> None:
    decks = frozen_decks()
    specs = [
        GameSpec(
            f"issue289-graveyard-recursion-317-{seats[0].display_id}-{seats[1].display_id}",
            "issue289-diagnostic",
            317,
            f"{seats[0].display_id}-first",
            seats,
        )
        for opponent in (decks["raphael"], decks["april_oneil"])
        for seats in ((decks["leonardo"], opponent), (opponent, decks["leonardo"]))
    ]
    games = []
    for spec in specs:
        first, replay = (run_smoke_game(ROOT, spec) for _ in range(2))
        digest = stable_digest(first)
        if first.get("error") or replay.get("error") or digest != stable_digest(replay):
            raise ValueError(f"diagnostic replay mismatch: {spec.game_id}")
        events = first["events"]
        resolutions = [
            {
                key: event[key]
                for key in (
                    "stack_object_id",
                    "target_ids",
                    "entered",
                    "invalid_target_ids",
                    "oracle_fragment",
                )
            }
            for event in events
            if event["event"] == "graveyard_recursion_resolved"
        ]
        for item in resolutions:
            if not 1 <= len(item["target_ids"]) <= 2:
                raise ValueError("recursion target count malformed")
            if set(item["invalid_target_ids"]) | {
                entry["graveyard_id"] for entry in item["entered"]
            } != set(item["target_ids"]):
                raise ValueError("recursion target resolution mismatch")
            for entry in item["entered"]:
                if not any(
                    event["event"] == "zone_changed"
                    and event.get("reason") == "graveyard_recursion_return"
                    and event["source_object_id"] == entry["graveyard_id"]
                    and event["destination_object_id"] == entry["battlefield_id"]
                    for event in events
                ):
                    raise ValueError("recursion entry provenance missing")
        payments = [
            {key: event[key] for key in ("card", "generic", "colored", "source_ids")}
            for event in events
            if event["event"] == "cost_paid" and event.get("card") == "Leonardo's Technique"
        ]
        sneak = [
            {key: event[key] for key in ("card", "mana_source_ids", "returned_attacker_id")}
            for event in events
            if event["event"] == "sneak_cost_paid" and event.get("card") == "Leonardo's Technique"
        ]
        if len(resolutions) != len(payments) + len(sneak):
            raise ValueError(f"recursion payment mismatch: {spec.game_id}")
        games.append(
            {
                "game_id": spec.game_id,
                "seed": spec.seed,
                "first_player": spec.seats[0].display_id,
                "replay_equal": True,
                "result_digest": digest,
                "event_count": len(events),
                "normal_payment": payments,
                "sneak_payment": sneak,
                "resolution": resolutions,
                "runtime_error": None,
            }
        )
    if not any(game["resolution"] for game in games):
        raise ValueError("frozen graveyard recursion never executed")
    result = {
        "kind": "diagnostic_only_not_balance_evidence",
        "baseline_manifest_sha256": MANIFEST_SHA,
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
                "normal_payments": sum(len(g["normal_payment"]) for g in games),
                "sneak_payments": sum(len(g["sneak_payment"]) for g in games),
                "resolutions": sum(len(g["resolution"]) for g in games),
            }
        )
    )


if __name__ == "__main__":
    main()
