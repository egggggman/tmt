"""Overlay validated shared interaction closure on the immutable Issue 289 ledger."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_LAND_SEMANTICS_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_SHARED_INTERACTION_CHECKPOINT.json"
ORIGINAL_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA256 = "69d299f87678e59434e0b015c176cafcc245ddd3d476642d576f4e13e30c4bcf"


def report() -> dict[str, object]:
    previous_digest = hashlib.sha256(PREVIOUS.read_bytes()).hexdigest()
    if previous_digest != PREVIOUS_SHA256:
        raise ValueError("land checkpoint changed")
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if previous["base_ledger_sha256"] != ORIGINAL_SHA256 or len(previous["rows"]) != 172:
        raise ValueError("original ledger identity changed")
    if previous["semantic_runtime_sha256"] != (
        "26a20e23ec621f492a7e4cf980ec431b0349bd520816baafbd9e9b72150a4c11"
    ):
        raise ValueError("previous runtime identity changed")
    if (
        hashlib.sha256(
            (ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv").read_bytes()
        ).hexdigest()
        != ORIGINAL_SHA256
    ):
        raise ValueError("original 172-row ledger changed")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    facts = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Stomped by the Foot", "Cowabunga!"},
    )
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] not in facts:
            continue
        card = facts[row["card"]]
        fragment = row["oracle_fragment"]
        coverage = interpreter.shared_interaction_semantic_coverage(card, fragment)
        if coverage is None or not coverage.fully_supported:
            raise ValueError("shared interaction clause is not executable")
        if (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card):
            raise ValueError("shared interaction clause remains unsupported")
        if row["execution_review"] != "gap":
            raise ValueError("unexpected preceding disposition")
        closed.append(
            {
                "deck": row["deck"],
                "card": row["card"],
                "oracle_fragment": fragment,
                "before": row["impact_priority"],
            }
        )
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Optional sacrifice paid on announcement, target checked at resolution, "
            "temporary modifier applies before combat damage"
            if card.name == "Stomped by the Foot"
            else "Private eligible top-card choice, reveal to hand, deterministic random bottom"
        )
    if len(closed) != 8 or Counter(item["before"] for item in closed) != {"P0": 5, "P1": 3}:
        raise ValueError("unexpected shared interaction closure count")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if counts["priority"] != {"none": 63, "P0": 41, "P1": 68}:
        raise ValueError("unexpected new priority count")
    return {
        "schema": "issue289-shared-interaction-checkpoint-v1",
        "baseline_id": previous["baseline_id"],
        "base_ledger_sha256": ORIGINAL_SHA256,
        "previous_checkpoint_sha256": previous_digest,
        "before_runtime_sha256": previous["semantic_runtime_sha256"],
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


def main() -> None:
    result = report()
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("gate", "counts", "semantic_runtime_sha256")}))


if __name__ == "__main__":
    main()
