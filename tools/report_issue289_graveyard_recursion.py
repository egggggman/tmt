"""Regenerate the preserved 172-row overlay for bounded graveyard recursion."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_HAND_RESET_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_GRAVEYARD_RECURSION_CHECKPOINT.json"
LEDGER_SHA = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA = "70bc2c96ba1f731ef321c173d1a41cd596ee5c330c5afd7e23b17cc9e2dad5ed"
PREVIOUS_RUNTIME = "39f7b510513784981863367bb5a0be0aacb62849b1fd483357e92e08e82b7c8a"


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
        or previous["counts"]["priority"] != {"none": 105, "P1": 61, "P0": 6}
    ):
        raise ValueError("unexpected predecessor coverage")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    card = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Leonardo's Technique"},
    )["Leonardo's Technique"]
    interpreter = CardInterpreter()
    program = interpreter.graveyard_recursion_program(card)
    if (
        program is None
        or program.sneak_fragment is None
        or program.mana_value_limit != 3
        or interpreter.cast_program(card).kind is not CastKind.GRAVEYARD_RECURSION
        or not interpreter.sneak_semantic_coverage(
            card, program.sneak_fragment
        ).coverage.fully_supported
        or interpreter.unsupported_fragments(card)
    ):
        raise ValueError("complete recursion and alternative cost not executable")
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] != card.name or row["oracle_fragment"] != program.effect_fragment:
            continue
        if row["execution_review"] != "gap" or row["impact_priority"] != "P0":
            raise ValueError("unexpected recursion row state")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Complete generic one-or-two graveyard creature-card targets within printed mana "
            "value limit: normal or fixed Sneak casting, distinct target identity and payment, "
            "resolution-time legal subset, simultaneous battlefield entry, event provenance, "
            "state-based actions, priority and deterministic replay"
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if len(closed) != 1 or counts != {
        "execution": {"covered": 33, "supported": 66, "annotation": 7, "gap": 64, "partial": 2},
        "priority": {"none": 106, "P1": 61, "P0": 5},
    }:
        raise ValueError("unexpected row closure")
    return {
        "schema": "issue289-graveyard-recursion-checkpoint-v1",
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
            "selected_rank_family": "bounded_multitarget_graveyard_recursion",
            "selected_card_copies": 2,
            "reason": (
                "Two frozen Leonardo copies restore one or two small creature cards, a high-impact "
                "board recovery action. Existing graveyard identity, normal entry triggers, "
                "target validation, stack and fixed Sneak primitives permit a bounded complete "
                "family smaller than Raphael linked permissions, top-eight coupled selection or "
                "conditional tapped-and-attacking token entry."
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
