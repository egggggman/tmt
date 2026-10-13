"""Append generic granted combat and subtype entry Equipment coverage to Issue 289."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_ARMOR_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_KATANA_CHECKPOINT.json"
ORIGINAL_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA256 = "5c73b50eeaf81ccdd0d0c95e4818fdca73a08aa6b9f5e9900ecea5916ff2595c"
PREVIOUS_RUNTIME = "ceb2b145af1728abad173ab378627b23e58f28f76659e70bdeae27e6a0fdb0a6"


def report() -> dict[str, object]:
    if hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() != PREVIOUS_SHA256:
        raise ValueError("previous checkpoint changed")
    original_sha = hashlib.sha256(
        (ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv").read_bytes()
    ).hexdigest()
    if original_sha != ORIGINAL_SHA256:
        raise ValueError("original ledger changed")
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if (
        previous["semantic_runtime_sha256"] != PREVIOUS_RUNTIME
        or previous["base_ledger_sha256"] != ORIGINAL_SHA256
        or len(previous["rows"]) != 172
        or previous["counts"]["priority"] != {"none": 91, "P0": 19, "P1": 62}
    ):
        raise ValueError("unexpected predecessor coverage")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    card = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Quintessential Katana"},
    )["Quintessential Katana"]
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] != card.name:
            continue
        fragment = row["oracle_fragment"]
        combat = interpreter.equipment_granted_combat_semantics(card, fragment)
        subtype = interpreter.equipment_subtype_entry_attach(card, fragment)
        if combat is None and subtype is None:
            continue
        if (
            row["execution_review"] != "gap"
            or row["impact_priority"] not in {"P0", "P1"}
            or (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card)
        ):
            raise ValueError("Katana clause did not execute completely")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Generic Equipment-granted combat-damage trigger against creature or player; "
            "recipient untaps if present and its controller at damage time gains life "
            "after Priority resolution"
            if combat is not None
            else "Generic optional subtype-entry triggered attachment; the entrant is an "
            "untargeted recipient and attachment follows legal zone identity"
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if len(closed) != 2 or counts["priority"] != {"none": 93, "P0": 18, "P1": 61}:
        raise ValueError("unexpected row closure")
    if counts["execution"] != {
        "covered": 33,
        "gap": 76,
        "annotation": 7,
        "partial": 3,
        "supported": 53,
    }:
        raise ValueError("unexpected execution totals")
    return {
        "schema": "issue289-katana-checkpoint-v1",
        "baseline_id": previous["baseline_id"],
        "base_ledger_sha256": ORIGINAL_SHA256,
        "previous_checkpoint_sha256": PREVIOUS_SHA256,
        "before_runtime_sha256": PREVIOUS_RUNTIME,
        "semantic_runtime_sha256": identity()["aggregate_semantic_runtime_sha256"],
        "baseline_manifest_sha256": previous["baseline_manifest_sha256"],
        "catalog_sha256": previous["catalog_sha256"],
        "historical_runtime_sha256": previous["historical_runtime_sha256"],
        "gate": "BLOCKED",
        "control_authorized": False,
        "before_counts": previous["counts"],
        "counts": counts,
        "closed_rows": closed,
        "rows": rows,
    }


if __name__ == "__main__":
    result = report()
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("gate", "counts", "semantic_runtime_sha256")}))
