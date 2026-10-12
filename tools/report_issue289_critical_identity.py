"""Overlay newly executed linked-play, Class, and conditional removal semantics."""

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
PREVIOUS = ROOT / "docs/cardcade/ISSUE_289_IDENTITY_CHECKPOINT.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_CRITICAL_IDENTITY_CHECKPOINT.json"
ORIGINAL_SHA256 = "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100"
PREVIOUS_SHA256 = "d1fe2dca95f2e3a3426f1234de3df664f499ca314e59994ce361846c5aa40282"
PREVIOUS_RUNTIME = "4d1dd3aa00758c8bf150878bcc0379e0a92f9c604ca2339c478d3a1b533e24bb"
TARGETS = {"Raphael, Most Attitude", "Cool but Rude", "Tainted Treats"}


def report() -> dict[str, object]:
    if hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() != PREVIOUS_SHA256:
        raise ValueError("previous checkpoint bytes changed")
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if (
        previous["base_ledger_sha256"] != ORIGINAL_SHA256
        or previous["semantic_runtime_sha256"] != PREVIOUS_RUNTIME
        or len(previous["rows"]) != 172
        or hashlib.sha256(
            (ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv").read_bytes()
        ).hexdigest()
        != ORIGINAL_SHA256
    ):
        raise ValueError("historical coverage identity changed")
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    facts = load_facts(load_card_data(catalog, catalog.with_suffix(".manifest.json")), TARGETS)
    interpreter = CardInterpreter()
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    partial = []
    for row in rows:
        name, fragment = row["card"], row["oracle_fragment"]
        if name not in TARGETS:
            continue
        card = facts[name]
        if name == "Raphael, Most Attitude":
            supported = bool(
                interpreter.linked_top_exile(card, fragment)
                or interpreter.linked_attack_play(card, fragment)
            )
            if supported:
                if row["execution_review"] != "partial" or row["impact_priority"] != "P0":
                    raise ValueError("linked predecessor changed")
                row["disposition"] = (
                    "Linked chosen-card identity, turn duration and interpreted main/priority "
                    "casting execute with payment, targeting and source-independent stack; "
                    "an exiled card with an uninterpreted spell effect still cannot be played"
                )
                partial.append(fragment)
            continue
        elif name == "Cool but Rude":
            discard_draw = interpreter.discard_draw_semantic_coverage(card, fragment)
            activation = interpreter.activated_ability_semantics(card, fragment)
            supported = bool(
                (discard_draw is not None and discard_draw.coverage.fully_supported)
                or (activation is not None and activation.coverage.fully_supported)
                or interpreter.CLASS_DISCARD_DAMAGE.fullmatch(fragment)
                or interpreter.CLASS_LEVEL_THREE_SEARCH.fullmatch(fragment)
            )
            expected = "gap"
        else:
            supported = interpreter.conditional_destroy_and_create_program(card) is not None
            expected = "gap"
        if not supported:
            continue
        if row["execution_review"] != expected:
            raise ValueError("unexpected predecessor for semantic closure")
        if (fragment, row["scanner_reason"]) in interpreter.unsupported_fragments(card):
            raise ValueError("claimed clause still unsupported")
        closed.append(
            {"deck": row["deck"], "card": name, "oracle_fragment": fragment, "before": expected}
        )
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Linked exile identity and end-of-turn play permission with interpreted main/priority "
            "casting, payment, legal targets and source-independent stack resolution"
            if name == "Raphael, Most Attitude"
            else "Class level gating, attack loot, discard damage, and level-three search/shuffle/"
            "random discard execute through reusable events and stack"
            if name == "Cool but Rude"
            else "Artifact/creature target and last-known mana value govern destruction "
            "and Food entry"
        )
    if (
        len(closed) != 6
        or len(partial) != 2
        or Counter(row["card"] for row in closed)
        != {
            "Cool but Rude": 5,
            "Tainted Treats": 1,
        }
    ):
        raise ValueError("unexpected closure membership")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if counts["priority"] != {"none": 80, "P0": 27, "P1": 65}:
        raise ValueError("unexpected remaining impact counts")
    return {
        "schema": "issue289-critical-identity-checkpoint-v1",
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
        "assessed_partial_rows": partial,
        "rows": rows,
    }


def main() -> None:
    result = report()
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("gate", "counts", "semantic_runtime_sha256")}))


if __name__ == "__main__":
    main()
