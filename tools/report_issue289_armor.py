"""Append the Equipment sacrifice/entry checkpoint to the immutable Issue 289 ledger."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_ALLIANCE_EQUIPMENT_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_ARMOR_CHECKPOINT.json"
ORIGINAL_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_RUNTIME = "d27c9c8f7aeb82a3311b6cc72586b6a5103c0f8ce333588fe13c41812e6c7e2d"


def report() -> dict[str, object]:
    previous_sha = hashlib.sha256(PREVIOUS.read_bytes()).hexdigest()
    original_sha = hashlib.sha256(
        (ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv").read_bytes()
    ).hexdigest()
    if original_sha != ORIGINAL_SHA256:
        raise ValueError("original 172-row ledger changed")
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if (
        previous["semantic_runtime_sha256"] != PREVIOUS_RUNTIME
        or previous["base_ledger_sha256"] != original_sha
        or len(previous["rows"]) != 172
        or previous["counts"]["priority"] != {"none": 89, "P0": 20, "P1": 63}
    ):
        raise ValueError("predecessor identity or coverage differs")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    card = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Shredder's Armor"},
    )["Shredder's Armor"]
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] != card.name:
            continue
        fragment = row["oracle_fragment"]
        entry = interpreter.equipment_etb_attach(card, fragment)
        activation = interpreter.activated_ability_semantics(card, fragment)
        equip = bool(
            activation is not None
            and activation.coverage.fully_supported
            and activation.program.cost.sacrifice_other_nonland
        )
        if not (entry or equip):
            continue
        if (
            row["execution_review"] != "gap"
            or row["impact_priority"] not in {"P0", "P1"}
            or (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card)
        ):
            raise ValueError("Equipment closure is not supported by execution")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Generic targeted Equipment entry trigger with legal stack resolution"
            if entry
            else "Generic sorcery-speed Equip cost sacrifices another controlled nonland "
            "permanent; once-per-turn source history and target legality checked"
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if len(closed) != 2 or counts["priority"] != {"none": 91, "P0": 19, "P1": 62}:
        raise ValueError("unexpected Equipment closure membership/counts")
    if counts["execution"] != {
        "covered": 33,
        "gap": 78,
        "annotation": 7,
        "partial": 3,
        "supported": 51,
    }:
        raise ValueError("unexpected execution counts")
    return {
        "schema": "issue289-armor-checkpoint-v1",
        "baseline_id": previous["baseline_id"],
        "base_ledger_sha256": original_sha,
        "previous_checkpoint_sha256": previous_sha,
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
