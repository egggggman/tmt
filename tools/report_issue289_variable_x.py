"""Preserve the 172-row ledger while closing complete variable-X entry tokens."""

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
PREVIOUS = DOCS / "ISSUE_289_ARTIFACT_ANIMATION_CHECKPOINT.json"
BEFORE = DOCS / "ISSUE_289_ARTIFACT_ANIMATION_CALIBRATION_READINESS.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
OVERLAY = DOCS / "ISSUE_289_VARIABLE_X_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_VARIABLE_X_CALIBRATION_READINESS.json"
SHA = {
    PREVIOUS: "7f81c12832cbc07e981578651afff41978429a004e8407878450d7c7e8a139af",
    BEFORE: "289dab6ddcd34bfd06faffb0e138db0fab53fc583ec80f186ccb973d2ff835b0",
    LEDGER: "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100",
    MANIFEST: "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac",
}
NAME = "Mutagen Man, Living Ooze"
EFFECT = (
    "When Mutagen Man enters, create X Mutagen tokens. (They're artifacts with "
    '"{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. '
    'Activate only as a sorcery.")'
)
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
        or before["counts"]["priority"]["P1"] != 14
        or assessment["important_blockers"] != 10
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
        or interpreter.x_entry_token_program(card, EFFECT) is None
        or not interpreter.token_semantic_coverage(card, EFFECT).fully_supported
        or any(fragment == EFFECT for fragment, _reason in interpreter.unsupported_fragments(card))
    ):
        raise ValueError("complete frozen targeted activation remains unsupported")
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
            raise ValueError("artifact animation row differs from the frozen gap")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Variable-X cost and self-entry token trigger: chosen X is paid, preserved across "
            "spell resolution, and creates exactly X printed artifact tokens after priority; "
            "zero, counter, source departure, state-based actions and replay verified."
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
        or counts["priority"] != {"none": 159, "P1": 13}
        or counts["execution"] != {"covered": 33, "supported": 119, "annotation": 7, "gap": 13}
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
    if any(exclusions.values()) or len(remaining) != 13:
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
        "schema": "issue289-variable-x-checkpoint-v1",
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
        "closure_kind": "generic_variable_x_spell_and_entry_tokens",
        "new_semantic_families": ["variable_x_spell_payment", "x_entry_token_trigger"],
        "closed_rows": closed,
        "corrected_existing_coverage_rows": [],
        "rows": rows,
    }
    readiness = {
        "schema": "issue289-variable-x-calibration-readiness-v1",
        "baseline_id": "OBL-BASELINE-005",
        "checkpoint_overlay_sha256": None,
        "semantic_runtime_sha256": runtime,
        "original_ledger_sha256": sha(LEDGER),
        "critical_remaining": 0,
        "important_remaining": 13,
        "important_blockers": 9,
        "unbounded_residual_important": 4,
        "calibration_readiness": "BLOCKED",
        "reason": (
            "Nine material resource, combat and token gaps remain; "
            "four important impacts are still unbounded."
        ),
        "pilot_execution_exposure": {
            "status": "UNPROVEN_FOR_THIS_MECHANIC",
            "diagnostic_path": str((DOCS / "ISSUE_289_VARIABLE_X_SMOKE.json").relative_to(ROOT)),
            "interpretation": (
                "A legal X opportunity does not imply pilot selection; compare offered X values, "
                "announcements, payments, resolved spells and created tokens."
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
        sum(item["calibration_blocker"] for item in remaining) != 9
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
                "unbounded": 4,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
