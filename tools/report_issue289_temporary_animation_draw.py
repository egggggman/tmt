"""Append complete temporary animation-and-draw coverage to the 172-row ledger overlay."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_COUNTER_KEYWORD_GRANT_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_TEMPORARY_ANIMATION_DRAW_CHECKPOINT.json"
LEDGER_SHA = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA = "3322db61328575c4b3fe21119997e1b1356efc6e96931f5436dfe644408c4a32"
PREVIOUS_RUNTIME = "1ecd33d0702f60c5c892a94a43112c238874518334cdcb4ed80acf5d831a57ca"


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
        or previous["counts"]["priority"] != {"none": 100, "P0": 11, "P1": 61}
    ):
        raise ValueError("unexpected predecessor coverage")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    card = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Mind Transfer Protocol"},
    )["Mind Transfer Protocol"]
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] != card.name:
            continue
        fragment = row["oracle_fragment"]
        program = interpreter.temporary_type_base_pt_draw_program(card)
        if program is None or fragment not in {program.effect_fragment, program.draw_fragment}:
            continue
        if (
            row["execution_review"] != "gap"
            or row["impact_priority"] != "P0"
            or (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card)
        ):
            raise ValueError("animation-and-draw spell clause did not execute completely")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Complete generic instant: legal artifact-or-creature target and normal payment/"
            "priority, temporary artifact-creature type in layer 4 and base P/T in layer 7b, "
            "coupled card draw, target resolution checks, SBA and cleanup"
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if len(closed) != 2 or counts["priority"] != {"none": 102, "P0": 9, "P1": 61}:
        raise ValueError("unexpected row closure")
    if counts["execution"] != {
        "covered": 33,
        "supported": 62,
        "annotation": 7,
        "gap": 68,
        "partial": 2,
    }:
        raise ValueError("unexpected execution totals")
    return {
        "schema": "issue289-temporary-animation-draw-checkpoint-v1",
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
                "Mind Transfer Protocol has three frozen April copies and two critical rows, "
                "affecting combat and card access; one generic animation-and-draw path closes "
                "both. Raphael's linked exile/play family has two copies and two rows but "
                "requires broader permission handling; recursion and library-search families "
                "have two copies or fewer and more choice/zone complexity. The existing layer "
                "7b, draw, stack, and targeting paths minimize new rules surface."
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
