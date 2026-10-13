"""Preserve every Issue 289 row and overlay verified restricted-mana support."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_CASTING_RESOURCES_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_RESTRICTED_MANA_CHECKPOINT.json"
ORIGINAL_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA256 = "555fda0587cdfbb30cabf522a27d522628736dfbd1114d5c97f3b672b08c70a2"
PREVIOUS_RUNTIME = "a3044b406738ae66f12ad3173a655849a5b5317ae2c009d80a460edfca94a178"


def report() -> dict[str, object]:
    if hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() != PREVIOUS_SHA256:
        raise ValueError("previous checkpoint changed")
    if (
        hashlib.sha256(
            (ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv").read_bytes()
        ).hexdigest()
        != ORIGINAL_SHA256
    ):
        raise ValueError("original coverage ledger changed")
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if (
        previous["semantic_runtime_sha256"] != PREVIOUS_RUNTIME
        or previous["base_ledger_sha256"] != ORIGINAL_SHA256
        or len(previous["rows"]) != 172
    ):
        raise ValueError("unexpected predecessor identity")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    facts = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Purple Dragon Punks"},
    )
    card = facts["Purple Dragon Punks"]
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] != card.name:
            continue
        fragment = row["oracle_fragment"]
        semantics = interpreter.activated_ability_semantics(card, fragment)
        program = interpreter.mana_ability_program(fragment)
        if (
            row["execution_review"] != "gap"
            or row["impact_priority"] != "P0"
            or semantics is None
            or not semantics.coverage.fully_supported
            or program is None
            or program.allowed_spending != ("artifact_spell", "activate_ability")
            or (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card)
        ):
            raise ValueError("restricted mana has not closed honestly")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Generic tapped mana ability produces a source-linked restricted unit; "
            "eligible artifact spells and activated abilities pay by exact unit; "
            "other spells cannot use it; mana expires at step boundaries"
        )
        closed.append({"deck": row["deck"], "card": row["card"], "oracle_fragment": fragment})
    if len(closed) != 1:
        raise ValueError("unexpected closure membership")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if counts["priority"] != {"none": 85, "P0": 23, "P1": 64} or counts["execution"] != {
        "covered": 33,
        "gap": 84,
        "annotation": 7,
        "partial": 3,
        "supported": 45,
    }:
        raise ValueError("unexpected overlay totals")
    return {
        "schema": "issue289-restricted-mana-checkpoint-v1",
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
