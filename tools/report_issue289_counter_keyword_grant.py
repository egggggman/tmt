"""Append complete counter-and-keyword instant coverage to the 172-row ledger overlay."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_MODAL_SPELL_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_COUNTER_KEYWORD_GRANT_CHECKPOINT.json"
LEDGER_SHA = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA = "899c16171c0ce61056033bff50abe77068035819ad9f6828a6d45428edabc77c"
PREVIOUS_RUNTIME = "82e98882e36523ade85ee4261a8f0f7675bef98fa50ac4d96d43469d6f2fcf77"


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
        or previous["counts"]["priority"] != {"none": 97, "P0": 14, "P1": 61}
    ):
        raise ValueError("unexpected predecessor coverage")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    card = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Saved by the Shell"},
    )["Saved by the Shell"]
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] != card.name:
            continue
        fragment = row["oracle_fragment"]
        grant = interpreter.targeted_counter_keyword_grant_program(card)
        if grant is None or fragment not in {
            grant.effect_fragment,
            grant.cost_reduction.oracle_fragment if grant.cost_reduction is not None else "",
        }:
            continue
        trample = interpreter.trample_semantic_coverage(card, grant.effect_fragment)
        if trample is None or not trample.coverage.fully_supported:
            raise ValueError("counter-and-keyword spell lacks complete trample coverage")
        if (
            row["execution_review"] not in {"gap", "partial"}
            or row["impact_priority"] != "P0"
            or (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card)
        ):
            raise ValueError("counter-and-keyword spell clause did not execute completely")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Complete generic instant: conditional generic cost reduction, legal controlled "
            "creature target and normal payment/Priority, +1/+1 counter placement, temporary "
            "trample/hexproof/indestructible, target resolution checks, SBA and cleanup"
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if len(closed) != 3 or counts["priority"] != {"none": 100, "P0": 11, "P1": 61}:
        raise ValueError("unexpected row closure")
    if counts["execution"] != {
        "covered": 33,
        "supported": 60,
        "annotation": 7,
        "gap": 70,
        "partial": 2,
    }:
        raise ValueError("unexpected execution totals")
    return {
        "schema": "issue289-counter-keyword-grant-checkpoint-v1",
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
            "selected_rank_family": 1,
            "selected_card_copies": 3,
            "reason": (
                "Both spells have three frozen copies. Saved by the Shell closes three "
                "critical rows with the existing conditional discount, counter placement, "
                "temporary keywords and combat rules plus general hexproof and indestructible "
                "evaluation. Mind Transfer Protocol closes two rows but requires a new "
                "temporary type layer, base P/T setting, and draw coupling."
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
