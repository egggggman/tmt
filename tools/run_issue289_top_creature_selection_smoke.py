"""Authenticated four-game frozen-deck diagnostics with exact deterministic replays."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.engine07 import load_facts
from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_TOP_CREATURE_SELECTION_SMOKE.json"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
MANIFEST_SHA = "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac"
CARD = "Michelangelo's Technique"


def frozen_decks() -> dict[str, DeckSpec]:
    if hashlib.sha256(MANIFEST.read_bytes()).hexdigest() != MANIFEST_SHA:
        raise ValueError("Baseline 005 manifest changed")
    decks = {}
    for entry in json.loads(MANIFEST.read_text(encoding="utf-8"))["decks"]:
        if entry["deck_key"] not in {"michelangelo", "leonardo", "donatello"}:
            continue
        source = (ROOT / entry["source_path"]).read_bytes()
        raw = hashlib.sha256(source).hexdigest() == entry["sha256"]
        crlf = (
            hashlib.sha256(source.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()
            == entry["sha256"]
        )
        if not (raw or crlf):
            raise ValueError("frozen deck changed")
        decks[entry["deck_key"]] = DeckSpec(entry["deck_key"], entry["source_path"])
    if set(decks) != {"michelangelo", "leonardo", "donatello"}:
        raise ValueError("frozen diagnostic deck missing")
    return decks


def main() -> None:
    decks = frozen_decks()
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    card_data = load_card_data(catalog, catalog.with_suffix(".manifest.json"))
    facts = load_facts(card_data, {card.name for card in card_data.cards})
    specs = [
        GameSpec(
            f"issue289-top-creature-selection-317-{seats[0].display_id}-{seats[1].display_id}",
            "issue289-diagnostic",
            317,
            f"{seats[0].display_id}-first",
            seats,
        )
        for opponent in (decks["leonardo"], decks["donatello"])
        for seats in ((decks["michelangelo"], opponent), (opponent, decks["michelangelo"]))
    ]
    games = []
    for spec in specs:
        first, replay = (run_smoke_game(ROOT, spec) for _ in range(2))
        digest = stable_digest(first)
        if first.get("error") or replay.get("error") or digest != stable_digest(replay):
            raise ValueError(f"frozen diagnostic replay mismatch: {spec.game_id}")
        events = first["events"]
        resolutions = [
            {
                key: event[key]
                for key in (
                    "stack_object_id",
                    "inspected_ids",
                    "selected",
                    "bottom_ids",
                    "maximum_creatures",
                    "maximum_total_mana_value",
                    "oracle_fragment",
                )
            }
            for event in events
            if event["event"] == "top_creature_selection_resolved"
        ]
        for item in resolutions:
            inspected = set(item["inspected_ids"])
            selected = {entry["library_id"] for entry in item["selected"]}
            if (
                len(item["inspected_ids"]) > 8
                or len(selected) > 2
                or selected | set(item["bottom_ids"]) != inspected
                or selected & set(item["bottom_ids"])
            ):
                raise ValueError("top-creature selected/remainder partition is malformed")
            values = []
            for entry in item["selected"]:
                matching = [
                    event
                    for event in events
                    if event["event"] == "zone_changed"
                    and event.get("reason") == "top_creature_selection_entry"
                    and event["source_object_id"] == entry["library_id"]
                    and event["destination_object_id"] == entry["battlefield_id"]
                ]
                if len(matching) != 1 or not facts[matching[0]["card"]].is_creature:
                    raise ValueError("top-creature zone identity or creature type invalid")
                values.append(facts[matching[0]["card"]].mana_value)
            if sum(values) > item["maximum_total_mana_value"]:
                raise ValueError("top-creature combined mana value exceeded")
        ordinary = [
            event for event in events if event["event"] == "cost_paid" and event.get("card") == CARD
        ]
        sneak = [
            event
            for event in events
            if event["event"] == "sneak_cost_paid" and event.get("card") == CARD
        ]
        if len(resolutions) != len(ordinary) + len(sneak):
            raise ValueError("top-creature resolution/payment provenance mismatch")
        games.append(
            {
                "game_id": spec.game_id,
                "seed": spec.seed,
                "first_player": spec.seats[0].display_id,
                "replay_equal": True,
                "result_digest": digest,
                "event_count": len(events),
                "normal_payments": len(ordinary),
                "sneak_payments": len(sneak),
                "resolutions": resolutions,
                "runtime_error": None,
            }
        )
    if not any(game["resolutions"] for game in games):
        raise ValueError("frozen selection spell never executed")
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
                "normal_payments": sum(g["normal_payments"] for g in games),
                "sneak_payments": sum(g["sneak_payments"] for g in games),
                "resolutions": sum(len(g["resolutions"]) for g in games),
            }
        )
    )


if __name__ == "__main__":
    main()
