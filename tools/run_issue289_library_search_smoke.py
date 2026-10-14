"""Four frozen-deck library-search diagnostics with exact deterministic replays."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_LIBRARY_SEARCH_SMOKE.json"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
MANIFEST_SHA = "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac"


def frozen_decks() -> dict[str, DeckSpec]:
    if hashlib.sha256(MANIFEST.read_bytes()).hexdigest() != MANIFEST_SHA:
        raise ValueError("Baseline 005 manifest changed")
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))["decks"]
    decks = {}
    for entry in entries:
        if entry["deck_key"] not in {"splinter", "raphael", "april_oneil"}:
            continue
        path = ROOT / entry["source_path"]
        source = path.read_bytes()
        raw_matches = hashlib.sha256(source).hexdigest() == entry["sha256"]
        # Two historical prototype sources were recorded with Windows line endings.
        # Git checks them out as LF; only accept that exact newline conversion.
        crlf_matches = (
            hashlib.sha256(source.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()
            == entry["sha256"]
        )
        if not (raw_matches or crlf_matches):
            raise ValueError("Baseline 005 deck changed")
        decks[entry["deck_key"]] = DeckSpec(entry["deck_key"], entry["source_path"])
    if set(decks) != {"splinter", "raphael", "april_oneil"}:
        raise ValueError("frozen diagnostic deck missing")
    return decks


def main() -> None:
    decks = frozen_decks()
    specs = [
        GameSpec(
            f"issue289-library-search-313-{seats[0].display_id}-{seats[1].display_id}",
            "issue289-diagnostic",
            313,
            f"{seats[0].display_id}-first",
            seats,
        )
        for opponent in (decks["raphael"], decks["april_oneil"])
        for seats in ((decks["splinter"], opponent), (opponent, decks["splinter"]))
    ]
    games = []
    for spec in specs:
        first, replay = (run_smoke_game(ROOT, spec) for _ in range(2))
        digest = stable_digest(first)
        if first.get("error") or replay.get("error") or digest != stable_digest(replay):
            raise ValueError(f"diagnostic replay mismatch: {spec.game_id}")
        events = first["events"]
        resolved = [
            {
                key: event[key]
                for key in (
                    "stack_object_id",
                    "searching_player",
                    "selected_id",
                    "hand_id",
                    "pre_shuffle_ids",
                    "post_shuffle_ids",
                    "shuffle_domain",
                )
            }
            for event in events
            if event["event"] == "library_search_to_hand_resolved"
        ]
        for item in resolved:
            selected = item["selected_id"]
            if selected is not None and not any(
                event["event"] == "zone_changed"
                and event.get("reason") == "library_search_to_hand"
                and event["source_object_id"] == selected
                and event["destination_object_id"] == item["hand_id"]
                for event in events
            ):
                raise ValueError(f"search hand movement missing: {spec.game_id}")
            if set(item["pre_shuffle_ids"]) != set(item["post_shuffle_ids"]):
                raise ValueError(f"search shuffle changed library membership: {spec.game_id}")
        payments = [
            {key: event[key] for key in ("card", "generic", "colored", "source_ids")}
            for event in events
            if event["event"] == "cost_paid" and event.get("card") == "Splinter's Technique"
        ]
        sneak = [
            {key: event[key] for key in ("card", "mana_source_ids", "returned_attacker_id")}
            for event in events
            if event["event"] == "sneak_cost_paid" and event.get("card") == "Splinter's Technique"
        ]
        if len(resolved) != len(payments) + len(sneak):
            raise ValueError(f"search payment mismatch: {spec.game_id}")
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
                "resolution": resolved,
                "runtime_error": None,
            }
        )
    if not any(game["resolution"] for game in games):
        raise ValueError("frozen search never executed")
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
