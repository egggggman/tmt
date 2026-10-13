"""Reproduce the 172-row coverage overlay after generic targeted removal."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_CRITICAL_IDENTITY_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_TARGETED_REMOVAL_CHECKPOINT.json"
ORIGINAL_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA256 = "540dc5b282750e5d6510b000f6b4ccfc4f6314380d8fa6d7a56c2b1c51e9f29e"
PREVIOUS_RUNTIME = "75a725ffdc6460a8d1190c5738837dddf0ed1a85d628eefaca4ed35adf8f1ccd"
TARGETS = {"Death in the Family", "Shredder's Technique"}


def report() -> dict[str, object]:
    if hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() != PREVIOUS_SHA256:
        raise ValueError("previous checkpoint bytes changed")
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if (
        previous["base_ledger_sha256"] != ORIGINAL_SHA256
        or previous["semantic_runtime_sha256"] != PREVIOUS_RUNTIME
        or len(previous["rows"]) != 172
        or hashlib.sha256(
            (ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv").read_bytes()
        ).hexdigest()
        != ORIGINAL_SHA256
    ):
        raise ValueError("historical coverage identity changed")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    facts = load_facts(load_card_data(catalog, catalog.with_suffix(".manifest.json")), TARGETS)
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] not in TARGETS:
            continue
        card = facts[row["card"]]
        fragment = row["oracle_fragment"]
        removal = interpreter.targeted_removal_program(card)
        sneak = interpreter.sneak_semantic_coverage(card, fragment)
        supported = removal is not None and (
            interpreter.TARGETED_REMOVAL.fullmatch(fragment)
            or (sneak is not None and sneak.coverage.fully_supported)
        )
        if not supported:
            continue
        if row["execution_review"] != "gap" or row["impact_priority"] not in {"P0", "P1"}:
            raise ValueError("unexpected predecessor row for removal")
        if (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card):
            raise ValueError("claimed clause still unsupported")
        closed.append(
            {
                "deck": row["deck"],
                "card": row["card"],
                "oracle_fragment": fragment,
                "before": row["execution_review"],
                "before_priority": row["impact_priority"],
            }
        )
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Oracle-derived target predicate, normal or Sneak cost, current-characteristic "
            "resolution, destination zone, and conditional life loss execute deterministically"
        )
    if Counter((row["card"], row["before_priority"]) for row in closed) != {
        ("Death in the Family", "P0"): 1,
        ("Shredder's Technique", "P0"): 1,
        ("Shredder's Technique", "P1"): 1,
    }:
        raise ValueError("unexpected coverage closure membership")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if counts["priority"] != {"none": 83, "P0": 25, "P1": 64}:
        raise ValueError("unexpected remaining impact counts")
    return {
        "schema": "issue289-targeted-removal-checkpoint-v1",
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


def main() -> None:
    result = report()
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("gate", "counts", "semantic_runtime_sha256")}))


if __name__ == "__main__":
    main()
