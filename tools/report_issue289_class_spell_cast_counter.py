"""Close complete Class level-three activation and spell-cast team-counter rows."""

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
DOCS = ROOT / "docs/cardcade"
PREVIOUS = DOCS / "ISSUE_289_CLASS_LEVEL_TWO_CHECKPOINT.json"
BEFORE = DOCS / "ISSUE_289_CLASS_LEVEL_TWO_CALIBRATION_READINESS.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
OVERLAY = DOCS / "ISSUE_289_CLASS_SPELL_CAST_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_CLASS_SPELL_CAST_CALIBRATION_READINESS.json"
SHA = {
    PREVIOUS: "a4accedded441d5545f8bb741b8fe41baba96dcea8e1e1dcdb1f277c50aae81d",
    BEFORE: "e3d9826ca0b0dfcbcd5b89c17c2b5d887c761b2a416fb4d47c39ead8c5c688a9",
    LEDGER: "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100",
    MANIFEST: "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac",
}
NAME = "Leader's Talent"
LEVEL = "{3}{W}: Level 3"
EFFECT = "Whenever you cast a spell, put a +1/+1 counter on each creature you control."


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reports() -> tuple[dict, dict]:
    for path, expected in SHA.items():
        if sha(path) != expected:
            raise ValueError(f"frozen lineage changed: {path}")
    before, assessment = (json.loads(path.read_text()) for path in (PREVIOUS, BEFORE))
    if (
        len(before["rows"]) != 172
        or before["counts"]["priority"]["P1"] != 27
        or assessment["important_blockers"] != 23
        or assessment["unbounded_residual_important"] != 4
    ):
        raise ValueError("predecessor coverage changed")
    manifest = json.loads(MANIFEST.read_text())
    frozen = {}
    for deck in manifest["decks"]:
        path = ROOT / deck["source_path"]
        raw = path.read_bytes()
        crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        if deck["sha256"] not in {
            hashlib.sha256(raw).hexdigest(),
            hashlib.sha256(crlf).hexdigest(),
        }:
            raise ValueError("frozen Baseline 005 deck differs from manifest")
        frozen[deck["deck_key"]] = {
            name: int(count)
            for count, name in (
                line.split(" ", 1)
                for line in path.read_text().splitlines()
                if line and line != "Deck"
            )
        }
    card = load_facts(load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")), {NAME})[NAME]
    interpreter = CardInterpreter()
    rows = [dict(row) for row in before["rows"]]
    closed = []
    for row in rows:
        if row["card"] != NAME or row["oracle_fragment"] not in {LEVEL, EFFECT}:
            continue
        if (
            row["deck"] != "leonardo"
            or frozen[row["deck"]][NAME] != int(row["copies"])
            or int(row["copies"]) != 4
            or not interpreter.class_spell_cast_team_counter(card, EFFECT)
            or interpreter.class_level_child(card, 3) != EFFECT
            or not interpreter.activated_ability_semantics(card, LEVEL).coverage.fully_supported
            or interpreter.class_level_child(card, 2) is None
            or any(
                frag == row["oracle_fragment"]
                for frag, _ in interpreter.unsupported_fragments(card)
            )
        ):
            raise ValueError("incomplete level-three trigger or changed frozen Class")
        if row["impact_priority"] != "P1" or row["execution_review"] != "gap":
            raise ValueError("Class level-three row was not open")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Complete generic Class level-three {3}{W} activation and spell-cast trigger: "
            "counter each creature controlled at resolution, including new entrants; "
            "spell event, controller and source provenance, priority and replay verified."
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    keys = ("deck", "card", "oracle_fragment")
    if Counter(tuple(row[k] for k in keys) for row in rows) != Counter(
        tuple(row[k] for k in keys) for row in before["rows"]
    ):
        raise ValueError("original 172 row identities changed")
    if (
        len(closed) != 2
        or counts["priority"] != {"none": 147, "P1": 25}
        or counts["execution"] != {"covered": 33, "supported": 107, "annotation": 7, "gap": 25}
    ):
        raise ValueError("unexpected row closure")
    remaining = [
        item
        for item in assessment["ranked_important_rows"]
        if not any(
            all(item[key] == row[key] for key in ("deck", "card", "oracle_fragment"))
            for row in closed
        )
    ]
    if len(remaining) != 25:
        raise ValueError("ranked residual differs from overlay")
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    overlay = {
        "schema": "issue289-class-spell-cast-checkpoint-v1",
        "baseline_id": "OBL-BASELINE-005",
        "base_ledger_sha256": sha(LEDGER),
        "previous_checkpoint_sha256": sha(PREVIOUS),
        "before_runtime_sha256": before["semantic_runtime_sha256"],
        "semantic_runtime_sha256": runtime,
        "baseline_manifest_sha256": sha(MANIFEST),
        "frozen_deck_sha256": {d["deck_key"]: d["sha256"] for d in manifest["decks"]},
        "historical_runtime_sha256": before["historical_runtime_sha256"],
        "gate": "BLOCKED",
        "control_authorized": False,
        "before_counts": before["counts"],
        "counts": counts,
        "closed_rows": closed,
        "corrected_existing_coverage_rows": [],
        "rows": rows,
    }
    readiness = {
        "schema": "issue289-class-spell-cast-calibration-readiness-v1",
        "baseline_id": "OBL-BASELINE-005",
        "checkpoint_overlay_sha256": None,
        "semantic_runtime_sha256": runtime,
        "original_ledger_sha256": sha(LEDGER),
        "critical_remaining": 0,
        "important_remaining": 25,
        "important_blockers": 21,
        "unbounded_residual_important": 4,
        "calibration_readiness": "BLOCKED",
        "reason": (
            "21 important gameplay blockers still distort combat and resource "
            "outcomes; four residual impacts remain unbounded."
        ),
        "score_formula": assessment["score_formula"],
        "score_scales": assessment["score_scales"],
        "ranked_important_rows": remaining,
        "ranked_family_order": [
            "tribal_combat_modifier (Splinter, Hamato Yoshi; 4 copies)",
            "activation_costs_and_resource_trade (Ice Cream Kitty; 3 copies, linked costs/effects)",
            "artifact_entry_counters (Donatello, Way with Machines; 3 copies)",
            "artifact_token_cost_and_creation (Mutagen Man; 2 copies, variable X)",
        ],
        "separate_unbounded_rows_preserved": [
            {key: item[key] for key in ("deck", "card", "oracle_fragment")}
            for item in remaining
            if not item["calibration_blocker"]
        ],
    }
    if (
        sum(item["calibration_blocker"] for item in remaining) != 21
        or len(readiness["separate_unbounded_rows_preserved"]) != 4
        or readiness["separate_unbounded_rows_preserved"]
        != assessment["separate_unbounded_rows_preserved"]
    ):
        raise ValueError("residual calibration risk changed unexpectedly")
    return overlay, readiness


def main() -> None:
    overlay, readiness = reports()
    OVERLAY.write_text(json.dumps(overlay, indent=2) + "\n")
    readiness["checkpoint_overlay_sha256"] = sha(OVERLAY)
    READINESS.write_text(json.dumps(readiness, indent=2) + "\n")
    print(
        json.dumps(
            {
                "runtime": overlay["semantic_runtime_sha256"],
                "important": readiness["important_remaining"],
                "blockers": readiness["important_blockers"],
                "unbounded": readiness["unbounded_residual_important"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
