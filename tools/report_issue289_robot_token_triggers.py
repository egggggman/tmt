"""Close only complete Robot-token triggers against the frozen 172-row ledger."""

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
PREVIOUS = DOCS / "ISSUE_289_CLASS_ARTIFACT_ANIMATION_CHECKPOINT.json"
READINESS_BEFORE = DOCS / "ISSUE_289_CLASS_ARTIFACT_ANIMATION_CALIBRATION_READINESS.json"
SNEAK = DOCS / "ISSUE_289_SNEAK_LEGALITY_SMOKE.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
OVERLAY = DOCS / "ISSUE_289_ROBOT_TOKEN_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_ROBOT_TOKEN_CALIBRATION_READINESS.json"
EXPECTED = {
    PREVIOUS: "01ccb63187e614cfeda064a8e1bd388f65df1210a745c9ee3345e76398ad815a",
    LEDGER: "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100",
    MANIFEST: "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac",
}
TARGETS = {
    "Mouser Foundry": "entry_or_leave",
    "Ravenous Robots": "artifact_cast",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reports() -> tuple[dict, dict]:
    for path, expected in EXPECTED.items():
        if sha(path) != expected:
            raise ValueError(f"frozen lineage changed: {path}")
    before = json.loads(PREVIOUS.read_text())
    previous_readiness = json.loads(READINESS_BEFORE.read_text())
    sneak = json.loads(SNEAK.read_text())
    if (
        len(before["rows"]) != 172
        or before["counts"]["priority"]["P1"] != 35
        or previous_readiness["important_blockers"] != 31
        or previous_readiness["unbounded_residual_important"] != 4
        or sneak["semantic_runtime_sha256"]
        != "2e140950578ddbfabf9fdb931a7edde800d9775c56c1e54bb438e09317c3ccf6"
        or sneak["row_delta"]
    ):
        raise ValueError("predecessor coverage or Sneak checkpoint changed")
    manifest = json.loads(MANIFEST.read_text())
    frozen: dict[str, dict[str, int]] = {}
    for deck in manifest["decks"]:
        path = ROOT / deck["source_path"]
        raw = path.read_bytes()
        crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        if deck["sha256"] not in {
            hashlib.sha256(raw).hexdigest(),
            hashlib.sha256(crlf).hexdigest(),
        }:
            raise ValueError("Baseline 005 deck differs from authenticated manifest")
        frozen[deck["deck_key"]] = {
            name: int(count)
            for count, name in (
                line.split(" ", 1)
                for line in path.read_text().splitlines()
                if line and line != "Deck"
            )
        }
    facts = load_facts(
        load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")),
        {name for deck in frozen.values() for name in deck},
    )
    interpreter = CardInterpreter()
    rows = [dict(row) for row in before["rows"]]
    closed = []
    for row in rows:
        if (
            row["card"] not in TARGETS
            or "Robot artifact creature token" not in row["oracle_fragment"]
        ):
            continue
        card, fragment = facts[row["card"]], row["oracle_fragment"]
        coverage = interpreter.token_semantic_coverage(card, fragment)
        if (
            row["deck"] != "casey_jones"
            or row["impact_priority"] != "P1"
            or row["execution_review"] != "gap"
            or frozen[row["deck"]][row["card"]] != int(row["copies"])
            or int(row["copies"]) != 4
            or interpreter.entry_leave_or_artifact_cast_token_context(card, fragment)
            != TARGETS[row["card"]]
            or coverage is None
            or not coverage.fully_supported
            or any(
                candidate == fragment for candidate, _ in interpreter.unsupported_fragments(card)
            )
        ):
            raise ValueError(f"Robot-token row is not complete: {row['card']}")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Complete Oracle-derived token creation from an authenticated self-entry/leave "
            "or controlled artifact-spell cast event. Trigger controller/source and stack "
            "survive source departure; priority, token entry and replay verified."
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if (
        len(closed) != 2
        or {item["card"] for item in closed} != set(TARGETS)
        or counts["priority"] != {"none": 139, "P1": 33}
        or counts["execution"] != {"covered": 33, "supported": 99, "annotation": 7, "gap": 33}
    ):
        raise ValueError("unexpected Robot-token row closure")
    remaining = [
        item
        for item in previous_readiness["ranked_important_rows"]
        if not any(
            item["deck"] == row["deck"]
            and item["card"] == row["card"]
            and item["oracle_fragment"] == row["oracle_fragment"]
            for row in closed
        )
    ]
    if len(remaining) != 33:
        raise ValueError("ranked residual does not match overlay")
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    overlay = {
        "schema": "issue289-robot-token-checkpoint-v1",
        "baseline_id": "OBL-BASELINE-005",
        "base_ledger_sha256": sha(LEDGER),
        "previous_checkpoint_sha256": sha(PREVIOUS),
        "sneak_checkpoint_sha256": sha(SNEAK),
        "before_runtime_sha256": sneak["semantic_runtime_sha256"],
        "semantic_runtime_sha256": runtime,
        "baseline_manifest_sha256": sha(MANIFEST),
        "frozen_deck_sha256": {deck["deck_key"]: deck["sha256"] for deck in manifest["decks"]},
        "historical_runtime_sha256": before["historical_runtime_sha256"],
        "gate": "BLOCKED",
        "control_authorized": False,
        "before_counts": before["counts"],
        "counts": counts,
        "closed_rows": closed,
        "rows": rows,
    }
    readiness = {
        "schema": "issue289-robot-token-calibration-readiness-v1",
        "baseline_id": "OBL-BASELINE-005",
        "checkpoint_overlay_sha256": None,
        "semantic_runtime_sha256": runtime,
        "original_ledger_sha256": sha(LEDGER),
        "critical_remaining": 0,
        "important_remaining": 33,
        "important_blockers": 29,
        "unbounded_residual_important": 4,
        "calibration_readiness": "BLOCKED",
        "reason": (
            "29 gameplay-important blockers still distort resource, combat and identity "
            "outcomes; four lower-exposure entries remain unbounded."
        ),
        "score_formula": previous_readiness["score_formula"],
        "score_scales": previous_readiness["score_scales"],
        "ranked_important_rows": remaining,
        "ranked_family_order": [
            "combat_damage_graveyard_recursion (Shark Shredder; 4 frozen copies in two decks)",
            "class_levels_and_counters (Leader's Talent; 4 copies, several linked levels/effects)",
            "combat_block_constraints (Rocksteady; 4 copies in B&R)",
            "artifact_token_cost_and_creation (Mutagen Man; 2 copies, variable X remains open)",
        ],
        "separate_unbounded_rows_preserved": [
            {key: item[key] for key in ("deck", "card", "oracle_fragment")}
            for item in remaining
            if not item["calibration_blocker"]
        ],
    }
    if (
        sum(item["calibration_blocker"] for item in remaining) != 29
        or len(readiness["separate_unbounded_rows_preserved"]) != 4
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
