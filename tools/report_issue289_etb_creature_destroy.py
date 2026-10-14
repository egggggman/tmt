"""Append the generic mandatory targeted entry-removal checkpoint to Issue 289."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_COMBAT_DRAW_LIFE_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_ETB_CREATURE_DESTROY_CHECKPOINT.json"
LEDGER_SHA = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA = "1ecb1a04a411d2f7e857278ac3b3161efb380c9f0171858b79f5364234574306"
PREVIOUS_RUNTIME = "d22d08a2d0181af12413cc816c64edbd096d112d55903711d50c13c1fef2f3e3"


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
        or previous["counts"]["priority"] != {"none": 94, "P0": 17, "P1": 61}
    ):
        raise ValueError("unexpected predecessor coverage")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    card = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Anchovy & Banana Pizza"},
    )["Anchovy & Banana Pizza"]
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] != card.name:
            continue
        fragment = row["oracle_fragment"]
        if not interpreter.etb_destroy_target_creature(card, fragment):
            continue
        if (
            row["execution_review"] != "gap"
            or row["impact_priority"] != "P0"
            or (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card)
        ):
            raise ValueError("entry destruction clause did not execute completely")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Generic mandatory targeted creature destruction on self-entry: legal target "
            "selected on the normal Priority stack, rechecked at resolution, source-independent "
            "trigger and authoritative destruction/zone/SBA handling"
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if len(closed) != 1 or counts["priority"] != {"none": 95, "P0": 16, "P1": 61}:
        raise ValueError("unexpected row closure")
    if counts["execution"] != {
        "covered": 33,
        "supported": 55,
        "annotation": 7,
        "gap": 74,
        "partial": 3,
    }:
        raise ValueError("unexpected execution totals")
    return {
        "schema": "issue289-etb-creature-destroy-checkpoint-v1",
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
            "selected_rank_family": 2,
            "selected_card_copies": 2,
            "reason": (
                "Targeted ETB removal has broad creature-combat impact and a complete "
                "generic event/target/priority/destroy path. Higher-copy modal, "
                "protection and type-layer spells need several coupled families."
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
