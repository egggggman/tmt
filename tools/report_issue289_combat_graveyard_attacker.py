"""Close only complete combat-damage graveyard attacker rows against frozen ledger."""

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
PREVIOUS = DOCS / "ISSUE_289_ROBOT_TOKEN_CHECKPOINT.json"
BEFORE = DOCS / "ISSUE_289_ROBOT_TOKEN_CALIBRATION_READINESS.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
OVERLAY = DOCS / "ISSUE_289_COMBAT_GRAVEYARD_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_COMBAT_GRAVEYARD_CALIBRATION_READINESS.json"
SHA = {
    PREVIOUS: "3604f80d3893b199d067a66b866d852adc5eb914c7b5244a0e92f5b7513ea360",
    BEFORE: "fdc07e196f0c568ae3601d093947d5a458fe4225523569ff16ca38758420e8cb",
    LEDGER: "56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100",
    MANIFEST: "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac",
}
NAME = "Shark Shredder, Killer Clone"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reports() -> tuple[dict, dict]:
    for path, expected in SHA.items():
        if sha(path) != expected:
            raise ValueError(f"frozen lineage changed: {path}")
    before, assessment = (json.loads(path.read_text()) for path in (PREVIOUS, BEFORE))
    if (
        len(before["rows"]) != 172
        or before["counts"]["priority"]["P1"] != 33
        or assessment["important_blockers"] != 29
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
        if row["card"] != NAME or "graveyard onto the battlefield" not in row["oracle_fragment"]:
            continue
        fragment = row["oracle_fragment"]
        if (
            row["deck"] not in {"shredder", "splinter"}
            or frozen[row["deck"]][NAME] != int(row["copies"]) != 2
            or row["impact_priority"] != "P1"
            or row["execution_review"] != "gap"
            or not interpreter.combat_damage_graveyard_attacker(card, fragment)
            or any(frag == fragment for frag, _ in interpreter.unsupported_fragments(card))
        ):
            raise ValueError("incomplete combat graveyard attacker closure")
        row["execution_review"] = "supported"
        row["impact_priority"] = "none"
        row["disposition"] = (
            "Full self combat-damage-to-player event, optional graveyard target chosen on stack "
            "after state-based actions, resolved into a tapped attacker under trigger controller. "
            "Invalid target fizzles; first-strike timing, source departure and replay verified."
        )
        closed.append({key: row[key] for key in ("deck", "card", "oracle_fragment")})
    counts = {
        "execution": dict(Counter(row["execution_review"] for row in rows)),
        "priority": dict(Counter(row["impact_priority"] for row in rows)),
    }
    if (
        len(closed) != 2
        or counts["priority"] != {"none": 141, "P1": 31}
        or counts["execution"] != {"covered": 33, "supported": 101, "annotation": 7, "gap": 31}
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
    if len(remaining) != 31:
        raise ValueError("ranked residual differs from overlay")
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    overlay = {
        "schema": "issue289-combat-graveyard-checkpoint-v1",
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
        "rows": rows,
    }
    readiness = {
        "schema": "issue289-combat-graveyard-calibration-readiness-v1",
        "baseline_id": "OBL-BASELINE-005",
        "checkpoint_overlay_sha256": None,
        "semantic_runtime_sha256": runtime,
        "original_ledger_sha256": sha(LEDGER),
        "critical_remaining": 0,
        "important_remaining": 31,
        "important_blockers": 27,
        "unbounded_residual_important": 4,
        "calibration_readiness": "BLOCKED",
        "reason": (
            "27 important gameplay blockers still distort class, combat and resource "
            "outcomes; four residual impacts remain unbounded."
        ),
        "score_formula": assessment["score_formula"],
        "score_scales": assessment["score_scales"],
        "ranked_important_rows": remaining,
        "ranked_family_order": [
            "class_levels_and_counters (Leader's Talent; 4 copies, linked levels/effects)",
            "combat_block_constraints (Rocksteady; 4 copies in B&R)",
            "artifact_token_cost_and_creation (Mutagen Man; 2 copies, variable X)",
        ],
        "separate_unbounded_rows_preserved": [
            {key: item[key] for key in ("deck", "card", "oracle_fragment")}
            for item in remaining
            if not item["calibration_blocker"]
        ],
    }
    if (
        sum(item["calibration_blocker"] for item in remaining) != 27
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
