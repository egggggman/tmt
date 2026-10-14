"""Regenerate the 172-row overlay for complete unrestricted library search."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_LIBRARY_RETURN_TOKEN_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_LIBRARY_SEARCH_CHECKPOINT.json"
LEDGER_SHA = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA = "d555ddf265d17fa9a29799aef71a962a75fe071ceb030e666e1b6806998832a2"
PREVIOUS_RUNTIME = "3ba2f858ffa06a24322f98dc2e0da218d53967fee6b385ef8cd1a252e6ad5fc0"


def report() -> dict[str, object]:
    if hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() != PREVIOUS_SHA:
        raise ValueError("previous checkpoint changed")
    ledger = ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv"
    if hashlib.sha256(ledger.read_bytes()).hexdigest() != LEDGER_SHA:
        raise ValueError("original ledger changed")
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if (
        previous["semantic_runtime_sha256"] != PREVIOUS_RUNTIME
        or len(previous["rows"]) != 172
        or previous["counts"]["priority"] != {"none": 103, "P1": 61, "P0": 8}
    ):
        raise ValueError("unexpected predecessor coverage")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    card = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Splinter's Technique"},
    )["Splinter's Technique"]
    interpreter = CardInterpreter()
    program = interpreter.library_search_to_hand_program(card)
    if (
        program is None
        or program.sneak_fragment is None
        or interpreter.cast_program(card).kind is not CastKind.LIBRARY_SEARCH_TO_HAND
        or not interpreter.sneak_semantic_coverage(
            card, program.sneak_fragment
        ).coverage.fully_supported
        or interpreter.unsupported_fragments(card)
    ):
        raise ValueError("complete search and alternative cost not executable")
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] != card.name or row["oracle_fragment"] != program.search_fragment:
            continue
        if row["execution_review"] != "gap" or row["impact_priority"] != "P0":
            raise ValueError("unexpected search row state")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Complete generic library search: ordinary or fixed Sneak cost, controller-only "
            "private legal card selection, move to hand with new zone identity, deterministic "
            "shuffle, priority, source independence and state-based actions"
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if len(closed) != 1 or counts != {
        "execution": {"covered": 33, "supported": 64, "annotation": 7, "gap": 66, "partial": 2},
        "priority": {"none": 104, "P1": 61, "P0": 7},
    }:
        raise ValueError("unexpected row closure")
    return {
        "schema": "issue289-library-search-checkpoint-v1",
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
            "selected_rank_family": "unrestricted_private_library_search",
            "selected_card_copies": 2,
            "reason": (
                "Two frozen Splinter copies tutor any library card, a high-impact resource "
                "action. Existing private selection, zone movement, deterministic shuffle, "
                "stack and fixed Sneak payment support make this smaller than Raphael's "
                "linked exile/play breadth or multi-target graveyard/top-eight recursion. "
                "The two-copy hand reset requires bilateral choices; one-copy attacking "
                "tokens require distinct combat-entry semantics."
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
    print(json.dumps({key: result[key] for key in ("counts", "semantic_runtime_sha256")}))
