"""Regenerate the preserved 172-row overlay for top-library creature selection."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import load_facts

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_CONDITIONAL_TOKENS_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_TOP_CREATURE_SELECTION_CHECKPOINT.json"
LEDGER_SHA = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA = "43b4f0ca8e66a898a99a3d2e74d55f119884964e130a4c850365e6d3e7a550c8"
PREVIOUS_RUNTIME = "5b3992c75837fbffee40d3eb641af9042b43505ec5e4eeab78c8334b7e9d8780"


def report() -> dict[str, object]:
    if hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() != PREVIOUS_SHA:
        raise ValueError("predecessor checkpoint changed")
    ledger = ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv"
    if hashlib.sha256(ledger.read_bytes()).hexdigest() != LEDGER_SHA:
        raise ValueError("original ledger changed")
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if (
        previous["semantic_runtime_sha256"] != PREVIOUS_RUNTIME
        or len(previous["rows"]) != 172
        or previous["counts"]["priority"] != {"none": 108, "P1": 61, "P0": 3}
    ):
        raise ValueError("unexpected predecessor coverage")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    card = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Michelangelo's Technique"},
    )["Michelangelo's Technique"]
    interpreter = CardInterpreter()
    program = interpreter.top_creature_selection_program(card)
    if (
        program is None
        or (program.count, program.maximum_creatures, program.maximum_total_mana_value)
        != (8, 2, 6)
        or interpreter.cast_program(card).kind is not CastKind.TOP_CREATURE_SELECTION
        or not interpreter.sneak_semantic_coverage(
            card, program.sneak_fragment
        ).coverage.fully_supported
        or interpreter.unsupported_fragments(card)
    ):
        raise ValueError("complete top-creature selection spell not executable")
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] != card.name or row["oracle_fragment"] != program.effect_fragment:
            continue
        if row["execution_review"] != "gap" or row["impact_priority"] != "P0":
            raise ValueError("unexpected top-creature row state")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Complete generic private top-library inspection and zero-to-two creature choice "
            "within combined mana value, simultaneous battlefield entry, randomized bottom "
            "order, normal/Sneak cost and priority, fresh zone identities, state-based actions, "
            "source provenance and deterministic replay"
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if len(closed) != 1 or counts != {
        "execution": {"covered": 33, "supported": 69, "annotation": 7, "gap": 61, "partial": 2},
        "priority": {"none": 109, "P1": 61, "P0": 2},
    }:
        raise ValueError("unexpected row closure")
    return {
        "schema": "issue289-top-creature-selection-checkpoint-v1",
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
        "selection_authority": {
            "previous_critical_assessment_sha256": PREVIOUS_SHA,
            "selected_rank_family": "top_creature_selection",
            "selected_card_copies": 2,
            "reason": (
                "Two frozen Michelangelo copies and one complete critical gap encode a bounded "
                "private eight-card selection with combined mana-value cap. Existing private "
                "inspection, deterministic bottom shuffle, fixed Sneak costs and batch entry "
                "make this smaller than Raphael's remaining linked-play casting families."
            ),
            "remaining_critical_rows": [
                {key: row[key] for key in ("deck", "card", "copies", "oracle_fragment")}
                for row in rows
                if row["impact_priority"] == "P0"
            ],
        },
        "closed_rows": closed,
        "rows": rows,
    }


if __name__ == "__main__":
    result = report()
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("counts", "semantic_runtime_sha256")}))
