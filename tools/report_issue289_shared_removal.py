"""Overlay verified shared removal closure on the immutable Issue 289 ledger."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_SHARED_INTERACTION_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_SHARED_REMOVAL_CHECKPOINT.json"
ORIGINAL_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA256 = "5b581fdf101822dd504dd44134fbc8d0c7fccafe89b7b8d2c816bf267b1d0167"
EXPECTED_CARDS = {"Spicy Oatmeal Pizza", "Mutant Chain Reaction"}


def report() -> dict[str, object]:
    previous_digest = hashlib.sha256(PREVIOUS.read_bytes()).hexdigest()
    if previous_digest != PREVIOUS_SHA256:
        raise ValueError("shared interaction checkpoint changed")
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if previous["base_ledger_sha256"] != ORIGINAL_SHA256 or len(previous["rows"]) != 172:
        raise ValueError("original ledger identity changed")
    if previous["semantic_runtime_sha256"] != (
        "5a7b948a7c6745971bfb9d66471aee4a369363ff944f2926fad0536700f7aed3"
    ):
        raise ValueError("parent runtime identity changed")
    if (
        hashlib.sha256(
            (ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv").read_bytes()
        ).hexdigest()
        != ORIGINAL_SHA256
    ):
        raise ValueError("original 172-row ledger changed")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    facts = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")), EXPECTED_CARDS
    )
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] not in EXPECTED_CARDS:
            continue
        card = facts[row["card"]]
        fragment = row["oracle_fragment"]
        coverage = interpreter.shared_removal_semantic_coverage(card, fragment)
        if coverage is None or not coverage.fully_supported:
            raise ValueError("shared removal clause is not executable")
        if (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card):
            raise ValueError("shared removal clause remains unsupported")
        if row["execution_review"] != "gap" or row["impact_priority"] != "P0":
            raise ValueError("unexpected preceding disposition")
        closed.append(
            {
                "deck": row["deck"],
                "card": row["card"],
                "oracle_fragment": fragment,
                "before": row["impact_priority"],
            }
        )
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "ETB stack target; simultaneous target/self damage; life checked afterward"
            if row["card"] == "Spicy Oatmeal Pizza"
            else "Optional legal removal target rechecked on resolution; Mutagen enters"
        )
    if len(closed) != 8 or Counter(item["card"] for item in closed) != {
        "Spicy Oatmeal Pizza": 6,
        "Mutant Chain Reaction": 2,
    }:
        raise ValueError("unexpected shared removal closure count")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if counts["priority"] != {"none": 71, "P0": 33, "P1": 68}:
        raise ValueError("unexpected priority counts")
    return {
        "schema": "issue289-shared-removal-checkpoint-v1",
        "baseline_id": previous["baseline_id"],
        "base_ledger_sha256": ORIGINAL_SHA256,
        "previous_checkpoint_sha256": previous_digest,
        "before_runtime_sha256": previous["semantic_runtime_sha256"],
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
