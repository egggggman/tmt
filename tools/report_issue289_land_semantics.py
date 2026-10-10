"""Overlay tested land entry/payment closure on the immutable Issue 289 ledger."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_CRITICAL_SEMANTICS_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_LAND_SEMANTICS_CHECKPOINT.json"
PREVIOUS_SHA256 = "dae33999c1e1bc6351b3c120ce32ad1b4675288c42c5c1575180b6b292d6cd1d"
ORIGINAL_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"


def report() -> dict[str, object]:
    if hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() != PREVIOUS_SHA256:
        raise ValueError("PR #294 checkpoint changed")
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if previous["base_ledger_sha256"] != ORIGINAL_SHA256 or len(previous["rows"]) != 172:
        raise ValueError("original ledger identity changed")
    rows = [dict(row) for row in previous["rows"]]
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    facts = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Illegitimate Business"},
    )
    land = facts["Illegitimate Business"]
    interpreter = CardInterpreter()
    closed = []
    for row in rows:
        if row["card"] != land.name or row["deck"] != "bebop_rocksteady":
            continue
        fragment = row["oracle_fragment"]
        if fragment == "This land enters tapped.":
            supported = interpreter.enters_tapped_semantics(land)
            disposition = "Printed tapped-entry replacement applies before land availability"
        elif fragment == "When this land enters, you gain 1 life.":
            semantics = interpreter.etb_self_life_gain_semantics(land, fragment)
            supported = semantics is not None and semantics[0] == 1 and semantics[1].fully_supported
            disposition = "Authenticated permanent-entry trigger gains one life after priority"
        elif fragment == "{T}: Add {B} or {G}.":
            supported = interpreter.land_mana_outputs(land, fragment) == ("B", "G")
            disposition = "Payment chooses a printed mana output from the land"
        else:
            continue
        if not supported or row["impact_priority"] != "P0":
            raise ValueError("land closure failed semantic or severity authentication")
        if (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(land):
            raise ValueError("land fragment still classified as unsupported")
        before = row["execution_review"]
        if before not in {"gap", "partial"}:
            raise ValueError("unexpected prior land disposition")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = disposition
        closed.append(
            {
                "deck": row["deck"],
                "card": row["card"],
                "oracle_fragment": fragment,
                "before": before,
            }
        )
    if Counter(item["before"] for item in closed) != {"gap": 3, "partial": 1}:
        raise ValueError("unexpected land closure count")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if counts["priority"] != {"none": 55, "P0": 46, "P1": 71}:
        raise ValueError("unexpected new priority counts")
    return {
        "schema": "issue289-land-semantics-checkpoint-v1",
        "baseline_id": previous["baseline_id"],
        "base_ledger_sha256": ORIGINAL_SHA256,
        "previous_checkpoint_sha256": PREVIOUS_SHA256,
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
