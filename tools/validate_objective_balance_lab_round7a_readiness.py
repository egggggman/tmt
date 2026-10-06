"""Authenticate frozen R7-A and fail closed on its required semantic gaps.

This gate never executes a scheduled game.  It packages only read-only
candidate, runtime, coverage, and Baseline 003 control evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import run_objective_balance_lab_round6c as prior  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402

from tmnt_design_studio.card_interpreter07 import CardInterpreter  # noqa: E402
from tmnt_design_studio.engine07 import load_facts  # noqa: E402
from tmnt_design_studio.stage002 import _semantic_coverage, load_catalog  # noqa: E402

MERGED_AUTHORITY = "9f48bdbd6fc4800429217ca7897257180132302d"
PLAN = "docs/objective-balance-lab/ROUND_7_A_CANDIDATE_PLAN.md"
CLOSURE = "docs/objective-balance-lab/ROUND_6_DESIGN_STUDIO_CLOSURE.md"
CANDIDATE = "docs/objective-balance-lab/candidates/KRANG_OBL_R7_A.txt"
CANDIDATE_SHA256 = "2d598af2d05212ffb0f19fe5f315b7bf8f85501975155f394448b0a48fa81ab1"
CANDIDATE_BLOB = "3d224fecb398bb01d675837238e1196a07bdcb2d"
OUTPUT = ROOT / "docs/objective-balance-lab/ROUND_7_A_READINESS.json"
REPORT = ROOT / "docs/objective-balance-lab/ROUND_7_A_READINESS.md"
EXPECTED_DIFF = {
    "Does Machines": {"parent": 2, "candidate": 1},
    "Negate": {"parent": 3, "candidate": 2},
    "Ray Fillet, Man Ray": {"parent": 3, "candidate": 4},
    "Stockman, Mad Fly-entist": {"parent": 2, "candidate": 3},
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def snapshot() -> dict:
    # The signed Git commit and its exact blobs are available in this checkout.
    assert git("rev-parse", f"{MERGED_AUTHORITY}^{{tree}}").decode().strip() == (
        "b4b0082ee633acfa814292b74191a49984abf725"
    )
    for path in (PLAN, CLOSURE, CANDIDATE):
        assert (ROOT / path).read_bytes() == git("show", f"{MERGED_AUTHORITY}:{path}")
    assert sha(ROOT / CANDIDATE) == CANDIDATE_SHA256
    assert git("hash-object", CANDIDATE).decode().strip() == CANDIDATE_BLOB

    authority, manifest, schedule, paths = prior.preflight()
    control = prior.read(prior.CONTROL)
    prior.verify(control, prior.template(authority, manifest, schedule), schedule, complete=True)
    runtime = identity(MERGED_AUTHORITY)
    assert runtime["aggregate_semantic_runtime_sha256"] == control["semantic_runtime_sha256"]
    assert identity()["aggregate_semantic_runtime_sha256"] == control["semantic_runtime_sha256"]
    catalog = prior.r1.catalog()
    baseline = prior.r1.validate_deck(ROOT / paths["krang"], catalog)
    candidate = prior.r1.validate_deck(ROOT / CANDIDATE, catalog)
    assert sum(candidate["cards"].values()) == 60
    assert prior.r1.diff(baseline["cards"], candidate["cards"]) == EXPECTED_DIFF

    interpreter = CardInterpreter()
    added = ("Ray Fillet, Man Ray", "Stockman, Mad Fly-entist")
    facts = load_facts(load_catalog(ROOT), set(added))
    card_coverage = {}
    for name in added:
        card = facts[name]
        card_coverage[name] = {
            "oracle_id": card.oracle_id,
            "oracle_text": card.oracle_text,
            "cast_kind": interpreter.cast_program(card).kind.value,
            "fragments": [
                {
                    "oracle_fragment": fragment,
                    **_semantic_coverage(interpreter, card, fragment, ()),
                }
                for fragment in interpreter.fragments(card)
            ],
        }
        assert card_coverage[name]["cast_kind"] == "creature"

    ray = next(
        row
        for row in card_coverage[added[0]]["fragments"]
        if row["oracle_fragment"].startswith("When Ray Fillet enters")
    )
    stockman = next(
        row
        for row in card_coverage[added[1]]["fragments"]
        if row["oracle_fragment"].startswith("Islandcycling")
    )
    assert ray["family"] == "create_token" and ray["payload_executable"]
    assert not ray["followup_executable"] and (
        "token_activated_ability_not_implemented" in ray["limitations"]
    )
    assert stockman["family"] == "activated_ability"
    assert not stockman["fully_supported"] and (
        "activation_nested_context_not_implemented" in stockman["limitations"]
    )
    assert len(schedule) == 4500
    assert len([row for row in schedule if "krang" in row["pair"]]) == 900

    return {
        "schema": "obl-r7a-readiness-v1",
        "experiment_id": "OBL-R7-KRANG-A",
        "status": "BLOCKED_SEMANTIC_EXECUTION",
        "handoff": "ENGINE_SEMANTICS_REQUIRED",
        "authority_pr": 268,
        "authority_merge_commit": MERGED_AUTHORITY,
        "authority_plan_path": PLAN,
        "authority_plan_sha256": sha(ROOT / PLAN),
        "authority_closure_path": CLOSURE,
        "authority_closure_sha256": sha(ROOT / CLOSURE),
        "candidate_path": CANDIDATE,
        "candidate_sha256": CANDIDATE_SHA256,
        "candidate_git_blob": CANDIDATE_BLOB,
        "exact_diff": EXPECTED_DIFF,
        "baseline_manifest_sha256": sha(prior.old.MANIFEST),
        "baseline_decks_changed": False,
        "semantic_runtime_sha256": runtime["aggregate_semantic_runtime_sha256"],
        "semantic_runtime_identity": runtime,
        "control_id": prior.CONTROL_ID,
        "control_path": prior.CONTROL.relative_to(ROOT).as_posix(),
        "control_sha256": sha(prior.CONTROL),
        "control_verified_games": 4500,
        "control_matched_replay_samples": 6,
        "control_runtime_errors": 0,
        "control_runtime_compatible": True,
        "established_schedule_sha256": prior.old.SCHEDULE_SHA,
        "candidate_schedule_games": 900,
        "card_coverage": card_coverage,
        "required_gaps": [
            {
                "card": added[0],
                "oracle_fragment": ray["oracle_fragment"],
                "supported": "ETB Mutagen token creation",
                "missing": "Mutagen token's {1}, {T}, sacrifice: +1/+1 counter activation",
                "reason": "token_activated_ability_not_implemented",
                "hypothesis_dependency": (
                    "The token's counter is a printed route to the counter "
                    "that Ray Fillet can remove to draw a card."
                ),
            },
            {
                "card": added[1],
                "oracle_fragment": stockman["oracle_fragment"],
                "supported": "Flying and ETB draw-then-discard",
                "missing": "Islandcycling from hand",
                "reason": "activation_nested_context_not_implemented",
                "hypothesis_dependency": (
                    "The extra Stockman copy changes access to its printed "
                    "land-selection mode, which the pilot cannot execute."
                ),
            },
        ],
        "retained_baseline_limits": [
            "Negate cannot counter a noncreature spell in this runtime.",
            "Does Machines level-3 activation and its associated effect are incomplete.",
        ],
        "diagnostics": ["raphael", "shredder"],
        "anti_polarization_sentinels": ["april_oneil", "leonardo"],
        "candidate_games_executed": 0,
        "candidate_replays_executed": 0,
        "combined_validation_run": False,
        "promotion_authorized": False,
        "experimental_results_merged": False,
        "next_gate": (
            "Implement and validate the general missing semantics, then authenticate the "
            "new runtime and refresh unchanged Baseline 003 before R7-A isolated execution."
        ),
    }


def render(data: dict) -> str:
    gaps = data["required_gaps"]
    return "\n".join(
        [
            "# Krang R7-A — semantic readiness",
            "",
            "**Status: BLOCKED_SEMANTIC_EXECUTION.** No R7-A games or replays were run.",
            "",
            (
                "Merged [Design Studio authority](https://github.com/egggggman/tmt/pull/268) "
                f"at `{MERGED_AUTHORITY}` freezes `−1 Does Machines / −1 Negate / "
                "+1 Ray Fillet, Man Ray / +1 Stockman, Mad Fly-entist`. "
                f"Candidate SHA-256: `{CANDIDATE_SHA256}`; Git blob: `{CANDIDATE_BLOB}`. "
                "The list is 60 cards and is the exact four-card-count diff from Baseline 003."
            ),
            "",
            (
                "The existing Aura-runtime Baseline 003 control "
                f"`{data['control_id']}` is compatible with runtime "
                f"`{data['semantic_runtime_sha256']}`. All 4,500 preserved control "
                "records and six deterministic replay samples authenticated. "
                "The 900-game candidate schedule is the established "
                f"`{data['established_schedule_sha256']}` schedule; "
                "it has not been executed for R7-A."
            ),
            "",
            "| Added card | Executable | Missing printed mode | Consequence for this test |",
            "|---|---|---|---|",
            *[
                "| {card} | {supported} | {missing} | {hypothesis_dependency} |".format(**row)
                for row in gaps
            ],
            "",
            (
                "Stockman's ETB filter and Ray Fillet's flying/body, Mutagen creation, "
                "and counter-removal draw are represented. The Mutagen's activated "
                "counter ability and Islandcycling are not. Their increased copy "
                "counts make the missing modes asymmetric against the existing "
                "control. The inherited baseline also has unsupported Negate and "
                "Does Machines level-3 behavior; neither is credited as simulated value."
            ),
            "",
            (
                "The merged [R7-A plan](ROUND_7_A_CANDIDATE_PLAN.md) directs Cardcade "
                "to fail closed when a required rule is unavailable. No deck edits, "
                "fresh control games, candidate games, combined validation, or "
                "promotion occurred."
            ),
            "",
            (
                "**NEXT MOVE → 🕹️ Cardcade engine/readiness:** implement the missing "
                "generic token activation and hand-zone Islandcycling semantics, "
                "validate them, then refresh all 4,500 unchanged Baseline 003 control "
                "games under the new runtime before the frozen 900-game R7-A "
                "isolated test. Return completed test evidence to 🧪 Design Studio "
                "for interpretation."
            ),
            "",
            "[Machine-readable identity, coverage, and control checks](ROUND_7_A_READINESS.json).",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = snapshot()
    products = {
        OUTPUT: json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        REPORT: render(data),
    }
    for path, content in products.items():
        if args.write:
            path.write_text(content, encoding="utf-8")
        else:
            assert path.read_text(encoding="utf-8") == content, path
    print("R7_A_BLOCKED_SEMANTIC_EXECUTION_VERIFIED")


if __name__ == "__main__":
    main()
