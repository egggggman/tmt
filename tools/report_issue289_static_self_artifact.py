"""Preserve the 172-row ledger while closing a dynamic self artifact modifier."""

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
PREVIOUS = DOCS / "ISSUE_289_RESOURCE_ACTIVATION_CHECKPOINT.json"
BEFORE = DOCS / "ISSUE_289_RESOURCE_ACTIVATION_CALIBRATION_READINESS.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
OVERLAY = DOCS / "ISSUE_289_STATIC_SELF_ARTIFACT_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_STATIC_SELF_ARTIFACT_CALIBRATION_READINESS.json"
SHA = {
    PREVIOUS: "e6f1a09d798d7fc270a772b13917a7e760e1c8a817329f1cbc9fda39cd50ce07",
    BEFORE: "248c4d96c9b86fc8916653e53c62760b0973b96f7a77791e6ebe5f7cbc24a285",
    LEDGER: "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100",
    MANIFEST: "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac",
}
NAME = "Krang, Master Mind"
EFFECT = "Krang gets +1/+0 for each other artifact you control."
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
        or before["counts"]["priority"]["P1"] != 18
        or assessment["important_blockers"] != 14
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
        or interpreter.static_self_per_other_quality(card, EFFECT) != (1, 0, "Artifact")
        or any(fragment == EFFECT for fragment, _reason in interpreter.unsupported_fragments(card))
    ):
        raise ValueError("complete frozen static clause remains unsupported")
    rows = [dict(row) for row in before["rows"]]
    closed = []
    for row in rows:
        if row["card"] != NAME or row["oracle_fragment"] != EFFECT:
            continue
        if (
            row["deck"] != "krang"
            or frozen[row["deck"]][NAME] != int(row["copies"])
            or int(row["copies"]) != 2
            or row["impact_priority"] != "P1"
            or row["execution_review"] != "gap"
        ):
            raise ValueError("self artifact scaling row differs from the frozen gap")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Generic self P/T layer-7c modifier counts other currently controlled artifacts, "
            "including tokens and animated artifacts. Entry, departure, control changes, "
            "ability loss, source reincarnation, counters, combat and "
            "deterministic replay verified."
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
        or counts["priority"] != {"none": 155, "P1": 17}
        or counts["execution"] != {"covered": 33, "supported": 115, "annotation": 7, "gap": 17}
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
    if any(exclusions.values()) or len(remaining) != 17:
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
        "schema": "issue289-static-self-artifact-checkpoint-v1",
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
        "closure_kind": "generic_dynamic_self_pt_modifier",
        "new_semantic_families": ["static_self_per_other_quality"],
        "closed_rows": closed,
        "corrected_existing_coverage_rows": [],
        "rows": rows,
    }
    readiness = {
        "schema": "issue289-static-self-artifact-calibration-readiness-v1",
        "baseline_id": "OBL-BASELINE-005",
        "checkpoint_overlay_sha256": None,
        "semantic_runtime_sha256": runtime,
        "original_ledger_sha256": sha(LEDGER),
        "critical_remaining": 0,
        "important_remaining": 17,
        "important_blockers": 13,
        "unbounded_residual_important": 4,
        "calibration_readiness": "BLOCKED",
        "reason": (
            "Thirteen material resource, combat and token gaps remain; "
            "four important impacts are still unbounded."
        ),
        "pilot_execution_exposure": {
            "status": "UNPROVEN_FOR_THIS_MECHANIC",
            "diagnostic_path": str(
                (DOCS / "ISSUE_289_STATIC_SELF_ARTIFACT_SMOKE.json").relative_to(ROOT)
            ),
            "interpretation": (
                "A supported static effect changes games only if the pilot casts its source; "
                "use the companion deterministic smoke to distinguish offered casts from selection."
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
    if (
        sum(item["calibration_blocker"] for item in remaining) != 13
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
                "important": 17,
                "blockers": 13,
                "unbounded": 4,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
