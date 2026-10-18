"""Publish final Issue #289 coverage and simulator-readiness assessment."""

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
PREVIOUS = DOCS / "ISSUE_289_HAMATO_GUARDIAN_STANCE_CHECKPOINT.json"
BEFORE = DOCS / "ISSUE_289_HAMATO_GUARDIAN_STANCE_CALIBRATION_READINESS.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
OVERLAY = DOCS / "ISSUE_289_MICHELANGELO_IMPROVISER_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_MICHELANGELO_IMPROVISER_CALIBRATION_READINESS.json"
NAME = "Michelangelo, Improviser"
FRAGMENT = (
    "Whenever Michelangelo deals combat damage to a player, you may put a creature card "
    "and/or a land card from your hand onto the battlefield."
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    previous = json.loads(PREVIOUS.read_text())
    assessment = json.loads(BEFORE.read_text())
    if len(previous["rows"]) != 172 or len(assessment["ranked_important_rows"]) != 1:
        raise ValueError("predecessor coverage changed")
    card = load_facts(load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")), {NAME})[NAME]
    interpreter = CardInterpreter()
    if not interpreter.combat_damage_hand_battlefield(card, FRAGMENT):
        raise ValueError("complete Improviser effect is not executable")
    if interpreter.unsupported_fragments(card):
        raise ValueError("Improviser retains unsupported fragments")
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] == NAME and row["oracle_fragment"] == FRAGMENT:
            if row["deck"] != "michelangelo" or row["execution_review"] != "gap":
                raise ValueError("target row differs from frozen gap")
            row["execution_review"] = "supported"
            row["impact_priority"] = "none"
            row["disposition"] = (
                "Complete generic combat-damage hand selection and battlefield entry; neither, "
                "creature-only, land-only, and one-of-each choices, source departure, ownership, "
                "entry triggers, state-based actions and deterministic replay verified."
            )
            closed.append({k: row[k] for k in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if len(closed) != 1 or counts["priority"] != {"none": 172} or counts["execution"].get("gap", 0):
        raise ValueError(f"unexpected final coverage: {counts}")
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    manifest = json.loads(MANIFEST.read_text())
    overlay = {
        "schema": "issue289-michelangelo-improviser-checkpoint-v1",
        "baseline_id": "OBL-BASELINE-005",
        "base_ledger_sha256": sha(LEDGER),
        "previous_checkpoint_sha256": sha(PREVIOUS),
        "before_runtime_sha256": previous["semantic_runtime_sha256"],
        "semantic_runtime_sha256": runtime,
        "baseline_manifest_sha256": sha(MANIFEST),
        "frozen_deck_sha256": {d["deck_key"]: d["sha256"] for d in manifest["decks"]},
        "historical_runtime_sha256": previous["historical_runtime_sha256"],
        "gate": "READY_PENDING_HQ_AUTHORIZATION",
        "control_authorized": False,
        "before_counts": previous["counts"],
        "counts": counts,
        "closure_kind": "combat_damage_optional_hand_battlefield_entry",
        "new_semantic_families": ["combat_damage_hand_battlefield_entry"],
        "closed_rows": closed,
        "corrected_existing_coverage_rows": [],
        "rows": rows,
    }
    readiness = {
        "schema": "issue289-michelangelo-improviser-calibration-readiness-v1",
        "baseline_id": "OBL-BASELINE-005",
        "checkpoint_overlay_sha256": None,
        "semantic_runtime_sha256": runtime,
        "original_ledger_sha256": sha(LEDGER),
        "critical_remaining": 0,
        "important_remaining": 0,
        "important_blockers": 0,
        "unbounded_residual_important": 0,
        "calibration_readiness": "READY",
        "control_authorized": False,
        "recommendation": "READY_FOR_HQ_AUTHORIZATION",
        "reason": (
            "All 172 ledger rows are supported or explicitly annotated; the final combat-damage "
            "hand-entry family is executable and deterministic. HQ must separately authorize any "
            "4,500-game Baseline 005 control."
        ),
        "engine_readiness_audit": {
            "oracle_coverage": "0 critical, 0 important, 0 unbounded",
            "pilot_quality": (
                "Choices are legal, private-hand selection is deterministic, and no "
                "named-deck dispatch is used."
            ),
            "determinism": (
                "Focused fixtures, frozen diagnostics, and full replay checks are "
                "required evidence below."
            ),
            "known_limitations": (
                "No unsupported gameplay rows remain; diagnostic exposure is not balance evidence."
            ),
            "historical_preservation": (
                "Baseline 005 deck hashes, 172 row identities, prior overlays and "
                "historical runtimes preserved."
            ),
        },
        "score_formula": assessment["score_formula"],
        "score_scales": assessment["score_scales"],
        "ranked_important_rows": [],
        "ranked_mechanic_families": [],
        "ranked_family_order": [],
        "separate_unbounded_rows_preserved": [],
        "original_unbounded_dispositions": [
            {"deck": "leonardo", "card": "Hamato Guardian Stance", "disposition": "implemented"},
            {"deck": "michelangelo", "card": NAME, "disposition": "implemented"},
        ],
    }
    OVERLAY.write_text(json.dumps(overlay, indent=2) + "\n")
    readiness["checkpoint_overlay_sha256"] = sha(OVERLAY)
    READINESS.write_text(json.dumps(readiness, indent=2) + "\n")
    print(
        json.dumps(
            {
                "runtime": runtime,
                "counts": counts,
                "overlay": str(OVERLAY),
                "readiness": str(READINESS),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
