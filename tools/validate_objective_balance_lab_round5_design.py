"""Fail-closed validation for the simulation-free Round 5 candidate design."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))

import run_objective_balance_lab_round1 as r1  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402

from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind  # noqa: E402
from tmnt_design_studio.engine07 import load_facts  # noqa: E402
from tmnt_design_studio.stage002 import load_catalog  # noqa: E402

TARGETS = {"shredder", "april_oneil", "krang"}
EXPECTED_IDS = {
    "OBL-R5-SHREDDER-A",
    "OBL-R5-SHREDDER-B",
    "OBL-R5-APRIL_ONEIL-A",
    "OBL-R5-KRANG-A",
    "OBL-R5-KRANG-B",
}
EXPECTED_ADDITIONS = {
    "Tunnel Rats",
    "April, Reporter of the Weird",
    "Utrom Scientists",
    "Mouser Mark III",
    "Donatello, Turtle Techie",
}


def _recorded_sha_matches(path: Path, recorded: str) -> bool:
    """Accept only identical LF or CRLF serialization of a preserved deck."""
    raw = path.read_bytes()
    versions = {
        raw,
        raw.replace(b"\r\n", b"\n"),
        raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"),
    }
    return recorded in {hashlib.sha256(value).hexdigest() for value in versions}


def _git_authored_sha(path: Path) -> str:
    """Candidate identity is the LF Git blob, independent of Windows checkout EOL."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _payable(mana_cost: str, allowed_color: str) -> bool:
    """Hybrid U/R is payable with U in Standard, unlike Commander identity."""
    for symbol in re.findall(r"\{([^}]+)\}", mana_cost):
        if symbol.isdigit() or symbol in {"X", "C"}:
            continue
        if symbol == allowed_color or allowed_color in symbol.split("/"):
            continue
        return False
    return True


def validate(*, allow_results: bool = False) -> dict[str, object]:
    plan = json.loads((OBL / "ROUND_5_CANDIDATE_PLAN.json").read_text(encoding="utf-8"))
    baseline = json.loads(
        (OBL / "baselines/OBL_BASELINE_002_MANIFEST.json").read_text(encoding="utf-8")
    )
    audit = json.loads((OBL / "BASELINE_002_METRIC_AUDIT.json").read_text(encoding="utf-8"))
    assert plan["state"] == "DESIGN_ONLY_NOT_SIMULATED"
    assert plan["parent_environment_id"] == baseline["environment_id"] == "OBL-BASELINE-002"
    assert baseline["environment_metrics"]["mean_matchup_balance_error"] == 0.189556
    assert audit["conclusion"] == "BASELINE_002_METADATA_CORRECTED"
    assert plan["semantic_runtime_sha256"] == baseline["semantic_runtime_sha256"]
    assert identity()["aggregate_semantic_runtime_sha256"] == plan["semantic_runtime_sha256"]
    assert plan["schedule_identity"] == baseline["schedule_identity"]
    assert plan["new_match_simulations"] == 0
    assert len(baseline["decks"]) == 10
    by_key = {row["deck_key"]: row for row in baseline["decks"]}
    assert len(by_key) == 10
    assert set(plan["frozen_decks"]) == set(by_key) - TARGETS

    cards = r1.catalog()
    snapshot_manifest = json.loads(r1.SNAPSHOT_MANIFEST.read_text(encoding="utf-8"))
    assert (
        hashlib.sha256(r1.SNAPSHOT.read_bytes()).hexdigest()
        == snapshot_manifest["snapshot"]["sha256"]
    )
    assert plan["card_snapshot"] == r1.SNAPSHOT.relative_to(ROOT).as_posix()
    assert (
        plan["reference_evidence"]
        == "docs/objective-balance-lab/COMBINED_003_RUNTIME_COMPATIBLE_EVIDENCE.json"
    )
    ledger = json.loads((OBL / "EXPERIMENT_LEDGER.json").read_text(encoding="utf-8"))
    prior_ids = {row["experiment_id"] for row in ledger["experiments"]}
    catalog = load_catalog(ROOT)
    interpreter = CardInterpreter()
    assert len(plan["candidates"]) == 5
    assert {row["experiment_id"] for row in plan["candidates"]} == EXPECTED_IDS
    if not allow_results:
        assert not EXPECTED_IDS & prior_ids
    assert plan["proposed_candidate_games"] == 900 * len(plan["candidates"])
    assert plan["maximum_if_six_candidates"] == 5400
    if not allow_results:
        assert all(
            not (OBL / name).exists()
            for name in ("ROUND_5_EVIDENCE.json", "ROUND_5_EVIDENCE.checkpoint.json")
        )
        assert not list(OBL.glob("ROUND_5_*RESULT*"))

    for baseline_row in baseline["decks"]:
        assert _recorded_sha_matches(ROOT / baseline_row["source_path"], baseline_row["sha256"])

    counts = Counter()
    seen_diffs: set[tuple[str, tuple[tuple[str, int], ...], tuple[tuple[str, int], ...]]] = set()
    added_names: set[str] = set()
    for row in plan["candidates"]:
        deck = row["deck_key"]
        assert deck in TARGETS
        counts[deck] += 1
        assert counts[deck] <= 2
        parent = by_key[deck]
        assert row["parent_path"] == parent["source_path"]
        assert row["parent_sha256"] == parent["sha256"]
        assert row["selection_status"] == "READY_FOR_ROUND_5_SIMULATION"
        assert row["prior_evidence_classification"] != "REPEATS_FALSIFIED_LEVER"
        assert row["candidate_path"].startswith("docs/objective-balance-lab/candidates/")
        candidate_path = ROOT / row["candidate_path"]
        assert candidate_path.is_file()
        candidate = r1.validate_deck(candidate_path, cards)
        assert _git_authored_sha(candidate_path) == row["candidate_sha256"]
        parent_validation = r1.validate_deck(ROOT / row["parent_path"], cards)
        actual_diff = r1.diff(parent_validation["cards"], candidate["cards"])
        assert actual_diff == {
            card: {
                "parent": parent_validation["cards"].get(card, 0),
                "candidate": candidate["cards"].get(card, 0),
            }
            for card in set(row["removals"]) | set(row["additions"])
        }
        for name, amount in row["removals"].items():
            assert (
                parent_validation["cards"].get(name, 0) - candidate["cards"].get(name, 0) == amount
            )
        for name, amount in row["additions"].items():
            assert (
                candidate["cards"].get(name, 0) - parent_validation["cards"].get(name, 0) == amount
            )
            added_names.add(name)
        assert sum(row["removals"].values()) == sum(row["additions"].values()) == 2
        assert sum(row["removals"].values()) + sum(row["additions"].values()) <= 4
        assert candidate["land_count"] == parent_validation["land_count"] == 22
        assert all(
            amount <= 4
            for name, amount in candidate["cards"].items()
            if name not in {"Island", "Swamp"}
        )
        allowed = "B" if deck == "shredder" else "U"
        assert all(_payable(cards[name]["mana_cost"], allowed) for name in candidate["cards"])
        key = (
            deck,
            tuple(sorted(row["removals"].items())),
            tuple(sorted(row["additions"].items())),
        )
        assert key not in seen_diffs
        seen_diffs.add(key)
        assert not any(
            old["experiment_id"] != row["experiment_id"]
            and (old.get("deck_key") == deck or old.get("deck") == r1.DISPLAY[deck])
            and old["exact_removals"] == row["removals"]
            and old["exact_additions"] == row["additions"]
            for old in ledger["experiments"]
        )

    assert added_names == EXPECTED_ADDITIONS
    screened = {row["card"]: row for row in plan["card_pre_screen"]}
    assert set(screened) == added_names
    facts = load_facts(catalog, added_names)
    for name in added_names:
        assert cards[name]["legalities"]["standard"] == "legal"
        assert screened[name]["standard_legal"] is True
        assert screened[name]["deck_payable"] is True
        assert screened[name]["rules_text"] == cards[name]["oracle_text"]
        assert screened[name]["mana_value"] == cards[name]["mana_value"]
        assert screened[name]["mana_cost"] == cards[name]["mana_cost"]
        assert facts[name].is_creature
        assert interpreter.cast_program(facts[name]).kind in {CastKind.CREATURE, CastKind.PERMANENT}
    assert (
        interpreter.etb_tap_stun_semantic_coverage(
            facts["Utrom Scientists"], interpreter.fragments(facts["Utrom Scientists"])[0]
        )
        is not None
    )
    assert any(
        interpreter.etb_artifact_draw_semantic_coverage(facts["Donatello, Turtle Techie"], fragment)
        is not None
        for fragment in interpreter.fragments(facts["Donatello, Turtle Techie"])
    )

    protected_paths = [row["source_path"] for row in baseline["decks"]]
    modified = subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD", "--", *protected_paths], cwd=ROOT, text=True
    )
    assert not modified.strip(), modified
    for document in ("ROUND_5_DIAGNOSTIC.md", "ROUND_5_CANDIDATE_PLAN.md"):
        path = OBL / document
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" in target:
                continue
            local = target.split("#", 1)[0].strip("<>")
            assert (OBL / local).is_file(), (document, target)
    return {
        "status": "PASS",
        "candidates": len(plan["candidates"]),
        "planned_games": 4500,
        "new_simulations": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-results", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(allow_results=args.allow_results), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
