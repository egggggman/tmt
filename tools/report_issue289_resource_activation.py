"""Preserve the 172-row ledger while closing complete resource activations."""

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
PREVIOUS = DOCS / "ISSUE_289_ARTIFACT_ENTRY_COUNTER_CHECKPOINT.json"
BEFORE = DOCS / "ISSUE_289_ARTIFACT_ENTRY_COUNTER_CALIBRATION_READINESS.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
OVERLAY = DOCS / "ISSUE_289_RESOURCE_ACTIVATION_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_RESOURCE_ACTIVATION_CALIBRATION_READINESS.json"
SHA = {
    PREVIOUS: "9afabf78cae20911d26f025f17b75c97d069351bf6a42adc0e03bf1dbcd13ece",
    BEFORE: "a8aae5c20a2bb2b7bddeca5f29f2989a18e5fdec72cd0533c92e35cb56ff416f",
    LEDGER: "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100",
    MANIFEST: "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac",
}
NAME = "Ice Cream Kitty"
DRAW = "{2}, Sacrifice another creature or token: Draw a card. Activate only as a sorcery."
LIFE = "{2}, {T}, Sacrifice this creature: You gain 3 life."
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
        or before["counts"]["priority"]["P1"] != 23
        or assessment["important_blockers"] != 19
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
    if any(
        fragment not in interpreter.fragments(card)
        or not interpreter.activated_ability_semantics(card, fragment).coverage.fully_supported
        for fragment in (DRAW, LIFE)
    ):
        raise ValueError("one complete frozen Oracle ability remains unsupported")
    rows = [dict(row) for row in before["rows"]]
    closed = []
    for row in rows:
        if row["card"] != NAME or row["oracle_fragment"] not in (DRAW, LIFE):
            continue
        if (
            row["deck"] != "bebop_rocksteady"
            or frozen[row["deck"]][NAME] != int(row["copies"])
            or int(row["copies"]) != 3
            or row["impact_priority"] != "P1"
            or row["execution_review"] != "gap"
        ):
            raise ValueError("resource activation row differs from the frozen gap")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Generic complete activated ability: fixed mana, legal creature/token sacrifice "
            "cost and sorcery timing, or tap and self-sacrifice for three life. "
            "Paid costs, zone identities, stack independence, draw/life, priority, "
            "pilot choices, state-based actions and deterministic replay verified."
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
        len(closed) != 5
        or Counter(row["oracle_fragment"] for row in closed) != {DRAW: 3, LIFE: 2}
        or counts["priority"] != {"none": 154, "P1": 18}
        or counts["execution"] != {"covered": 33, "supported": 114, "annotation": 7, "gap": 18}
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
    if any(exclusions.values()) or len(remaining) != 18:
        raise ValueError("ranked residual differs from overlay")
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    overlay = {
        "schema": "issue289-resource-activation-checkpoint-v1",
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
        "closure_kind": "generic_activation_payment_and_effect_execution",
        "new_semantic_families": [
            "other_creature_or_token_sacrifice_draw",
            "food_creature_self_sacrifice_life",
        ],
        "closed_rows": closed,
        "corrected_existing_coverage_rows": [],
        "rows": rows,
    }
    readiness = {
        "schema": "issue289-resource-activation-calibration-readiness-v1",
        "baseline_id": "OBL-BASELINE-005",
        "checkpoint_overlay_sha256": None,
        "semantic_runtime_sha256": runtime,
        "original_ledger_sha256": sha(LEDGER),
        "critical_remaining": 0,
        "important_remaining": 18,
        "important_blockers": 14,
        "unbounded_residual_important": 4,
        "calibration_readiness": "BLOCKED",
        "reason": (
            "Fourteen material resource, combat and token gaps remain; "
            "four important impacts are still unbounded."
        ),
        "score_formula": assessment["score_formula"],
        "score_scales": assessment["score_scales"],
        "ranked_important_rows": remaining,
        "ranked_family_order": [
            "artifact_token_cost_and_creation (Mutagen Man; 2 frozen copies, variable X)",
            "remaining combat, resource, and token families ranked by preserved row scores",
        ],
        "separate_unbounded_rows_preserved": [
            {key: item[key] for key in KEYS}
            for item in remaining
            if not item["calibration_blocker"]
        ],
    }
    if (
        sum(item["calibration_blocker"] for item in remaining) != 14
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
                "important": 18,
                "blockers": 14,
                "unbounded": 4,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
