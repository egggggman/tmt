"""Reproduce bounded family triage without changing Issue 289 engine semantics."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import SmokeGameFailure, run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/cardcade"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
OLD = DOCS / "ISSUE_289_CLASS_ANTHEM_CHECKPOINT.json"
CURRENT = DOCS / "ISSUE_289_CLASS_ARTIFACT_ANIMATION_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_CLASS_ARTIFACT_ANIMATION_CALIBRATION_READINESS.json"
OUTPUT = DOCS / "ISSUE_289_FAMILY_TRIAGE.json"
EXPECTED = {
    MANIFEST: "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac",
    LEDGER: "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100",
    CURRENT: "01ccb63187e614cfeda064a8e1bd388f65df1210a745c9ee3345e76398ad815a",
}
RUNTIME = "a95807a7bf0a8a87b78155c425fe275da8b223190941e167d859ecf9f90902d9"

# Family membership is a planning taxonomy, not a new execution classification.
FAMILIES = {
    "artifact_token_engines": {
        "artifact_entry_leave_token_triggers",
        "artifact_spell_token_triggers",
        "artifact_token_cost_and_creation",
    },
    "combat_and_death_recursion": {
        "combat_damage_graveyard_recursion",
        "combat_damage_hidden_hand_entry",
        "temporary_death_recursion",
    },
    "class_counter_engines": {"class_levels_and_counters"},
    "combat_legality_and_team_effects": {
        "combat_block_constraints",
        "tribal_combat_modifier",
        "tribal_combat_keyword",
    },
    "activated_resource_conversion": {"activation_costs_and_resource_trade"},
    "artifact_counters_and_animation": {
        "artifact_entry_counters",
        "artifact_counters_and_animation",
    },
    "artifact_copy_effects": {"combat_damage_artifact_copy", "equipment_token_copy"},
    "artifact_scaling": {"artifact_scaling"},
    "damage_to_mana": {"damage_trigger_restricted_mana"},
    "temporary_combat_effects": {
        "targeted_entry_combat_modifier",
        "temporary_combat_modifier_and_scry",
    },
}
PAIRS = (
    ("shredder", "splinter"),
    ("leonardo", "raphael"),
    ("bebop_rocksteady", "michelangelo"),
    ("casey_jones", "donatello"),
    ("donatello", "krang"),
    ("bebop_rocksteady", "casey_jones"),
    ("leonardo", "april_oneil"),
    ("splinter", "bebop_rocksteady"),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(row: dict) -> tuple[str, str, str]:
    return row["deck"], row["card"], row["oracle_fragment"]


def main() -> None:
    for path, expected in EXPECTED.items():
        if sha(path) != expected:
            raise ValueError(f"frozen evidence changed: {path}")
    if identity()["aggregate_semantic_runtime_sha256"] != RUNTIME:
        raise ValueError("semantic runtime differs from validated #325")
    original = list(csv.DictReader(LEDGER.open(encoding="utf-8", newline="")))
    old = json.loads(OLD.read_text(encoding="utf-8"))
    current = json.loads(CURRENT.read_text(encoding="utf-8"))
    readiness = json.loads(READINESS.read_text(encoding="utf-8"))
    if Counter(map(key, original)) != Counter(map(key, current["rows"])):
        raise ValueError("original row identities changed")
    if len(original) != 172 or len(current["rows"]) != 172:
        raise ValueError("172-row ledger changed")
    if (
        old["counts"]["priority"].get("P1") != 47
        or current["counts"]["priority"].get("P1") != 35
        or readiness["important_blockers"] != 31
        or readiness["unbounded_residual_important"] != 4
        or readiness["checkpoint_overlay_sha256"] != sha(CURRENT)
        or readiness["semantic_runtime_sha256"] != RUNTIME
    ):
        raise ValueError("checkpoint or readiness lineage changed")
    old_gaps = Counter(key(r) for r in old["rows"] if r["impact_priority"] == "P1")
    open_keys = Counter(key(r) for r in current["rows"] if r["impact_priority"] == "P1")
    closed = sorted((old_gaps - open_keys).elements())
    if len(closed) != 12 or open_keys - old_gaps:
        raise ValueError("unexpected #322-to-#325 row delta")

    ranked = readiness["ranked_important_rows"]
    if len(ranked) != 35 or Counter(map(key, ranked)) != open_keys:
        raise ValueError("ranked rows do not match current overlay")
    tags = {item["mechanic"] for item in ranked}
    family_by_tag = {tag: family for family, members in FAMILIES.items() for tag in members}
    if tags != set(family_by_tag) or sum(map(len, FAMILIES.values())) != len(family_by_tag):
        raise ValueError("each open mechanic must be assigned to exactly one family")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    decks: dict[str, DeckSpec] = {}
    for deck in manifest["decks"]:
        source = (ROOT / deck["source_path"]).read_bytes()
        crlf = source.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        acceptable = {hashlib.sha256(source).hexdigest(), hashlib.sha256(crlf).hexdigest()}
        if deck["sha256"] not in acceptable:
            raise ValueError(f"frozen deck differs from manifest: {deck['deck_key']}")
        decks[deck["deck_key"]] = DeckSpec(deck["deck_key"], deck["source_path"])
    if len(decks) != 10:
        raise ValueError("expected ten frozen decks")

    catalog = json.loads((ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json").read_text())
    names_by_id = {item["oracle_id"]: item["name"] for item in catalog}
    cards_to_families: dict[str, set[str]] = defaultdict(set)
    fragments_to_families: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in ranked:
        family = family_by_tag[row["mechanic"]]
        cards_to_families[row["card"]].add(family)
        fragments_to_families[(row["card"], row["oracle_fragment"])].add(family)

    totals: dict[str, Counter] = defaultdict(Counter)
    card_totals: dict[str, Counter] = defaultdict(Counter)
    fragment_witnesses: Counter[tuple[str, str]] = Counter()
    games = []
    for index, (left, right) in enumerate(PAIRS):
        for seats in ((decks[left], decks[right]), (decks[right], decks[left])):
            spec = GameSpec(
                f"issue289-family-triage-{seats[0].display_id}-{seats[1].display_id}",
                "issue289-diagnostic-only",
                326 + index,
                f"{seats[0].display_id}-first",
                seats,
            )
            attempts = []
            for _ in range(2):
                try:
                    snapshot = run_smoke_game(ROOT, spec)
                    attempts.append(("success", snapshot, stable_digest(snapshot), None))
                except SmokeGameFailure as error:
                    attempts.append(
                        ("failure", error.snapshot, stable_digest(error.snapshot), str(error))
                    )
            if (attempts[0][0], attempts[0][2]) != (attempts[1][0], attempts[1][2]):
                raise ValueError(f"non-deterministic game or failure: {spec.game_id}")
            status, snapshot, digest, error_message = attempts[0]
            result = {
                "game_id": spec.game_id,
                "seed": spec.seed,
                "first_player": seats[0].display_id,
                "second_player": seats[1].display_id,
                "status": status,
                "replay_equal": True,
                "snapshot_digest": digest,
                "event_count": len(snapshot["events"]),
            }
            if status == "failure":
                result["error"] = error_message
                result["turn"] = snapshot["turn"]
                result["last_events"] = [
                    {
                        field: event[field]
                        for field in (
                            "event", "card", "source_zone", "destination_zone", "reason",
                            "oracle_fragment", "stack_object_id", "permanent_object_id",
                            "tapped", "attacking", "turn", "step",
                        )
                        if field in event
                    }
                    for event in snapshot["events"][-12:]
                ]
            games.append(result)

            for event in snapshot["events"]:
                for family in cards_to_families.get(event.get("card", ""), ()):
                    if event["event"] == "spell_cast":
                        totals[family]["spell_casts"] += 1
                        card_totals[event["card"]]["spell_casts"] += 1
                    if (
                        event["event"] == "zone_changed"
                        and event.get("destination_zone") == "battlefield"
                    ):
                        totals[family]["battlefield_entries"] += 1
                        card_totals[event["card"]]["battlefield_entries"] += 1
                if event["event"] == "combat_damage_player":
                    for family in cards_to_families.get(event.get("source", ""), ()):
                        totals[family]["source_player_damage_events"] += 1
                        card_totals[event["source"]]["source_player_damage_events"] += 1
            for occurrence in snapshot["conformance"]["semantic_occurrences"]:
                name = names_by_id.get(occurrence["oracle_id"], "")
                for family in fragments_to_families.get((name, occurrence["oracle_fragment"]), ()):
                    totals[family]["unsupported_fragment_presence"] += 1
                    card_totals[name]["unsupported_fragment_presence"] += 1
            for witness in snapshot["conformance"]["opportunity_witnesses"]:
                occurrence = next(
                    (item for item in snapshot["conformance"]["semantic_occurrences"]
                     if item["occurrence_id"] == witness["occurrence_id"]),
                    None,
                )
                if occurrence is None:
                    raise ValueError("witness without occurrence")
                name = names_by_id.get(occurrence["oracle_id"], "")
                for family in fragments_to_families.get((name, witness["oracle_fragment"]), ()):
                    totals[family]["recorded_opportunity_witnesses"] += 1
                    card_totals[name]["recorded_opportunity_witnesses"] += 1
                    fragment_witnesses[(name, witness["oracle_fragment"])] += 1

    groups = defaultdict(list)
    for row in ranked:
        groups[family_by_tag[row["mechanic"]]].append(row)
    families = []
    for family in FAMILIES:
        rows = groups[family]
        card_copies = {(row["deck"], row["card"]): row["copies_in_deck"] for row in rows}
        families.append(
            {
                "family": family,
                "row_count": len(rows),
                "frozen_distinct_card_copies": sum(card_copies.values()),
                "affected_decks": sorted({row["deck"] for row in rows}),
                "cards": sorted({row["card"] for row in rows}),
                "mechanic_tags": sorted({row["mechanic"] for row in rows}),
                "blocker_rows": sum(row["calibration_blocker"] for row in rows),
                "unbounded_rows": sum(not row["calibration_blocker"] for row in rows),
                "top_prior_row_score": max(row["priority_score"] for row in rows),
                "diagnostic": dict(sorted(totals[family].items())),
                "diagnostic_by_card": {
                    name: dict(sorted(card_totals[name].items()))
                    for name in sorted({row["card"] for row in rows})
                },
                "recorded_witnesses_by_fragment": [
                    {"card": name, "oracle_fragment": fragment, "count": count}
                    for (name, fragment), count in sorted(fragment_witnesses.items())
                    if name in {row["card"] for row in rows}
                ],
                "legal_action_availability": "unknown_for_unsupported_clauses",
                "pilot_selection": "unknown_for_unsupported_clauses",
                "effect_resolution": "unimplemented_or_incomplete; no success inferred",
                "rows": [
                    {
                        "deck": row["deck"],
                        "card": row["card"],
                        "oracle_fragment": row["oracle_fragment"],
                        "mechanic": row["mechanic"],
                        "copies_in_deck": row["copies_in_deck"],
                        "calibration_blocker": row["calibration_blocker"],
                    }
                    for row in rows
                ],
            }
        )
    if (
        sum(f["row_count"] for f in families) != 35
        or sum(f["blocker_rows"] for f in families) != 31
    ):
        raise ValueError("family classification lost an open row")

    report = {
        "schema": "issue289-family-triage-v1",
        "kind": "diagnostic_only_not_balance_evidence",
        "baseline_id": "OBL-BASELINE-005",
        "semantic_runtime_sha256": RUNTIME,
        "manifest_sha256": sha(MANIFEST),
        "original_ledger_sha256": sha(LEDGER),
        "start_checkpoint_sha256": sha(OLD),
        "current_checkpoint_sha256": sha(CURRENT),
        "current_readiness_sha256": sha(READINESS),
        "start_counts": {"important": 47, "blockers": 43, "unbounded": 4},
        "current_counts": {"critical": 0, "important": 35, "blockers": 31, "unbounded": 4},
        "closed_since_start": [
            dict(zip(("deck", "card", "oracle_fragment"), row, strict=True)) for row in closed
        ],
        "families": families,
        "diagnostic_game_count": len(games),
        "deterministic_replay_count": len(games),
        "diagnostic_games": games,
        "calibration_readiness": "BLOCKED",
    }
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "families": len(families),
        "games": len(games),
        "replays": len(games),
        "failures": sum(g["status"] == "failure" for g in games),
        "current": report["current_counts"],
        "diagnostic": {f["family"]: f["diagnostic"] for f in families},
    }, sort_keys=True))


if __name__ == "__main__":
    main()
