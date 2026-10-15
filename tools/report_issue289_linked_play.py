"""Preserve the 172-row ledger while auditing linked play and important risk."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import load_facts

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_TOP_CREATURE_SELECTION_CHECKPOINT.json"
OVERLAY = ROOT / "docs/cardcade/ISSUE_289_LINKED_PLAY_CHECKPOINT.json"
READINESS = ROOT / "docs/cardcade/ISSUE_289_LINKED_PLAY_CALIBRATION_READINESS.json"
LEDGER = ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
PREVIOUS_SHA = "358e2a47084f09121a62a63f44ce6256def99b52133645242d2c9d050a8e57c6"
LEDGER_SHA = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
MANIFEST_SHA = "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac"

GROUPS = {
    "Leader's Talent": "class_levels_and_counters",
    "Ninja Teen": "class_levels_and_graveyard_sneak",
    "Does Machines": "class_levels_and_artifact_animation",
    "Ravenous Robots": "artifact_spell_token_triggers",
    "Mouser Foundry": "artifact_entry_leave_token_triggers",
    "Foot Mystic": "disappear_token_triggers",
    "Rocksteady, Crash Courser": "combat_block_constraints",
    "Michelangelo, Mutant BFF": "combat_block_constraints",
    "Bebop, Warthog Warrior": "tribal_combat_keyword",
    "Splinter, Hamato Yoshi": "tribal_combat_modifier",
    "Donatello, Mutant Mechanic": "artifact_counters_and_animation",
    "Donatello, Gadget Master": "combat_damage_artifact_copy",
    "Donatello, Way with Machines": "artifact_entry_counters",
    "Ice Cream Kitty": "activation_costs_and_resource_trade",
    "Mutagen Man, Living Ooze": "artifact_token_cost_and_creation",
    "Krang, Master Mind": "artifact_scaling",
    "Raphael, Ninja Destroyer": "damage_trigger_restricted_mana",
    "Putrid Pals": "disappear_entry_counters",
    "Insectoid Exterminator": "disappear_resource_trigger",
    "Michelangelo, Game Master": "disappear_end_step_counters",
    "Guac & Marshmallow Pizza": "targeted_entry_combat_modifier",
    "Pain 101": "temporary_death_recursion",
    "Shark Shredder, Killer Clone": "combat_damage_graveyard_recursion",
    "Michelangelo, Improviser": "combat_damage_hidden_hand_entry",
    "Hamato Guardian Stance": "temporary_combat_modifier_and_scry",
    "Improvised Arsenal": "equipment_token_copy",
}
HIGH_IMPACT = {
    "Leader's Talent",
    "Ninja Teen",
    "Does Machines",
    "Ravenous Robots",
    "Mouser Foundry",
    "Foot Mystic",
    "Rocksteady, Crash Courser",
    "Splinter, Hamato Yoshi",
    "Donatello, Mutant Mechanic",
    "Donatello, Gadget Master",
    "Donatello, Way with Machines",
    "Ice Cream Kitty",
    "Mutagen Man, Living Ooze",
    "Krang, Master Mind",
    "Raphael, Ninja Destroyer",
    "Putrid Pals",
    "Shark Shredder, Killer Clone",
}
HIGH_COMPLEXITY = {
    "class_levels_and_graveyard_sneak",
    "class_levels_and_artifact_animation",
    "combat_damage_artifact_copy",
    "equipment_token_copy",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reports() -> tuple[dict, dict]:
    if (sha(PREVIOUS), sha(LEDGER), sha(MANIFEST)) != (
        PREVIOUS_SHA,
        LEDGER_SHA,
        MANIFEST_SHA,
    ):
        raise ValueError("frozen predecessor, ledger or manifest changed")
    before = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = next(item for item in manifest["decks"] if item["deck_key"] == "raphael")
    deck_path = ROOT / source["source_path"]
    if sha(deck_path) != source["sha256"]:
        raise ValueError("Raphael frozen deck differs from the Baseline 005 manifest")
    frozen = {}
    for line in deck_path.read_text(encoding="utf-8").splitlines():
        if not line or line == "Deck":
            continue
        count, name = line.split(" ", 1)
        frozen[name] = int(count)
    if sum(frozen.values()) != 60 or frozen.get("Raphael, Most Attitude") != 2:
        raise ValueError("unexpected frozen Raphael deck")
    facts = load_facts(load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")), set(frozen))
    interpreter = CardInterpreter()
    kinds = {name: interpreter.cast_program(facts[name]).kind.value for name in frozen}
    if any(
        interpreter.cast_program(facts[name]).kind is CastKind.UNSUPPORTED
        for name in frozen
        if not facts[name].is_land
    ):
        raise ValueError("frozen Raphael card with an unsupported cast family")
    rows = [dict(row) for row in before["rows"]]
    closed = []
    for row in rows:
        if row["card"] != "Raphael, Most Attitude" or row["impact_priority"] != "P0":
            continue
        if row["execution_review"] != "partial" or not (
            interpreter.linked_top_exile(facts[row["card"]], row["oracle_fragment"])
            or interpreter.linked_attack_play(facts[row["card"]], row["oracle_fragment"])
        ):
            raise ValueError("linked critical row is no longer the accepted partial fixture")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Complete generic source-object-linked exile and single-use attack grant: "
            "choice at play time, later-linked cards, controller-specific duration, source "
            "departure, normal land/spell timing, mana and alternative Sneak costs, "
            "targeted/modal priority dispatch, zone identities and deterministic replay; "
            "all frozen Raphael card casting families authenticated"
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if len(closed) != 2 or counts != {
        "execution": {"covered": 33, "supported": 76, "annotation": 7, "gap": 56},
        "priority": {"none": 116, "P1": 56},
    }:
        raise ValueError("unexpected linked row closure")
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    overlay = {
        "schema": "issue289-linked-play-checkpoint-v1",
        "baseline_id": before["baseline_id"],
        "base_ledger_sha256": LEDGER_SHA,
        "previous_checkpoint_sha256": PREVIOUS_SHA,
        "before_runtime_sha256": before["semantic_runtime_sha256"],
        "semantic_runtime_sha256": runtime,
        "baseline_manifest_sha256": MANIFEST_SHA,
        "frozen_raphael_deck_sha256": source["sha256"],
        "frozen_raphael_cast_kinds": kinds,
        "historical_runtime_sha256": before["historical_runtime_sha256"],
        "gate": "BLOCKED",
        "control_authorized": False,
        "before_counts": before["counts"],
        "counts": counts,
        "closed_rows": closed,
        "rows": rows,
    }

    important = [r for r in rows if r["impact_priority"] == "P1"]
    copies: dict[str, dict[str, int]] = defaultdict(dict)
    for row in important:
        copies[row["card"]][row["deck"]] = int(row["copies"])
    ranked = []
    for row in important:
        card = row["card"]
        group = GROUPS[card]
        total = sum(copies[card].values())
        decks = len(copies[card])
        impact = 4 if card in HIGH_IMPACT else 3
        reuse = 3 if group.startswith("class_levels") else (2 if decks > 1 else 1)
        complexity = 4 if group in HIGH_COMPLEXITY else (3 if reuse == 3 else 2)
        score = total * 3 + decks * 4 + impact * 5 + reuse * 2 - complexity
        blocker = impact == 4 or total >= 3
        ranked.append(
            {
                "deck": row["deck"],
                "card": card,
                "copies_in_deck": int(row["copies"]),
                "total_frozen_copies": total,
                "affected_decks": sorted(copies[card]),
                "oracle_fragment": row["oracle_fragment"],
                "mechanic": group,
                "execution_review": row["execution_review"],
                "impact_score": impact,
                "rules_reuse_score": reuse,
                "implementation_complexity_score": complexity,
                "priority_score": score,
                "calibration_blocker": blocker,
                "assessment": (
                    "Unexecuted clause changes material board, combat, resource or card-identity "
                    "outcomes in repeated frozen copies."
                    if blocker
                    else "Two-copy consequential clause; exposure remains unbounded and requires "
                    "diagnostic measurement before it can be accepted as residual risk."
                ),
            }
        )
    ranked.sort(
        key=lambda item: (
            -item["priority_score"],
            item["deck"],
            item["card"],
            item["oracle_fragment"],
        )
    )
    readiness = {
        "schema": "issue289-linked-play-calibration-readiness-v1",
        "baseline_id": before["baseline_id"],
        "checkpoint_overlay_sha256": None,
        "semantic_runtime_sha256": runtime,
        "original_ledger_sha256": LEDGER_SHA,
        "critical_remaining": 0,
        "important_remaining": len(ranked),
        "important_blockers": sum(item["calibration_blocker"] for item in ranked),
        "unbounded_residual_important": sum(not item["calibration_blocker"] for item in ranked),
        "calibration_readiness": "BLOCKED",
        "reason": (
            "High-copy executable gaps still distort core resource, board and combat outcomes "
            "across all ten frozen decks; the lower-exposure entries lack empirical bounds."
        ),
        "score_formula": "3*copies + 4*decks + 5*impact + 2*reuse - complexity",
        "score_scales": {
            "impact": (
                "4=core deck identity/resource/combat; 3=consequential conditional or utility"
            ),
            "reuse": "3=shared Class rules; 2=cross-deck; 1=single-deck",
            "complexity": "4=linked copy/animation/recursion; 3=Class; 2=bounded rule",
        },
        "ranked_important_rows": ranked,
    }
    return overlay, readiness


if __name__ == "__main__":
    overlay, readiness = reports()
    OVERLAY.write_text(json.dumps(overlay, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    readiness["checkpoint_overlay_sha256"] = sha(OVERLAY)
    READINESS.write_text(
        json.dumps(readiness, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "counts": overlay["counts"],
                "runtime": overlay["semantic_runtime_sha256"],
                "blockers": readiness["important_blockers"],
                "unbounded": readiness["unbounded_residual_important"],
            }
        )
    )
