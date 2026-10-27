"""Authenticate frozen R7-A and fail closed on its required semantic gaps.

This gate never executes a scheduled game.  It packages only read-only
candidate, runtime, coverage, and Baseline 003 control evidence.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round6c as prior  # noqa: E402
from historical_validation import (  # noqa: E402
    authenticated_bytes,
    authenticated_sha256,
    recorded_checkout_sha_matches,
)
from objective_balance_lab_semantic_identity import identity  # noqa: E402

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


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def snapshot() -> dict:
    """Authenticate archived readiness against its frozen runtime, without games.

    The live interpreter has since gained the formerly missing semantics. Do not
    regenerate an obsolete blocked gate using today's interpreter or edit the
    frozen R6-C driver (whose recorded hash is part of the original authority).
    """
    source = "897f8501ecddfdb0dd1cfd587dba8cf589087959"
    data = json.loads(authenticated_bytes(OUTPUT, ROOT, source))
    authenticated_bytes(REPORT, ROOT, source)
    assert data["authority_merge_commit"] == MERGED_AUTHORITY
    assert git("rev-parse", f"{MERGED_AUTHORITY}^{{tree}}").decode().strip() == (
        "b4b0082ee633acfa814292b74191a49984abf725"
    )
    for path, key in ((PLAN, "authority_plan_sha256"), (CLOSURE, "authority_closure_sha256")):
        assert authenticated_sha256(ROOT / path, ROOT, MERGED_AUTHORITY) == data[key]
    assert (
        authenticated_sha256(ROOT / CANDIDATE, ROOT, MERGED_AUTHORITY)
        == (data["candidate_sha256"])
        == CANDIDATE_SHA256
    )
    assert (
        git("rev-parse", f"{MERGED_AUTHORITY}:{CANDIDATE}").decode().strip()
        == (data["candidate_git_blob"])
        == CANDIDATE_BLOB
    )

    frozen = identity(MERGED_AUTHORITY)
    assert frozen == data["semantic_runtime_identity"]
    assert frozen["aggregate_semantic_runtime_sha256"] == data["semantic_runtime_sha256"]
    authority = json.loads(authenticated_bytes(prior.AUTHORITY, ROOT, source))
    driver = git("show", f"{MERGED_AUTHORITY}:tools/run_objective_balance_lab_round6c.py")
    assert prior.old.sha(driver) == authority["execution_driver_sha256"]
    assert authority["semantic_runtime_sha256"] == data["semantic_runtime_sha256"]
    manifest = json.loads(authenticated_bytes(prior.old.MANIFEST, ROOT, source))
    assert (
        authenticated_sha256(prior.old.MANIFEST, ROOT, source)
        == (data["baseline_manifest_sha256"])
        == authority["baseline_manifest_sha256"]
    )
    for row in manifest["decks"]:
        assert recorded_checkout_sha_matches(ROOT / row["source_path"], row["sha256"], ROOT)
    cards = prior.r1.catalog()
    parent = next(row for row in manifest["decks"] if row["deck_key"] == "krang")
    baseline = prior.r1.validate_deck(ROOT / parent["source_path"], cards)
    candidate = prior.r1.validate_deck(ROOT / CANDIDATE, cards)
    assert sum(candidate["cards"].values()) == 60
    assert (
        prior.r1.diff(baseline["cards"], candidate["cards"]) == data["exact_diff"] == EXPECTED_DIFF
    )
    schedule = prior.r1.schedule()
    assert (
        prior.r5.digest(schedule) == data["established_schedule_sha256"] == prior.old.SCHEDULE_SHA
    )
    assert len(schedule) == data["control_verified_games"] == 4500
    assert (
        len([row for row in schedule if "krang" in row["pair"]])
        == (data["candidate_schedule_games"])
        == 900
    )
    assert authenticated_sha256(prior.CONTROL, ROOT, source) == data["control_sha256"]
    control = prior.read(prior.CONTROL)
    prior.verify(control, prior.template(authority, manifest, schedule), schedule, complete=True)
    assert len(control["replays"]) == data["control_matched_replay_samples"] == 6
    assert data["status"] == "BLOCKED_SEMANTIC_EXECUTION"
    assert data["candidate_games_executed"] == data["candidate_replays_executed"] == 0
    assert not data["combined_validation_run"] and not data["promotion_authorized"]
    return data


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
