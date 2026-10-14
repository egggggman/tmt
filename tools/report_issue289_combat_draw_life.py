"""Preserve the full Issue 289 ledger with one closed combat-damage clause."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import load_facts

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_KATANA_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_COMBAT_DRAW_LIFE_CHECKPOINT.json"
LEDGER_SHA = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA = "65f43641ad41a3d434203b88b4fc6cbb4d864aeac786a95a7cf5224ee4660ed5"
PREVIOUS_RUNTIME = "289ce95d8282e2ee33b1ffb468c117a7620dea7127609dcfe9ebc993cb5ea8a3"

# Ranking is a readiness assessment, not an engine dispatch table. Multiple rows
# of one printed card share its actual frozen copy count, never add their copies.
ASSESSMENT = {
    "Oroku Saki, Shredder Rising": (1, "combat card advantage/life", 3, 3, 1),
    "Anchovy & Banana Pizza": (2, "targeted ETB removal", 3, 3, 2),
    "Mouser Attack!": (3, "modal token or combat trick", 3, 3, 4),
    "Saved by the Shell": (4, "conditional cost/protection", 3, 3, 4),
    "Mind Transfer Protocol": (5, "type/base P/T transformation plus draw", 3, 2, 4),
    "Raphael, Most Attitude": (6, "linked exile/play permission", 3, 3, 5),
    "Return to the Sewers": (7, "owner library choice and token", 3, 2, 3),
    "Leonardo's Technique": (8, "multi-target recursion", 3, 2, 4),
    "Raphael's Technique": (9, "each-player optional discard/draw", 2, 2, 3),
    "Splinter's Technique": (10, "unrestricted library tutor", 3, 3, 3),
    "Michelangelo's Technique": (11, "top-eight constrained selection", 3, 2, 5),
    "The Last Ronin's Technique": (12, "sneak-dependent attacking tokens", 2, 2, 4),
}


def report() -> dict[str, object]:
    if hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() != PREVIOUS_SHA:
        raise ValueError("previous checkpoint changed")
    if (
        hashlib.sha256(
            (ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv").read_bytes()
        ).hexdigest()
        != LEDGER_SHA
    ):
        raise ValueError("original ledger changed")
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if (
        previous["semantic_runtime_sha256"] != PREVIOUS_RUNTIME
        or len(previous["rows"]) != 172
        or previous["counts"]["priority"] != {"none": 93, "P0": 18, "P1": 61}
    ):
        raise ValueError("unexpected predecessor")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    card = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Oroku Saki, Shredder Rising"},
    )["Oroku Saki, Shredder Rising"]
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    assessed = []
    closed = []
    for index, row in enumerate(rows):
        if row["impact_priority"] != "P0":
            continue
        rank, family, severity, reuse, complexity = ASSESSMENT[row["card"]]
        assessed.append(
            {
                "row_index": index,
                "rank_family": rank,
                "deck": row["deck"],
                "card": row["card"],
                "frozen_copies": int(row["copies"]),
                "oracle_fragment": row["oracle_fragment"],
                "family": family,
                "gameplay_severity_1_to_3": severity,
                "generic_reuse_1_to_3": reuse,
                "implementation_complexity_1_to_5": complexity,
                "before_execution_review": row["execution_review"],
            }
        )
        if row["card"] != card.name:
            continue
        fragment = row["oracle_fragment"]
        if (
            row["execution_review"] != "gap"
            or interpreter.combat_damage_draw_lose_life(card, fragment) != (1, 1)
            or (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card)
        ):
            raise ValueError("combat draw/life clause did not execute completely")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Generic authenticated self combat-damage-to-player trigger; draw then lose life "
            "on the Priority stack, retaining source/event identity after source departure"
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    if len(assessed) != 18 or len(closed) != 1:
        raise ValueError("not all critical rows assessed or unexpected closure")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if counts["priority"] != {"none": 94, "P0": 17, "P1": 61}:
        raise ValueError("unexpected priority totals")
    if counts["execution"] != {
        "covered": 33,
        "supported": 54,
        "annotation": 7,
        "gap": 75,
        "partial": 3,
    }:
        raise ValueError("unexpected execution totals")
    equipment_copy = [
        row
        for row in rows
        if row["card"] == "Improvised Arsenal"
        and "copy of this Equipment" in row["oracle_fragment"]
    ]
    if len(equipment_copy) != 2 or any(row["impact_priority"] != "P1" for row in equipment_copy):
        raise ValueError("Equipment copy assessment changed")
    return {
        "schema": "issue289-combat-draw-life-checkpoint-v1",
        "baseline_id": previous["baseline_id"],
        "base_ledger_sha256": LEDGER_SHA,
        "previous_checkpoint_sha256": PREVIOUS_SHA,
        "before_runtime_sha256": PREVIOUS_RUNTIME,
        "semantic_runtime_sha256": identity()["aggregate_semantic_runtime_sha256"],
        "baseline_manifest_sha256": previous["baseline_manifest_sha256"],
        "catalog_sha256": previous["catalog_sha256"],
        "historical_runtime_sha256": previous["historical_runtime_sha256"],
        "gate": "BLOCKED",
        "control_authorized": False,
        "before_counts": previous["counts"],
        "counts": counts,
        "critical_assessment": sorted(
            assessed, key=lambda item: (item["rank_family"], item["row_index"])
        ),
        "important_equipment_copy_assessment": {
            "card": "Improvised Arsenal",
            "frozen_copies": 3,
            "rows": len(equipment_copy),
            "priority": "P1",
            "finding": (
                "Token copying needs copyable values, independent object identity, and "
                "attachment state; retained as a separate complete family."
            ),
        },
        "closed_rows": closed,
        "rows": rows,
    }


if __name__ == "__main__":
    result = report()
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("gate", "counts", "semantic_runtime_sha256")}))
