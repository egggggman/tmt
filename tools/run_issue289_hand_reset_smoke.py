"""Four authenticated frozen-deck diagnostics with exact replay verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_HAND_RESET_SMOKE.json"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
MANIFEST_SHA = "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac"


def frozen_decks() -> dict[str, DeckSpec]:
    if hashlib.sha256(MANIFEST.read_bytes()).hexdigest() != MANIFEST_SHA:
        raise ValueError("Baseline 005 manifest changed")
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))["decks"]
    decks = {}
    for entry in entries:
        if entry["deck_key"] not in {"raphael", "splinter", "april_oneil"}:
            continue
        source = (ROOT / entry["source_path"]).read_bytes()
        raw_matches = hashlib.sha256(source).hexdigest() == entry["sha256"]
        # Git checks out the historical Splinter CRLF prototype as LF.
        crlf_matches = (
            hashlib.sha256(source.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()
            == entry["sha256"]
        )
        if not (raw_matches or crlf_matches):
            raise ValueError("Baseline 005 deck changed")
        decks[entry["deck_key"]] = DeckSpec(entry["deck_key"], entry["source_path"])
    if set(decks) != {"raphael", "splinter", "april_oneil"}:
        raise ValueError("frozen diagnostic deck missing")
    return decks


def main() -> None:
    decks = frozen_decks()
    specs = [
        GameSpec(
            f"issue289-hand-reset-314-{seats[0].display_id}-{seats[1].display_id}",
            "issue289-diagnostic",
            314,
            f"{seats[0].display_id}-first",
            seats,
        )
        for opponent in (decks["splinter"], decks["april_oneil"])
        for seats in ((decks["raphael"], opponent), (opponent, decks["raphael"]))
    ]
    games = []
    for spec in specs:
        first, replay = (run_smoke_game(ROOT, spec) for _ in range(2))
        digest = stable_digest(first)
        if first.get("error") or replay.get("error") or digest != stable_digest(replay):
            raise ValueError(f"diagnostic replay mismatch: {spec.game_id}")
        events = first["events"]
        resets = [
            {
                key: event[key]
                for key in (
                    "stack_object_id",
                    "apnap_order",
                    "choices",
                    "discarded",
                    "drawn",
                    "draw_quantity",
                    "draw_succeeded",
                    "oracle_fragment",
                )
            }
            for event in events
            if event["event"] == "optional_hand_reset_resolved"
        ]
        for item in resets:
            if item["apnap_order"] not in ([0, 1], [1, 0]):
                raise ValueError("hand reset APNAP order malformed")
            if item["draw_quantity"] != 7:
                raise ValueError("hand reset draw quantity changed")
            for index in (0, 1):
                if not item["choices"][index]["discard_and_draw"] and (
                    item["discarded"][index]["zone_ids"] or item["drawn"][index]["hand_ids"]
                ):
                    raise ValueError("declining player was changed")
            for group in item["discarded"]:
                for source, destination in group["zone_ids"]:
                    if not any(
                        event["event"] == "zone_changed"
                        and event.get("reason") == "optional_hand_reset_discard"
                        and event["source_object_id"] == source
                        and event["destination_object_id"] == destination
                        for event in events
                    ):
                        raise ValueError("discard provenance missing")
        payments = [
            {key: event[key] for key in ("card", "generic", "colored", "source_ids")}
            for event in events
            if event["event"] == "cost_paid" and event.get("card") == "Raphael's Technique"
        ]
        sneak = [
            {key: event[key] for key in ("card", "mana_source_ids", "returned_attacker_id")}
            for event in events
            if event["event"] == "sneak_cost_paid" and event.get("card") == "Raphael's Technique"
        ]
        if len(resets) != len(payments) + len(sneak):
            raise ValueError(f"reset payment mismatch: {spec.game_id}")
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
                "resolution": resets,
                "runtime_error": None,
            }
        )
    if not any(game["resolution"] for game in games):
        raise ValueError("frozen hand reset never executed")
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
