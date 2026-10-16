"""Record the provenance correction to generic artifact-entry self counters."""

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
PREVIOUS = DOCS / "ISSUE_289_STATIC_SUBTYPE_CHECKPOINT.json"
BEFORE = DOCS / "ISSUE_289_STATIC_SUBTYPE_CALIBRATION_READINESS.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
OVERLAY = DOCS / "ISSUE_289_ARTIFACT_ENTRY_COUNTER_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_ARTIFACT_ENTRY_COUNTER_CALIBRATION_READINESS.json"
SHA = {
    PREVIOUS: "8cd7f803220bf3dd9d21cebe74271eede90d691bc61ecbaf06aa8dfe9033df1d",
    BEFORE: "a7f54da09cf857c1f52b4d7570ec5d8ea18fb4d7895caada9947d66d7ab20143",
    LEDGER: "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100",
    MANIFEST: "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac",
}
NAME = "Donatello, Way with Machines"
EFFECT = "Whenever an artifact you control enters, put a +1/+1 counter on Donatello."


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reports() -> tuple[dict, dict]:
    for path, expected in SHA.items():
        if sha(path) != expected:
            raise ValueError(f"frozen lineage changed: {path}")
    before, assessment = (json.loads(path.read_text()) for path in (PREVIOUS, BEFORE))
    if (
        len(before["rows"]) != 172
        or before["counts"]["priority"]["P1"] != 24
        or assessment["important_blockers"] != 20
        or assessment["unbounded_residual_important"] != 4
    ):
        raise ValueError("predecessor coverage changed")
    manifest = json.loads(MANIFEST.read_text())
    frozen = {}
    for deck in manifest["decks"]:
        raw = (ROOT / deck["source_path"]).read_bytes()
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
                for line in (ROOT / deck["source_path"]).read_text().splitlines()
                if line and line != "Deck"
            )
        }
    card = load_facts(load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")), {NAME})[NAME]
    if EFFECT not in CardInterpreter().fragments(card):
        raise ValueError("frozen Oracle fragment changed")
    if (
        not CardInterpreter()
        .artifact_entry_self_counter_semantic_coverage(card, EFFECT)
        .fully_supported
    ):
        raise ValueError("entry self-counter recognizer is incomplete")
    rows = [dict(row) for row in before["rows"]]
    closed = []
    for row in rows:
        if row["card"] != NAME or row["oracle_fragment"] != EFFECT:
            continue
        if (
            row["deck"] != "donatello"
            or frozen[row["deck"]][NAME] != int(row["copies"])
            or int(row["copies"]) != 3
            or row["impact_priority"] != "P1"
            or row["execution_review"] != "gap"
        ):
            raise ValueError("artifact-entry row was not the expected frozen gap")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Existing generic entry trigger corrected: entry-time artifact/controller "
            "provenance is authenticated independently of the entering object's later "
            "zone, type and controller; original source incarnation receives the counter "
            "if still on the battlefield. No target. Priority, source loss/reentry, "
            "simultaneous entries, state-based actions and deterministic replay verified."
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    keys = ("deck", "card", "oracle_fragment")
    if Counter(tuple(row[k] for k in keys) for row in rows) != Counter(
        tuple(row[k] for k in keys) for row in before["rows"]
    ):
        raise ValueError("original 172 row identities changed")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if (
        len(closed) != 1
        or counts["priority"] != {"none": 149, "P1": 23}
        or counts["execution"] != {"covered": 33, "supported": 109, "annotation": 7, "gap": 23}
    ):
        raise ValueError("unexpected row closure")
    remaining = [
        item
        for item in assessment["ranked_important_rows"]
        if not any(all(item[key] == row[key] for key in keys) for row in closed)
    ]
    if len(remaining) != 23:
        raise ValueError("ranked residual differs from overlay")
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    overlay = {
        "schema": "issue289-artifact-entry-counter-checkpoint-v1",
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
        "closure_kind": "simulator_defect_correction_to_existing_trigger",
        "new_semantic_families": [],
        "closed_rows": closed,
        "corrected_existing_coverage_rows": closed,
        "rows": rows,
    }
    readiness = {
        "schema": "issue289-artifact-entry-counter-calibration-readiness-v1",
        "baseline_id": "OBL-BASELINE-005",
        "checkpoint_overlay_sha256": None,
        "semantic_runtime_sha256": runtime,
        "original_ledger_sha256": sha(LEDGER),
        "critical_remaining": 0,
        "important_remaining": 23,
        "important_blockers": 19,
        "unbounded_residual_important": 4,
        "calibration_readiness": "BLOCKED",
        "reason": (
            "19 important gameplay blockers still distort combat and resource "
            "outcomes; four residual impacts remain unbounded."
        ),
        "score_formula": assessment["score_formula"],
        "score_scales": assessment["score_scales"],
        "ranked_important_rows": remaining,
        "ranked_family_order": [
            "activation_costs_and_resource_trade (Ice Cream Kitty; 3 copies, two abilities)",
            "artifact_token_cost_and_creation (Mutagen Man; 2 copies, variable X)",
        ],
        "separate_unbounded_rows_preserved": [
            {key: item[key] for key in keys}
            for item in remaining
            if not item["calibration_blocker"]
        ],
    }
    if (
        sum(item["calibration_blocker"] for item in remaining) != 19
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
                "important": 23,
                "blockers": 19,
                "unbounded": 4,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
