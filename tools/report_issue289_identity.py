"""Add the validated identity checkpoint without mutating the 172-row source ledger."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_SHARED_REMOVAL_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_IDENTITY_CHECKPOINT.json"
ORIGINAL_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA256 = "6fb3f210a07ac02282e7cffbfad619682282b49794b058fa10e216ebaa74275e"
PREVIOUS_RUNTIME = "9d263bb6151f3060dcacd59482f14a35d7759f1f0daae2a54c28c6dc0cb561a2"
CLOSED = {
    "Bebop & Rocksteady": "combat_discard_or_sacrifice",
    "Raphael, Ninja Destroyer": "must_be_blocked",
    "April O'Neil, Hacktivist": "end_step_spell_types_draw",
}
PARTIAL = {"Raphael, Most Attitude": "linked_exile_play"}


def report() -> dict[str, object]:
    if hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() != PREVIOUS_SHA256:
        raise ValueError("previous checkpoint bytes changed")
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if (previous["base_ledger_sha256"], previous["semantic_runtime_sha256"]) != (
        ORIGINAL_SHA256,
        PREVIOUS_RUNTIME,
    ) or len(previous["rows"]) != 172:
        raise ValueError("previous checkpoint identity changed")
    if (
        hashlib.sha256(
            (ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv").read_bytes()
        ).hexdigest()
        != ORIGINAL_SHA256
    ):
        raise ValueError("original ledger changed")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    facts = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        CLOSED.keys() | PARTIAL.keys(),
    )
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    assessed_partial = []
    for row in rows:
        card = facts.get(row["card"])
        if card is None or row["card"] not in CLOSED | PARTIAL:
            continue
        fragment = row["oracle_fragment"]
        if row["card"] in CLOSED:
            supported = {
                "combat_discard_or_sacrifice": interpreter.combat_discard_or_sacrifice,
                "must_be_blocked": interpreter.must_be_blocked,
                "end_step_spell_types_draw": lambda _c, f: interpreter.end_step_spell_types_draw(f),
            }[CLOSED[row["card"]]](card, fragment)
            if not supported:
                continue
            if row["execution_review"] != "gap" or row["impact_priority"] != "P0":
                raise ValueError("unexpected closure predecessor")
            if (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card):
                raise ValueError("closed clause still unsupported")
            closed.append({"deck": row["deck"], "card": row["card"], "oracle_fragment": fragment})
            row["execution_review"] = "supported"
            row["impact_priority"] = "none"
            row["disposition"] = (
                "Authenticated declaration trigger and mandatory discard or sacrifice"
                if row["card"] == "Bebop & Rocksteady"
                else "Maximal legal block requirements"
                if row["card"] == "Raphael, Ninja Destroyer"
                else "End-step stack trigger counts distinct cast spell types this turn"
            )
        elif interpreter.linked_top_exile(card, fragment) or interpreter.linked_attack_play(
            card, fragment
        ):
            if row["execution_review"] != "partial":
                raise ValueError("linked permission was not partial")
            assessed_partial.append(fragment)
            row["disposition"] = (
                "Linked object identity, duration, source-independent resolution and ordinary "
                "land/creature/spell main-phase options execute; remaining cast-family breadth "
                "and pilot behavior require further review"
            )
    if len(closed) != 3 or len(assessed_partial) != 2:
        raise ValueError("unexpected identity closure membership")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if counts["priority"] != {"none": 74, "P0": 30, "P1": 68}:
        raise ValueError("unexpected identity impact totals")
    return {
        "schema": "issue289-identity-checkpoint-v1",
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
        "assessed_partial_rows": assessed_partial,
        "rows": rows,
    }


def main() -> None:
    result = report()
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("gate", "counts", "semantic_runtime_sha256")}))


if __name__ == "__main__":
    main()
