"""Overlay verified counterspell/evasion closure without rewriting prior evidence."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_READINESS_CHECKPOINT.json"
ORIGINAL = ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_CRITICAL_SEMANTICS_CHECKPOINT.json"
PREVIOUS_SHA256 = "f4c8c8cf1cf9cb53d814d7c9cf2b9a039538fa2a3386b5f4862451b18c556be3"
ORIGINAL_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
EVASION = (
    "This creature can't be blocked if an artifact entered the battlefield "
    "under your control this turn."
)


def report() -> dict[str, object]:
    if hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() != PREVIOUS_SHA256:
        raise ValueError("PR #293 checkpoint changed")
    if hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() != ORIGINAL_SHA256:
        raise ValueError("preserved 172-row ledger changed")
    before = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if before["counts"]["priority"] != {"none": 46, "P0": 55, "P1": 71}:
        raise ValueError("PR #293 priority counts changed")
    rows = [dict(row) for row in before["rows"]]
    if len(rows) != 172:
        raise ValueError("checkpoint row count changed")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    cards = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {row["card"] for row in rows},
    )
    interpreter = CardInterpreter()
    closed = []
    for row in rows:
        card = cards[row["card"]]
        fragment = row["oracle_fragment"]
        counter = (
            row["card"] == "Negate"
            and interpreter.cast_program(card).kind is CastKind.COUNTER_TARGET_SPELL
            and interpreter.counter_spell_semantic_coverage(card, fragment).fully_supported
        )
        evasion = (
            fragment == EVASION
            and card.is_creature
            and interpreter.supports_blocking_fragment(fragment)
        )
        if not (counter or evasion):
            continue
        if row["execution_review"] != "gap" or row["impact_priority"] != "P0":
            raise ValueError("closure no longer applies to a critical gap")
        if (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card):
            raise ValueError("closed fragment still flagged unsupported")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Paid targeted Instant with Priority, Stack resolution and counter zone movement"
            if counter
            else "Artifact entry controller and turn provenance governs live block legality"
        )
        closed.append({"deck": row["deck"], "card": row["card"], "oracle_fragment": fragment})
    if Counter(item["card"] for item in closed) != {"Negate": 2, "Fugitive Droid": 3}:
        raise ValueError("unexpected closed fragment identity")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if counts["priority"] != {"none": 51, "P0": 50, "P1": 71}:
        raise ValueError("unexpected checkpoint priority counts")
    return {
        "schema": "issue289-critical-semantics-checkpoint-v1",
        "baseline_id": before["baseline_id"],
        "base_ledger_sha256": ORIGINAL_SHA256,
        "previous_checkpoint_sha256": PREVIOUS_SHA256,
        "before_runtime_sha256": before["semantic_runtime_sha256"],
        "semantic_runtime_sha256": identity()["aggregate_semantic_runtime_sha256"],
        "baseline_manifest_sha256": before["baseline_manifest_sha256"],
        "catalog_sha256": before["catalog_sha256"],
        "historical_runtime_sha256": before["historical_runtime_sha256"],
        "gate": "BLOCKED",
        "control_authorized": False,
        "before_counts": before["counts"],
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
