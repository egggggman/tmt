"""Reproduce the complete targeted library-return overlay on the original 172 rows."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_TEMPORARY_ANIMATION_DRAW_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_LIBRARY_RETURN_TOKEN_CHECKPOINT.json"
LEDGER_SHA = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA = "d58dffb2f61b1556cd294fcd30316aaaf1d372099ca8134353a32b207ee2e382"
PREVIOUS_RUNTIME = "60bcdf05b99454f1e69015652c603f744c0df9a91e8dc83f0eb8fbb3128ebf1a"


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
        or previous["counts"]["priority"] != {"none": 102, "P1": 61, "P0": 9}
    ):
        raise ValueError("unexpected predecessor coverage")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    card = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Return to the Sewers"},
    )["Return to the Sewers"]
    interpreter = CardInterpreter()
    program = interpreter.targeted_library_return_and_token_program(card)
    if (
        program is None
        or interpreter.cast_program(card).kind is not CastKind.TARGETED_LIBRARY_RETURN_AND_TOKEN
        or interpreter.unsupported_fragments(card)
        or not interpreter.token_semantic_coverage(card, card.oracle_text).fully_supported
    ):
        raise ValueError("complete spell semantics are not executable")
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] != card.name or row["oracle_fragment"] != program.oracle_fragment:
            continue
        if row["execution_review"] != "gap" or row["impact_priority"] != "P0":
            raise ValueError("unexpected row state")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Generic legal creature target, normal payment and priority, resolution-time "
            "owner top/bottom library choice and zone identity, then executable artifact token "
            "creation, provenance, state-based actions and deterministic replay"
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if len(closed) != 1 or counts != {
        "execution": {"covered": 33, "supported": 63, "annotation": 7, "gap": 67, "partial": 2},
        "priority": {"none": 103, "P1": 61, "P0": 8},
    }:
        raise ValueError("unexpected row closure")
    return {
        "schema": "issue289-library-return-token-checkpoint-v1",
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
            "selected_rank_family": "targeted_library_return_and_token",
            "selected_card_copies": 2,
            "reason": (
                "Two frozen April copies affect removal and Mutagen resource output. Existing "
                "target, owner-zone, token, activation, payment and priority primitives make "
                "this the smallest complete family. Raphael linked permissions have high identity "
                "impact but broader permission complexity; recursion, search, hand reset and "
                "combat-entry tokens each require distinct choice or combat systems."
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
