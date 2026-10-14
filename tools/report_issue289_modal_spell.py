"""Append complete two-mode instant coverage without changing the original ledger."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_ETB_CREATURE_DESTROY_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_MODAL_SPELL_CHECKPOINT.json"
LEDGER_SHA = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA = "b3d8e15c4609f3bb94801f723c1dc6c3cd4b159dc9566fddb9098a6df0fca0fe"
PREVIOUS_RUNTIME = "fb7dab9e04fe1b138c5bb1560cc7d0026d289d8cbe5ca7a7890e12ad69346476"


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
        or previous["counts"]["priority"] != {"none": 95, "P0": 16, "P1": 61}
    ):
        raise ValueError("unexpected predecessor coverage")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    card = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Mouser Attack!"},
    )["Mouser Attack!"]
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] != card.name:
            continue
        fragment = row["oracle_fragment"]
        modal = interpreter.modal_token_or_creature_pump_program(card)
        if modal is None or fragment not in {modal.token_fragment, modal.pump_fragment}:
            continue
        token_coverage = interpreter.token_semantic_coverage(card, modal.token_fragment)
        strike_coverage = interpreter.strike_semantic_coverage(card, modal.pump_fragment)
        if (
            token_coverage is None
            or not token_coverage.fully_supported
            or strike_coverage is None
            or not strike_coverage.coverage.fully_supported
        ):
            raise ValueError("modal spell lacks full child-clause coverage")
        if (
            row["execution_review"] != "gap"
            or row["impact_priority"] != "P0"
            or (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card)
        ):
            raise ValueError("modal spell clause did not execute completely")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Complete generic two-mode instant: casting-time mode selection locked on the "
            "Stack, mode-specific legal target and payment checks, token entry or temporary "
            "creature P/T and first-strike effects, resolution legality, provenance and cleanup"
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if len(closed) != 2 or counts["priority"] != {"none": 97, "P0": 14, "P1": 61}:
        raise ValueError("unexpected row closure")
    if counts["execution"] != {
        "covered": 33,
        "supported": 57,
        "annotation": 7,
        "gap": 72,
        "partial": 3,
    }:
        raise ValueError("unexpected execution totals")
    return {
        "schema": "issue289-modal-spell-checkpoint-v1",
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
            "selected_rank_family": 1,
            "selected_card_copies": 3,
            "reason": (
                "Three Raphael copies; two critical clauses affecting board development "
                "and combat. Existing token, P/T, and strike rules permit the smallest "
                "complete two-mode cast path. Saved by the Shell (three copies, three "
                "critical rows) additionally needs counter and three protection keywords; "
                "Mind Transfer Protocol (three copies, two critical rows) needs temporary "
                "type and base P/T layers plus draw coupling."
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
    print(json.dumps({key: result[key] for key in ("gate", "counts", "semantic_runtime_sha256")}))
