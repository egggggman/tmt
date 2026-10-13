"""Overlay the immutable Issue 289 ledger after two-target creature-power damage."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_ACTIVATED_DAMAGE_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_CREATURE_POWER_DAMAGE_CHECKPOINT.json"
ORIGINAL_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA256 = "27c66e3db22fb8b4968165e59626b088fdab036980c1511e1401737be4d4e13b"
PREVIOUS_RUNTIME = "7ca337922f33feeaf8371f15eb5813ade5bcbaa21a0f0fbbae6166c8a49daa9d"


def report() -> dict[str, object]:
    if hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() != PREVIOUS_SHA256:
        raise ValueError("previous checkpoint changed")
    if (
        hashlib.sha256(
            (ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv").read_bytes()
        ).hexdigest()
        != ORIGINAL_SHA256
    ):
        raise ValueError("original 172-row ledger changed")
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if (
        previous["semantic_runtime_sha256"] != PREVIOUS_RUNTIME
        or previous["base_ledger_sha256"] != ORIGINAL_SHA256
        or len(previous["rows"]) != 172
    ):
        raise ValueError("unexpected predecessor identity")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    facts = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")), {"Tenderize"}
    )
    card = facts["Tenderize"]
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] != card.name or row["oracle_fragment"] != card.oracle_text:
            continue
        semantics = interpreter.damage_semantic_coverage(card, row["oracle_fragment"])
        if (
            row["execution_review"] != "gap"
            or row["impact_priority"] != "P0"
            or semantics is None
            or not semantics.coverage.fully_supported
            or interpreter.cast_program(card).kind is not CastKind.CREATURE_POWER_DAMAGE
            or (row["oracle_fragment"], row["scanner_reason"])
            in interpreter.unsupported_fragments(card)
        ):
            raise ValueError("two-target damage has not closed honestly")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Generic instant two-creature target pair, mana and priority, current source power "
            "at resolution, noncombat damage provenance, and state-based death"
        )
        closed.append(
            {"deck": row["deck"], "card": row["card"], "oracle_fragment": row["oracle_fragment"]}
        )
    if len(closed) != 1:
        raise ValueError("unexpected closure membership")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if counts["priority"] != {"none": 87, "P0": 21, "P1": 64} or counts["execution"] != {
        "covered": 33,
        "gap": 82,
        "annotation": 7,
        "partial": 3,
        "supported": 47,
    }:
        raise ValueError("unexpected overlay totals")
    return {
        "schema": "issue289-creature-power-damage-checkpoint-v1",
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
