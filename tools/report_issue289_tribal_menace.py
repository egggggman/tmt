"""Preserve the 172-row ledger while closing a controlled subtype keyword grant."""

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
PREVIOUS = DOCS / "ISSUE_289_DEATH_RETURN_CHECKPOINT.json"
BEFORE = DOCS / "ISSUE_289_DEATH_RETURN_CALIBRATION_READINESS.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
OVERLAY = DOCS / "ISSUE_289_TRIBAL_MENACE_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_TRIBAL_MENACE_CALIBRATION_READINESS.json"
SHA = {
    PREVIOUS: "7d2351fc3191064f85919ac11ea4709a266ae5fc6eb4199da5eb885964ee3706",
    BEFORE: "e3f48f35fbf3bc1ecbc02b566ec67d4bb1457a5c2c4b8e83f58ff584f30d1596",
    LEDGER: "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100",
    MANIFEST: "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac",
}
NAME = "Bebop, Warthog Warrior"
EFFECT = "Rhinos you control have menace."
KEYS = ("deck", "card", "oracle_fragment")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reports() -> tuple[dict, dict]:
    for path, expected in SHA.items():
        if sha(path) != expected:
            raise ValueError(f"frozen lineage changed: {path}")
    before, assessment = (json.loads(path.read_text()) for path in (PREVIOUS, BEFORE))
    if (
        len(before["rows"]) != 172
        or before["counts"]["priority"]["P1"] != 8
        or assessment["important_blockers"] != 4
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
        frozen[deck["deck_key"]] = dict(
            (name, int(count))
            for count, name in (
                line.split(" ", 1)
                for line in (ROOT / deck["source_path"]).read_text().splitlines()
                if line and line != "Deck"
            )
        )
    card = load_facts(load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")), {NAME})[NAME]
    interpreter = CardInterpreter()
    if (
        EFFECT not in interpreter.fragments(card)
        or interpreter.static_subtype_keyword_grant(card, EFFECT) is None
        or any(fragment == EFFECT for fragment, _reason in interpreter.unsupported_fragments(card))
    ):
        raise ValueError("complete frozen entry modifier remains unsupported")
    rows = [dict(row) for row in before["rows"]]
    closed = []
    for row in rows:
        if row["card"] != NAME or row["oracle_fragment"] != EFFECT:
            continue
        if (
            row["deck"] != "bebop_rocksteady"
            or frozen[row["deck"]][NAME] != int(row["copies"])
            or int(row["copies"]) != 2
            or row["impact_priority"] != "P1"
            or row["execution_review"] != "gap"
        ):
            raise ValueError("targeted entry pump and untap row differs from the frozen gap")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Complete Oracle-derived controlled-subtype menace grant; authoritative source, "
            "recipient controller and subtype, ability loss and source departure recalculate "
            "in the keyword layer. Block legality and deterministic replay verified."
        )
        closed.append({key: row[key] for key in KEYS})
    if Counter(tuple(row[k] for k in KEYS) for row in rows) != Counter(
        tuple(row[k] for k in KEYS) for row in before["rows"]
    ):
        raise ValueError("original 172 row identities changed")
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if (
        len(closed) != 1
        or counts["priority"] != {"none": 165, "P1": 7}
        or counts["execution"] != {"covered": 33, "supported": 125, "annotation": 7, "gap": 7}
    ):
        raise ValueError("unexpected coverage closure")
    exclusions = Counter(tuple(row[k] for k in KEYS) for row in closed)
    remaining = []
    for item in assessment["ranked_important_rows"]:
        key = tuple(item[k] for k in KEYS)
        if exclusions[key]:
            exclusions[key] -= 1
        else:
            remaining.append(item)
    if any(exclusions.values()) or len(remaining) != 7:
        raise ValueError("ranked residual differs from overlay")
    families: dict[str, dict] = {}
    for item in remaining:
        family = families.setdefault(
            item["mechanic"],
            {
                "mechanic": item["mechanic"],
                "entries": 0,
                "score": 0,
                "cards": set(),
                "decks": set(),
            },
        )
        family["entries"] += 1
        family["score"] = max(family["score"], item["priority_score"])
        family["cards"].add(item["card"])
        family["decks"].update(item["affected_decks"])
    ranked_families = [
        {**family, "cards": sorted(family["cards"]), "decks": sorted(family["decks"])}
        for family in sorted(families.values(), key=lambda row: (-row["score"], row["mechanic"]))
    ]
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    overlay = {
        "schema": "issue289-tribal-menace-checkpoint-v1",
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
        "closure_kind": "generic_controlled_subtype_keyword_grant",
        "new_semantic_families": ["continuous_controlled_subtype_keyword_grant"],
        "closed_rows": closed,
        "corrected_existing_coverage_rows": [],
        "rows": rows,
    }
    readiness = {
        "schema": "issue289-tribal-menace-calibration-readiness-v1",
        "baseline_id": "OBL-BASELINE-005",
        "checkpoint_overlay_sha256": None,
        "semantic_runtime_sha256": runtime,
        "original_ledger_sha256": sha(LEDGER),
        "critical_remaining": 0,
        "important_remaining": 7,
        "important_blockers": 4,
        "unbounded_residual_important": 3,
        "calibration_readiness": "BLOCKED",
        "reason": (
            "Four artifact-copy gap entries remain; three important effects are still unbounded."
        ),
        "pilot_execution_exposure": {
            "status": "FROZEN_DIAGNOSTIC_RECORDED",
            "diagnostic_path": str((DOCS / "ISSUE_289_TRIBAL_MENACE_SMOKE.json").relative_to(ROOT)),
            "interpretation": (
                "Frozen-deck diagnostics record cast opportunities, selections, entries and "
                "attacking use separately. Mechanic fixtures prove blocking legality even if "
                "natural attacks are absent; "
                "no balance inference."
            ),
        },
        "score_formula": assessment["score_formula"],
        "score_scales": assessment["score_scales"],
        "ranked_important_rows": remaining,
        "ranked_mechanic_families": ranked_families,
        "ranked_family_order": [family["mechanic"] for family in ranked_families],
        "separate_unbounded_rows_preserved": [
            {key: item[key] for key in KEYS}
            for item in remaining
            if not item["calibration_blocker"]
        ],
    }
    previous_unbounded = assessment["separate_unbounded_rows_preserved"]
    expected_unbounded = [item for item in previous_unbounded if item["card"] != NAME]
    if (
        sum(item["calibration_blocker"] for item in remaining) != 4
        or readiness["separate_unbounded_rows_preserved"] != expected_unbounded
    ):
        raise ValueError("residual calibration risk changed unexpectedly")
    readiness["original_unbounded_dispositions"] = [
        {
            **{key: item[key] for key in KEYS},
            "disposition": "implemented" if item["card"] == NAME else "still_unresolved",
            "evidence": (
                "Focused generic layer/combat fixtures and authenticated diagnostic replay"
                if item["card"] == NAME
                else "No complete execution or credible impact bound in this checkpoint"
            ),
        }
        for item in previous_unbounded
    ]
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
                "unbounded": 3,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
