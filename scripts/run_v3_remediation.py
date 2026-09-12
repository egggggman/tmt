"""Prepare and execute only the four HQ-authorized remediation fixtures."""

# ruff: noqa: E501
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from collections import defaultdict

import build_v3_phase1_fitness_packet as p1
import build_v3_phase2_candidate as p2
import run_v3_path_a_scoring as original
from run_v3_scoring import decode, digest, encode

from tmnt_design_studio.engine07 import ActionOption
from tmnt_design_studio.pilot_input_v2 import PriorityViewV2

DIRECTORY = original.DIRECTORY
STEM = "PILOT_FITNESS_V3_REMEDIATION_96"
IDS = ("V3-P1-004", "V3-P1-005", "V3-P2-001", "V3-P2-004")


def typed_inputs(observation):
    if observation["hook"] != "priority":
        return original.typed_inputs(observation)
    base = observation["base"]
    view = decode(PriorityViewV2, base["view"])
    options = tuple(decode(ActionOption, o) for o in base["options"])
    assert encode(view) == base["view"] and encode(options) == base["options"]
    return view, options


def mirror(value, key=None):
    # Priority adds scalar priority_player and a sequence of passing seat IDs.
    if key == "priority_player":
        return 1 - value
    if key == "consecutive_passes":
        return [1 - seat for seat in value]
    if isinstance(value, dict):
        return {k: mirror(v, k) for k, v in value.items()}
    if isinstance(value, list):
        rows = [mirror(v) for v in value]
        if key in original.SIDE_ARRAYS:
            rows.reverse()
        return rows
    return original.mirror(value, key)


def fixtures():
    rows = []
    for fid, hook, category, record in (
        (IDS[0], "priority", "T", p1.priority_t()),
        (IDS[1], "main", "B", p1.boundary("main_action", 0, 3010)),
    ):
        name, seat, base, branches, oracle = record
        rows.append(
            dict(
                fixture_id=fid,
                hook=hook,
                category=category,
                name=name,
                seat=seat,
                base=base,
                branches=branches,
                oracle=oracle,
                horizon="immediate engine resolution; Priority fully drained",
            )
        )
    rows.extend((p2.scry_fixture(), p2.sneak_boundary()))
    return rows


def construct_plan():
    rows = fixtures()
    assert rows == fixtures(), "Construction must be deterministic"
    observations = []
    for f in rows:
        expected = original.expected_actions(f)
        assert expected and all(o in f["base"]["options"] for o in expected)
        if f["category"] == "B":
            assert expected == f["base"]["options"]
        for seat in (0, 1):
            for variant in original.VARIANTS:
                source = dict(base=f["base"], expected_actions=expected)
                package = copy.deepcopy(source)
                if seat:
                    package = mirror(package)
                    assert mirror(package) == source
                mapping = {}
                if variant == "runtime_id_rename":
                    mapping = {
                        old: f"object-{900000 + i:06d}"
                        for i, old in enumerate(sorted(original.object_ids(package)))
                    }
                    before = copy.deepcopy(package)
                    package = original.rename(package, mapping)
                    assert original.rename(package, {v: k for k, v in mapping.items()}) == before
                if variant == "option_permutation":
                    package["base"]["options"].reverse()
                observation = dict(
                    fixture_id=f["fixture_id"],
                    hook=f["hook"],
                    category=f["category"],
                    seat=seat,
                    source_seat=0,
                    variant=variant,
                    mirrored=bool(seat),
                    id_mapping=mapping,
                    hook_method=original.HOOKS[f["hook"]],
                    hook_kwargs={"stage": "damage"} if f["hook"] == "main" else {},
                    **package,
                )
                typed_inputs(observation)
                observation["observation_id"] = digest(observation)
                observations.append(observation)
    return dict(
        preserved_commits=["d880c36", "decb9eb2"],
        fixtures=rows,
        planned_hook_invocations=96,
        preflight_hook_invocations=0,
        observations=observations,
        calibration="BLOCKED",
        hq_decision="PENDING",
        action_33="NOT AUTHORIZED",
        source_sha256={
            p: hashlib.sha256((original.ROOT / p).read_bytes()).hexdigest()
            for p in (
                "src/tmnt_design_studio/pilot07.py",
                "scripts/build_v3_phase1_fitness_packet.py",
                "scripts/build_v3_phase2_candidate.py",
                "scripts/run_v3_remediation.py",
                "scripts/run_v3_path_a_scoring.py",
                "scripts/run_v3_scoring.py",
                "src/tmnt_design_studio/engine07.py",
                "src/tmnt_design_studio/pilot_input_v2.py",
            )
        },
    )


def execute(plan):
    plan_relative = "docs/cardcade/" + STEM + "_EXECUTION_PLAN.json"
    assert subprocess.check_output(
        ["git", "show", "HEAD:" + plan_relative], cwd=original.ROOT
    ) == original.pretty(plan), "Execution plan must be committed unchanged"
    assert len(plan["observations"]) == 24
    assert {o["fixture_id"] for o in plan["observations"]} == set(IDS)
    for p, sha in plan["source_sha256"].items():
        assert hashlib.sha256((original.ROOT / p).read_bytes()).hexdigest() == sha
    assert not subprocess.check_output(
        ["git", "diff", "HEAD", "--", "scripts", "src", "tests"], cwd=original.ROOT
    )
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=original.ROOT).decode().strip()
    paths = [
        DIRECTORY / (STEM + suffix) for suffix in ("_RAW.jsonl", "_RESULTS.json", "_REPORT.md")
    ]
    assert not any(p.exists() for p in paths), "Refusing repeat execution"
    calls = []
    groups = defaultdict(list)
    with paths[0].open("x", encoding="utf-8", newline="\n") as stream:
        for o in plan["observations"]:
            for replay in (1, 2):
                for cls in original.PILOTS:
                    view, options = typed_inputs(o)
                    try:
                        returned = getattr(cls(), o["hook_method"])(
                            view, options, **o["hook_kwargs"]
                        )
                        result = dict(
                            outcome="RETURNED",
                            returned_action=encode(returned),
                            legal_option_member=returned in options,
                            exception=None,
                            returned_matches_expectation=encode(returned) in o["expected_actions"],
                        )
                    except Exception as error:
                        result = dict(
                            outcome="EXCEPTION",
                            returned_action=None,
                            legal_option_member=None,
                            returned_matches_expectation=False,
                            exception=dict(type=type(error).__name__, message=str(error)),
                        )
                    row = dict(
                        call_index=len(calls) + 1,
                        runner_commit=sha,
                        pilot=cls.__name__,
                        replay=replay,
                        observation=o,
                        **result,
                    )
                    stream.write(json.dumps(row, sort_keys=True) + "\n")
                    stream.flush()
                    calls.append(row)
                    groups[(o["fixture_id"], cls.__name__)].append(row)
    assert len(calls) == 96
    summaries = []
    for (fid, pilot), rows in groups.items():
        normalized = [original.normalized_result(r["observation"], r) for r in rows]
        summaries.append(
            dict(
                fixture_id=fid,
                pilot=pilot,
                calls=len(rows),
                returns=sum(r["outcome"] == "RETURNED" for r in rows),
                exceptions=sum(r["outcome"] == "EXCEPTION" for r in rows),
                legal_returns=sum(r["legal_option_member"] is True for r in rows),
                matches=sum(r["returned_matches_expectation"] for r in rows),
                stable=all(r == normalized[0] for r in normalized),
            )
        )
    raw_sha = hashlib.sha256(paths[0].read_bytes()).hexdigest()
    original.save(
        paths[1],
        original.pretty(
            dict(
                runner_commit=sha,
                actual_hook_invocations=96,
                execution_plan_sha256=hashlib.sha256(original.pretty(plan)).hexdigest(),
                raw_sha256=raw_sha,
                summaries=summaries,
                calibration="BLOCKED",
                hq_decision="PENDING",
                privacy_calls=0,
                filtering="UNCHANGED",
                action_33="NOT AUTHORIZED",
                prototype_0_2="FROZEN",
                prototype_0_3="NOT AUTHORIZED",
            )
        ),
    )
    paths[0].with_suffix(paths[0].suffix + ".sha256").write_text(
        raw_sha + "  " + paths[0].name + "\n", encoding="ascii"
    )
    report = f"# Four-fixture remediation candidate\n\nImplementation: `{sha}`. Original evidence d880c36 and diagnosis decb9eb2 preserved.\n\n"
    report += "96 actual hooks: four fixtures, two seats, three variants, two replays, two Pilots. No clean competencies rerun.\n\n"
    report += "Priority uses PriorityViewV2; AcceptancePilot takes a supplied opposing-spell counter; PassingPilot remains pass-only. Scry policy is unchanged; all four creature-top actions are acceptable. Main has an empty hand and only pass. Sneak spends its sole cast, drains Priority, then offers a genuine pass in declare_blockers; the old no-unblocked-attacker label is replaced.\n\n"
    report += "| Fixture | Pilot | Calls | Returns | Exceptions | Legal | Matches | Stable |\n|---|---|---:|---:|---:|---:|---:|---|\n"
    for s in summaries:
        report += (
            "| "
            + " | ".join(
                str(s[k])
                for k in (
                    "fixture_id",
                    "pilot",
                    "calls",
                    "returns",
                    "exceptions",
                    "legal_returns",
                    "matches",
                    "stable",
                )
            )
            + " |\n"
        )
    report += "\nHQ decision pending; calibration BLOCKED; decks / Prototype 0.2 FROZEN; Action #33 / Prototype 0.3 NOT AUTHORIZED. Privacy and filtering unchanged. This affected-fixture result does not replace the original run or establish broader Pilot competence.\n"
    original.save(paths[2], report.encode())
    print(json.dumps(summaries, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    path = DIRECTORY / (STEM + "_EXECUTION_PLAN.json")
    if args.execute:
        plan = json.loads(path.read_text())
        assert path.read_bytes() == original.pretty(plan)
        execute(plan)
    else:
        original.save(path, original.pretty(construct_plan()))
        print("24 typed observations; 96 planned hooks; zero Pilot invocations")


if __name__ == "__main__":
    main()
