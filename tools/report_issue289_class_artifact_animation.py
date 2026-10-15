"""Append complete Class combat artifact-animation coverage and calibrate risk."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import load_facts

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_CLASS_GRAVEYARD_SNEAK_CHECKPOINT.json"
OVERLAY = ROOT / "docs/cardcade/ISSUE_289_CLASS_ARTIFACT_ANIMATION_CHECKPOINT.json"
READINESS = ROOT / "docs/cardcade/ISSUE_289_CLASS_ARTIFACT_ANIMATION_CALIBRATION_READINESS.json"
LEDGER = ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
PREVIOUS_SHA = "d0d5b21dba7bea6854520b67d5affbb365e009bb9f1aeed7be7bcfeb26e5a2a0"
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
    frozen = {}
    checked_deck_bytes = {}
    for deck in manifest["decks"]:
        path = ROOT / deck["source_path"]
        raw = path.read_bytes()
        canonical_crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        actual, line_ending_equivalent = (
            hashlib.sha256(raw).hexdigest(),
            hashlib.sha256(canonical_crlf).hexdigest(),
        )
        if deck["sha256"] not in {actual, line_ending_equivalent}:
            raise ValueError("frozen deck differs from the Baseline 005 manifest")
        checked_deck_bytes[deck["deck_key"]] = {
            "working_tree_sha256": actual,
            "manifest_sha256": deck["sha256"],
            "crlf_equivalent": actual != deck["sha256"],
        }
        frozen[deck["deck_key"]] = {
            name: int(count)
            for count, name in (
                line.split(" ", 1)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line and line != "Deck"
            )
        }
    facts = load_facts(
        load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")),
        {name for deck in frozen.values() for name in deck},
    )
    interpreter = CardInterpreter()
    rows = [dict(row) for row in before["rows"]]
    closed = []
    card = facts["Does Machines"]
    trigger = interpreter.fragments(card)[-1]
    if interpreter.class_combat_artifact_animation(card, trigger) is None:
        raise ValueError("Class combat artifact animation is incomplete")
    for row in rows:
        if row["card"] != "Does Machines" or row["oracle_fragment"] not in {
            "{4}{U}: Level 3",
            trigger,
        }:
            continue
        card, fragment = facts[row["card"]], row["oracle_fragment"]
        if (
            row["impact_priority"] != "P1"
            or row["execution_review"] != "gap"
            or frozen[row["deck"]][row["card"]] != int(row["copies"])
        ):
            raise ValueError("unexpected Class animation row or frozen copy count")
        if fragment == "{4}{U}: Level 3":
            complete = (
                interpreter.class_level_child(card, 3) == trigger
                and interpreter.activated_ability_semantics(card, fragment).coverage.fully_supported
            )
        else:
            complete = interpreter.class_combat_artifact_animation(card, fragment) is not None
        if not complete:
            raise ValueError("Class combat artifact animation is incomplete")
        if any(
            reason
            for candidate, reason in interpreter.unsupported_fragments(card)
            if candidate == fragment
        ):
            raise ValueError("Class clause still reports an unsupported fragment")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Generic level-three Class activation and beginning-of-combat targeted trigger. "
            "Three counters use the ordinary placement/SBA path; a noncreature artifact gains "
            "lasting Creature and Robot types plus base 0/0 in layer 7b. The effect retains "
            "other types/abilities, detaches Equipment, and survives Class departure. "
            "Timing, payment, target identity, cleanup and deterministic replay are tested."
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if len(closed) != 4 or counts != {
        "execution": {"covered": 33, "supported": 97, "annotation": 7, "gap": 35},
        "priority": {"none": 137, "P1": 35},
    }:
        raise ValueError("unexpected Class combat artifact animation row closure")
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    overlay = {
        "schema": "issue289-class-artifact-animation-checkpoint-v1",
        "baseline_id": before["baseline_id"],
        "base_ledger_sha256": LEDGER_SHA,
        "previous_checkpoint_sha256": PREVIOUS_SHA,
        "before_runtime_sha256": before["semantic_runtime_sha256"],
        "semantic_runtime_sha256": runtime,
        "baseline_manifest_sha256": MANIFEST_SHA,
        "frozen_deck_sha256": {deck["deck_key"]: deck["sha256"] for deck in manifest["decks"]},
        "frozen_deck_byte_verification": checked_deck_bytes,
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
        "schema": "issue289-class-artifact-animation-calibration-readiness-v1",
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
