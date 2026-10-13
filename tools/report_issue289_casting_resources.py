"""Reproduce the full Issue 289 overlay after generic spell-cost discounts."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_TARGETED_REMOVAL_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_CASTING_RESOURCES_CHECKPOINT.json"
ORIGINAL_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA256 = "bd2962a375bdb95144533dac7a92f8ae776eeb87515de71f75bfe7909e70e383"
PREVIOUS_RUNTIME = "92528faf3854869ea0905e36102c2aa22b8b36d8a880ccaeebf7ab8668b33cb5"
TARGETS = {"Saved by the Shell", "Krang, Master Mind", "Purple Dragon Punks"}


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
    closed, partial = [], []
    for row in rows:
        name, fragment = row["card"], row["oracle_fragment"]
        if name not in TARGETS:
            continue
        program = interpreter.generic_cost_reduction_program(facts[name], fragment)
        if program is None:
            continue
        if row["execution_review"] != "gap" or row["impact_priority"] != "P0":
            raise ValueError("unexpected predecessor for resource row")
        if (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(facts[name]):
            raise ValueError("claimed discount still unsupported")
        if name == "Krang, Master Mind":
            row["execution_review"] = "supported"
            row["impact_priority"] = "none"
            row["disposition"] = (
                "Affinity reduces generic cost from current controlled artifacts; legal action, "
                "payment commitment, and permanent resolution execute"
            )
            closed.append({"deck": row["deck"], "card": name, "oracle_fragment": fragment})
        elif name == "Saved by the Shell":
            if interpreter.cast_program(facts[name]).kind.value != "unsupported":
                raise ValueError("Saved payload unexpectedly executable")
            row["execution_review"] = "partial"
            row["disposition"] = (
                "Conditional Turtle discount computes and revalidates; spell counter, "
                "temporary keywords, and complete casting remain unsupported"
            )
            partial.append({"deck": row["deck"], "card": name, "oracle_fragment": fragment})
        else:
            raise ValueError("restricted mana unexpectedly classified as cost reduction")
    if [row["card"] for row in closed] != ["Krang, Master Mind"] or [
        row["card"] for row in partial
    ] != ["Saved by the Shell"]:
        raise ValueError("unexpected closure membership")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if counts["priority"] != {"none": 84, "P0": 24, "P1": 64} or counts["execution"] != {
        "covered": 33,
        "gap": 85,
        "annotation": 7,
        "partial": 3,
        "supported": 44,
    }:
        raise ValueError("unexpected remaining coverage counts")
    return {
        "schema": "issue289-casting-resources-checkpoint-v1",
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
        "assessed_partial_rows": partial,
        "rows": rows,
    }


def main() -> None:
    result = report()
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("gate", "counts", "semantic_runtime_sha256")}))


if __name__ == "__main__":
    main()
