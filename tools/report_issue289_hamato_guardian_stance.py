"""Publish the Hamato Guardian Stance semantic checkpoint without changing the ledger."""

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
PREVIOUS = DOCS / "ISSUE_289_DONATELLO_ARTIFACT_COPY_CHECKPOINT.json"
BEFORE = DOCS / "ISSUE_289_DONATELLO_ARTIFACT_COPY_CALIBRATION_READINESS.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
OVERLAY = DOCS / "ISSUE_289_HAMATO_GUARDIAN_STANCE_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_HAMATO_GUARDIAN_STANCE_CALIBRATION_READINESS.json"
NAME = "Hamato Guardian Stance"
FRAGMENT = (
    "Target creature gets +1/+3 and gains flying until end of turn. Scry 1. "
    "(Look at the top card of your library. You may put that card on the bottom.)"
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    previous = json.loads(PREVIOUS.read_text())
    assessment = json.loads(BEFORE.read_text())
    if len(previous["rows"]) != 172 or len(assessment["ranked_important_rows"]) != 2:
        raise ValueError("predecessor coverage changed")
    card = load_facts(load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")), {NAME})[NAME]
    interpreter = CardInterpreter()
    program = interpreter.targeted_pump_flying_scry_program(card)
    if program is None or interpreter.unsupported_fragments(card):
        raise ValueError("complete Hamato effect is not executable")
    rows = [dict(row) for row in previous["rows"]]
    closed = []
    for row in rows:
        if row["card"] == NAME and row["oracle_fragment"] == FRAGMENT:
            if row["deck"] != "leonardo" or row["execution_review"] != "gap":
                raise ValueError("target row differs from frozen gap")
            row["execution_review"] = "supported"
            row["impact_priority"] = "none"
            row["disposition"] = (
                "Complete targeted temporary +1/+3, flying, and Scry 1; legal target, "
                "payment, resolution, cleanup, source independence and deterministic "
                "replay verified."
            )
            closed.append({k: row[k] for k in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if len(closed) != 1 or counts["priority"] != {"none": 171, "P1": 1}:
        raise ValueError(f"unexpected closure: {counts}")
    remaining = [item for item in assessment["ranked_important_rows"] if item["card"] != NAME]
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    manifest = json.loads(MANIFEST.read_text())
    overlay = {
        "schema": "issue289-hamato-guardian-stance-checkpoint-v1",
        "baseline_id": "OBL-BASELINE-005",
        "base_ledger_sha256": sha(LEDGER),
        "previous_checkpoint_sha256": sha(PREVIOUS),
        "before_runtime_sha256": previous["semantic_runtime_sha256"],
        "semantic_runtime_sha256": runtime,
        "baseline_manifest_sha256": sha(MANIFEST),
        "frozen_deck_sha256": {d["deck_key"]: d["sha256"] for d in manifest["decks"]},
        "historical_runtime_sha256": previous["historical_runtime_sha256"],
        "gate": "BLOCKED",
        "control_authorized": False,
        "before_counts": previous["counts"],
        "counts": counts,
        "closure_kind": "targeted_temporary_pump_flying_scry",
        "new_semantic_families": ["targeted_temporary_keyword_and_pt", "spell_followup_scry"],
        "closed_rows": closed,
        "corrected_existing_coverage_rows": [],
        "rows": rows,
    }
    families = []
    for item in remaining:
        families.append(
            {
                "mechanic": item["mechanic"],
                "entries": 1,
                "score": item["priority_score"],
                "cards": [item["card"]],
                "decks": item["affected_decks"],
            }
        )
    readiness = {
        "schema": "issue289-hamato-guardian-stance-calibration-readiness-v1",
        "baseline_id": "OBL-BASELINE-005",
        "checkpoint_overlay_sha256": None,
        "semantic_runtime_sha256": runtime,
        "original_ledger_sha256": sha(LEDGER),
        "critical_remaining": 0,
        "important_remaining": 1,
        "important_blockers": 0,
        "unbounded_residual_important": 1,
        "calibration_readiness": "BLOCKED",
        "reason": (
            "Hamato Guardian Stance is closed; Michelangelo Improviser remains "
            "unbounded and calibration is not authorized."
        ),
        "score_formula": assessment["score_formula"],
        "score_scales": assessment["score_scales"],
        "ranked_important_rows": remaining,
        "ranked_mechanic_families": families,
        "ranked_family_order": [x["mechanic"] for x in families],
        "separate_unbounded_rows_preserved": [
            {k: item[k] for k in ("deck", "card", "oracle_fragment")} for item in remaining
        ],
        "original_unbounded_dispositions": [
            {
                "deck": "leonardo",
                "card": NAME,
                "oracle_fragment": FRAGMENT,
                "disposition": "implemented",
                "evidence": "Focused generic spell fixtures and deterministic replay.",
            },
            {
                "deck": "michelangelo",
                "card": "Michelangelo, Improviser",
                "oracle_fragment": remaining[0]["oracle_fragment"],
                "disposition": "still_unresolved",
                "evidence": remaining[0]["assessment"],
            },
        ],
    }
    OVERLAY.write_text(json.dumps(overlay, indent=2) + "\n")
    readiness["checkpoint_overlay_sha256"] = sha(OVERLAY)
    READINESS.write_text(json.dumps(readiness, indent=2) + "\n")
    print(
        json.dumps(
            {
                "runtime": runtime,
                "overlay": str(OVERLAY),
                "readiness": str(READINESS),
                "counts": counts,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
