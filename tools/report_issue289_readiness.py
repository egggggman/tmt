"""Overlay tested deathtouch closure on the preserved Issue 289 coverage ledger.

This reporting tool never changes card data, runtime behavior, or the prior ledger.
Unknown ledger shapes fail closed; semantic coverage is checked against frozen facts.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import load_facts

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_READINESS_CHECKPOINT.json"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
PREVIOUS_LEDGER_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
HISTORICAL_RUNTIME = "d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924"


def report() -> dict[str, object]:
    raw = LEDGER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PREVIOUS_LEDGER_SHA256:
        raise ValueError("preserved acceptance ledger identity changed")
    rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    if len(rows) != 172:
        raise ValueError("preserved acceptance ledger is incomplete")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    catalog = load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json"))
    names = {row["card"] for row in rows}
    facts = load_facts(catalog, names)
    interpreter = CardInterpreter()
    closed = []
    for row in rows:
        fragment = row["oracle_fragment"]
        card = facts[row["card"]]
        intrinsic = (
            fragment == "Deathtouch"
            and "deathtouch" in {keyword.casefold() for keyword in card.keywords}
            and row["execution_review"] == "gap"
        )
        grant = (
            row["execution_review"] == "partial"
            and fragment.endswith(
                "another target creature you control gains deathtouch until end of turn."
            )
            and (coverage := interpreter.shredder_deathtouch_semantic_coverage(card, fragment))
            is not None
            and coverage.fully_supported
        )
        if intrinsic or grant:
            row["execution_review"] = "supported"
            row["impact_priority"] = "none"
            row["disposition"] = "Positive damage destroys creature under state-based actions"
            closed.append((row["deck"], row["card"], fragment))
    if len(closed) != 6:
        raise ValueError(f"unexpected deathtouch closure count: {len(closed)}")
    counts = Counter(row["execution_review"] for row in rows)
    priorities = Counter(row["impact_priority"] for row in rows)
    if counts != {"covered": 33, "annotation": 7, "partial": 3, "gap": 123, "supported": 6}:
        raise ValueError(f"unexpected coverage: {counts}")
    if priorities != {"none": 46, "P0": 55, "P1": 71}:
        raise ValueError(f"unexpected priorities: {priorities}")
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    return {
        "schema": "issue289-readiness-checkpoint-v1",
        "base_ledger_sha256": PREVIOUS_LEDGER_SHA256,
        "baseline_manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "catalog_sha256": hashlib.sha256(CATALOG.read_bytes()).hexdigest(),
        "baseline_id": manifest.get("baseline_id", "OBL-BASELINE-005"),
        "historical_runtime_sha256": HISTORICAL_RUNTIME,
        "semantic_runtime_sha256": runtime,
        "compatible_with_historical_control": runtime == HISTORICAL_RUNTIME,
        "gate": "BLOCKED",
        "control_authorized": False,
        "counts": {"execution": dict(counts), "priority": dict(priorities)},
        "closed_deathtouch_rows": [
            {"deck": deck, "card": card, "oracle_fragment": fragment}
            for deck, card, fragment in closed
        ],
        "rows": rows,
    }


def main() -> None:
    result = report()
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("gate", "counts", "semantic_runtime_sha256")}))


if __name__ == "__main__":
    main()
