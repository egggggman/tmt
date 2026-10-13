"""Overlay the immutable Issue 289 ledger after Alliance and scaled Equipment fixes."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_CREATURE_POWER_DAMAGE_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_ALLIANCE_EQUIPMENT_CHECKPOINT.json"
ORIGINAL_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA256 = "439cecc09756c6ccfc1ba9f561b3a2d97b7743de145caa2d49ecd962c0332285"
PREVIOUS_RUNTIME = "61fcd7d0c5aeb1972fc5e531bc6b7d8168ec7b616feb1d39322d9e56819db4ed"


def report() -> dict[str, object]:
    if hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() != PREVIOUS_SHA256:
        raise ValueError("previous checkpoint changed")
    if (
        hashlib.sha256(
            (ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv").read_bytes()
        ).hexdigest()
        != ORIGINAL_SHA256
    ):
        raise ValueError("original ledger changed")
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if (
        previous["semantic_runtime_sha256"] != PREVIOUS_RUNTIME
        or previous["base_ledger_sha256"] != ORIGINAL_SHA256
        or len(previous["rows"]) != 172
    ):
        raise ValueError("unexpected predecessor identity")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    card = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Improvised Arsenal"},
    )["Improvised Arsenal"]
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] != card.name:
            continue
        fragment = row["oracle_fragment"]
        scaled = interpreter.equipment_scaled_static_semantics(card, fragment)
        equip = interpreter.activated_ability_semantics(card, fragment)
        if scaled is None and (
            equip is None or not equip.coverage.fully_supported or not fragment.startswith("Equip ")
        ):
            continue
        if (
            row["execution_review"] != "gap"
            or row["impact_priority"] not in {"P0", "P1"}
            or (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card)
        ):
            raise ValueError("Equipment closure has not executed honestly")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Generic legal sorcery-speed Equip payment/target/stack and attached creature "
            "power recalculated per controlled artifact in the P/T modification layer"
        )
        closed.append({"deck": row["deck"], "card": row["card"], "oracle_fragment": fragment})
    if len(closed) != 2:
        raise ValueError("unexpected closure membership")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if counts["priority"] != {"none": 89, "P0": 20, "P1": 63} or counts["execution"] != {
        "covered": 33,
        "gap": 80,
        "annotation": 7,
        "partial": 3,
        "supported": 49,
    }:
        raise ValueError("unexpected overlay totals")
    return {
        "schema": "issue289-alliance-equipment-checkpoint-v1",
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
