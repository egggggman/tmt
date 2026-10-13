"""Overlay the exact Issue 289 ledger after generic sacrifice-damage activation."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import load_facts

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_RESTRICTED_MANA_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_ACTIVATED_DAMAGE_CHECKPOINT.json"
ORIGINAL_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA256 = "2a4efb70a6e8ae06d4de7dd8f3992f9abca7f30e8ce123ba3bd9023531539745"
PREVIOUS_RUNTIME = "0d953551f6faee293e74afb9642c75c8cc7a9c93142f64a4c0d7b45537d3832a"


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
        load_card_data(catalog, catalog.with_suffix(".manifest.json")), {"Mouser Foundry"}
    )
    card = facts["Mouser Foundry"]
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] != card.name or "deals 3 damage" not in row["oracle_fragment"]:
            continue
        fragment = row["oracle_fragment"]
        semantics = interpreter.activated_ability_semantics(card, fragment)
        damage = interpreter.damage_semantic_coverage(card, fragment)
        if (
            row["execution_review"] != "gap"
            or row["impact_priority"] != "P0"
            or semantics is None
            or not semantics.coverage.fully_supported
            or semantics.program.effect_kind
            is not ActivatedEffectKind.DEAL_FIXED_DAMAGE_TO_TARGET_CREATURE
            or damage is None
            or not damage.coverage.fully_supported
            or (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card)
        ):
            raise ValueError("activated damage has not closed honestly")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Generic noncreature-artifact mana and sacrifice cost, legal creature target, "
            "stack-independent fixed damage from last-known source, and state-based death"
        )
        closed.append({"deck": row["deck"], "card": row["card"], "oracle_fragment": fragment})
    if len(closed) != 1:
        raise ValueError("unexpected closure membership")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if counts["priority"] != {"none": 86, "P0": 22, "P1": 64} or counts["execution"] != {
        "covered": 33,
        "gap": 83,
        "annotation": 7,
        "partial": 3,
        "supported": 46,
    }:
        raise ValueError("unexpected overlay totals")
    return {
        "schema": "issue289-activated-damage-checkpoint-v1",
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
