"""Execute Path A from sealed serialized observations, without constructing game states."""

# ruff: noqa: E501
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

from run_v3_scoring import AUTHORITY, ROOT, decode, digest, encode, frozen

from tmnt_design_studio.engine07 import ActionOption, ScryOption
from tmnt_design_studio.pilot07 import AcceptancePilot, PassingPilot
from tmnt_design_studio.pilot_input_v2 import GameViewV2, ScryViewV2

DIRECTORY = ROOT / "docs/cardcade"
STEM = "PILOT_FITNESS_V3_PATH_A_288"
PILOTS = (AcceptancePilot, PassingPilot)
VARIANTS = ("canonical", "option_permutation", "runtime_id_rename")
SEAT_FIELDS = {"observer_index", "player_index", "active_player", "owner", "controller"}
SIDE_ARRAYS = {"life", "hands", "battlefields", "hand_sizes", "library_sizes"}
HOOKS = {
    "main": "choose_main_action",
    "attack": "choose_attack",
    "blocks": "choose_blocks",
    "priority": "choose_priority",
    "scry": "choose_scry",
    "sneak": "choose_sneak",
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def pretty(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def save(path, payload):
    with path.open("xb") as stream:
        stream.write(payload)
    Path(str(path) + ".sha256").write_text(
        hashlib.sha256(payload).hexdigest() + "  " + path.name + "\n", encoding="ascii"
    )


def mirror(value, key=None):
    if isinstance(value, dict):
        return {k: mirror(v, k) for k, v in value.items()}
    if isinstance(value, list):
        rows = [mirror(v) for v in value]
        if key in SIDE_ARRAYS:
            require(len(rows) == 2, "Expected two player-indexed sides")
            rows.reverse()
        return rows
    if key in SEAT_FIELDS:
        require(type(value) is int and value in (0, 1), "Invalid player-index field")
        return 1 - value
    return value


def rename(value, mapping):
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [rename(v, mapping) for v in value]
    if isinstance(value, dict):
        return {k: rename(v, mapping) for k, v in value.items()}
    return value


def object_ids(value):
    if isinstance(value, str):
        return {value} if value.startswith("object-") else set()
    if isinstance(value, list):
        return set().union(*(object_ids(v) for v in value))
    if isinstance(value, dict):
        return set().union(*(object_ids(v) for v in value.values()))
    return set()


def normalize_p1(value, mapping=None):
    if mapping is None:
        mapping = {}
    if isinstance(value, str) and value.startswith("object-"):
        return mapping.setdefault(value, f"object-{len(mapping) + 1:06d}")
    if isinstance(value, list):
        return [normalize_p1(v, mapping) for v in value]
    if isinstance(value, dict):
        return {k: normalize_p1(v, mapping) for k, v in value.items()}
    return value


def phase2_digest(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def boundary_member(option, boundary):
    if boundary in (
        "empty_or_pass_only",
        "pass_only_no_counter_source",
        "no_unblocked_attacker_pass_only",
    ):
        return (
            option.get("kind") in ("pass", "pass_priority")
            or (option.get("kind") == "declare_attackers" and not option["attacker_ids"])
            or (option.get("kind") == "declare_blockers" and not option["blocks"])
        )
    if boundary == "empty_library_sole_choice":
        return not option["top_ids"] and not option["bottom_ids"]
    raise RuntimeError(f"Unrecognized sealed boundary: {boundary}")


def expected_actions(fixture):
    oracle = fixture["oracle"]
    options = fixture["base"]["options"]
    if fixture["category"] == "B":
        return [o for o in options if boundary_member(o, oracle["boundary"])]
    if "branches" in fixture:
        indices = oracle.get("acceptable", oracle.get("guaranteed_win"))
        require(indices is not None, "Missing sealed acceptable indices")
        return [fixture["branches"][i]["option"] for i in indices]
    return oracle["acceptable"]


def typed_inputs(observation):
    base = observation["base"]
    is_scry = observation["hook"] == "scry"
    view = decode(ScryViewV2 if is_scry else GameViewV2, base["view"])
    options = tuple(decode(ScryOption if is_scry else ActionOption, o) for o in base["options"])
    require(encode(view) == base["view"], "View round-trip mismatch")
    require(encode(options) == base["options"], "Option round-trip mismatch")
    return view, options


def construct_plan():
    sources = {}

    def read(path):
        payload = frozen(path)
        sources[path] = hashlib.sha256(payload).hexdigest()
        return payload

    paths = (
        subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", AUTHORITY, "src/tmnt_design_studio"], cwd=ROOT
        )
        .decode()
        .splitlines()
    )
    for path in paths:
        if path.endswith(".py"):
            read(path)
    directory = "docs/cardcade/"
    integration = json.loads(read(directory + "PILOT_FITNESS_V3_GLOBAL_PRERUN_INTEGRATION.json"))
    for row in integration["sources"].values():
        if isinstance(row, dict):
            require(
                hashlib.sha256(read(directory + row["path"])).hexdigest() == row["sha256"],
                "Integration source hash mismatch",
            )
    fixtures = []
    checks = []
    for phase, source_key, candidate_file in (
        (1, "phase1", "PILOT_FITNESS_V3_PHASE1_CANDIDATE.json"),
        (2, "phase2a", "PILOT_FITNESS_V3_PHASE2_CANDIDATE.json"),
    ):
        sealed = json.loads(read(directory + integration["sources"][source_key]["path"]))
        candidate = json.loads(read(directory + candidate_file))
        for seal in sealed["fixtures"]:
            f = next(f for f in candidate["fixtures"] if f["fixture_id"] == seal["fixture_id"])
            require(
                (f["hook"], f["category"]) == (seal["hook"], seal["category"]),
                "Fixture identity mismatch",
            )
            if phase == 1:
                replay = digest({k: f[k] for k in ("base", "branches", "oracle")})
                require(seal["duplicate_replay_digests"] == [replay, replay], "Replay mismatch")
                normalized = digest(normalize_p1(f["base"]))
                require(normalized == seal["runtime_id_rename_digest"], "ID digest mismatch")
                require(
                    all(s["counterpart_digest"] == normalized for s in seal["seat_versions"]),
                    "Seat digest mismatch",
                )
                keys = list(
                    dict.fromkeys(json.dumps(b["option"], sort_keys=True) for b in f["branches"])
                )
                require(
                    digest(list(reversed(keys))) == seal["option_permutation_digest"],
                    "Permutation digest mismatch",
                )
            else:
                replay = phase2_digest({k: f[k] for k in ("base", "oracle", "horizon")})
                require(
                    seal["duplicate_reconstruction"]["digests"] == [replay, replay],
                    "Replay mismatch",
                )
                require(
                    phase2_digest(f["base"]) == seal["runtime_id_rename"]["digest"],
                    "Base digest mismatch",
                )
                require(
                    phase2_digest(list(reversed(f["base"]["options"])))
                    == seal["option_permutation"]["digest"],
                    "Permutation digest mismatch",
                )
                require(f["oracle"] == seal["oracle"], "Oracle mismatch")
            expected = expected_actions(f)
            require(all(a in f["base"]["options"] for a in expected), "Oracle option absent")
            checks.append(
                {
                    "fixture_id": f["fixture_id"],
                    "replay_digest": replay,
                    "sealed_digests_verified": True,
                    "oracle": f["oracle"],
                    "option_count": len(f["base"]["options"]),
                }
            )
            fixtures.append(f)
    require(len(fixtures) == 12, "Fixture count mismatch")
    observations = []
    for f in fixtures:
        base = f["base"]
        source_seat = base["view"].get("observer_index", base["view"].get("player_index"))
        expected = expected_actions(f)
        issues = []
        if f["hook"] == "priority":
            issues.append(
                "Sealed observation is GameViewV2, not annotated PriorityViewV2; preserved verbatim."
            )
        if f["category"] == "B" and (not base["options"] or len(expected) != len(base["options"])):
            issues.append(
                "Sealed boundary label and option domain disagree; no options added or removed."
            )
        if f["fixture_id"] == "V3-P2-002" and f["oracle"].get("winner") is None:
            issues.append(
                "Sealed lethal objective has winner null; acceptable cast remains frozen."
            )
        for seat in (0, 1):
            for variant in VARIANTS:
                package = copy.deepcopy({"base": base, "expected_actions": expected})
                mirrored = seat != source_seat
                if mirrored:
                    package = mirror(package)
                    require(
                        mirror(package) == {"base": base, "expected_actions": expected},
                        "Seat mirror is not invertible",
                    )
                mapping = {}
                if variant == "runtime_id_rename":
                    mapping = {
                        old: f"object-{900000 + i:06d}"
                        for i, old in enumerate(sorted(object_ids(package)))
                    }
                    original = copy.deepcopy(package)
                    package = rename(package, mapping)
                    require(
                        rename(package, {v: k for k, v in mapping.items()}) == original,
                        "ID rename is not invertible",
                    )
                if variant == "option_permutation":
                    package["base"]["options"].reverse()
                observation = {
                    "fixture_id": f["fixture_id"],
                    "hook": f["hook"],
                    "category": f["category"],
                    "seat": seat,
                    "source_seat": source_seat,
                    "variant": variant,
                    "hook_method": HOOKS[f["hook"]],
                    "hook_kwargs": {"stage": "damage"} if f["hook"] == "main" else {},
                    "source_oracle": f["oracle"],
                    "source_horizon": f["horizon"],
                    "input_limitations": issues,
                    "id_mapping": mapping,
                    "mirrored": mirrored,
                    **package,
                }
                typed_inputs(observation)
                observation["observation_id"] = digest(observation)
                observations.append(observation)
    require(len(observations) == 72, "Observation count mismatch")
    return {
        "pre_run_authority": AUTHORITY,
        "specification": "c18a8fc",
        "path_a_authorization": "43bda04",
        "synchronized_main": "77b1228",
        "failed_attempts_preserved": ["32e692b", "b353537"],
        "proof_preserved": "37054b7",
        "privacy_defect": "4bb9ed61",
        "planned_hook_invocations": 288,
        "preflight_hook_invocations": 0,
        "privacy": "96 INCONCLUSIVE / UNEXECUTED; no addendum authorized",
        "source_git_blob_sha256": sources,
        "fixture_checks": checks,
        "execution_interpretation": {
            "seats": "Structural player-index mirror of sealed observations and option identities.",
            "permutation": "Reverse complete supplied option tuple, preserving membership.",
            "rename": "Bijection of sorted runtime IDs to object-900000 onwards; same map for oracle.",
            "seal_limits": "Seal digests certify canonical data/normalization; variant instances are reconstructed here, not claimed as preserved serialized states.",
            "main_stage": "damage for frozen Missile witness and main boundary; explicit hook argument absent from candidate JSON.",
            "boundary": "Compare returned supplied option to sealed empty/pass-only or empty-scry predicate; domain contradictions remain flagged.",
            "exceptions": "Every scheduled hook is invoked once; exceptions are recorded as no return, never repaired or retried.",
            "hq_decision": "PENDING; per-call comparisons do not certify fixture validity or suite fitness.",
        },
        "control_expectations_before_run": {
            "PassingPilot": "Pass/no attackers/no blocks/no sneak/all scry cards bottom; misses non-pass T/R obligations.",
            "AcceptancePilot": "Damage-stage Missile, maximal attacks/blocks, pass priority, first Sneak cast, keep scry order.",
        },
        "observations": observations,
    }


def invoke(observation, pilot_class):
    view, options = typed_inputs(observation)
    pilot = pilot_class()
    hook = getattr(pilot, observation["hook_method"])
    try:
        returned = hook(view, options, **observation["hook_kwargs"])
    except Exception as error:
        return {
            "outcome": "EXCEPTION",
            "returned_action": None,
            "exception": {"type": type(error).__name__, "message": str(error)},
            "legal_option_member": None,
            "returned_matches_expectation": False,
        }
    action = encode(returned)
    return {
        "outcome": "RETURNED",
        "returned_action": action,
        "returned_repr": repr(returned),
        "exception": None,
        "legal_option_member": returned in options,
        "returned_matches_expectation": action in observation["expected_actions"],
    }


def normalized_result(observation, result):
    action = result["returned_action"]
    if action is not None:
        action = rename(action, {v: k for k, v in observation["id_mapping"].items()})
        if observation["mirrored"]:
            action = mirror(action)
    return {"outcome": result["outcome"], "action": action, "exception": result["exception"]}


def execute(plan):
    plan_path = DIRECTORY / (STEM + "_EXECUTION_PLAN.json")
    require(plan_path.read_bytes() == pretty(plan), "Preflight plan changed before execution")
    paths = [
        DIRECTORY / (STEM + suffix) for suffix in ("_RAW.jsonl", "_RESULTS.json", "_REPORT.md")
    ]
    require(not any(p.exists() for p in paths), "Results already exist; refusing repeat execution")
    runner_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    require(
        not subprocess.check_output(["git", "diff", "HEAD", "--", "scripts", "src"], cwd=ROOT),
        "Runner/implementation must be committed before execution",
    )
    calls = []
    groups = defaultdict(list)
    invariants = defaultdict(list)
    with paths[0].open("x", encoding="utf-8", newline="\n") as stream:
        for observation in plan["observations"]:
            for replay in (1, 2):
                for pilot_class in PILOTS:
                    result = invoke(observation, pilot_class)
                    row = {
                        "call_index": len(calls) + 1,
                        "runner_commit": runner_sha,
                        "pilot": pilot_class.__name__,
                        "replay": replay,
                        "observation": observation,
                        **result,
                    }
                    stream.write(json.dumps(row, sort_keys=True) + "\n")
                    stream.flush()
                    calls.append(row)
                    groups[(observation["fixture_id"], pilot_class.__name__)].append(row)
                    invariants[(observation["fixture_id"], pilot_class.__name__)].append(
                        normalized_result(observation, result)
                    )
    require(len(calls) == 288, "Incomplete invocation count")
    summaries = []
    for (fixture_id, pilot), rows in groups.items():
        results = invariants[(fixture_id, pilot)]
        summaries.append(
            {
                "fixture_id": fixture_id,
                "pilot": pilot,
                "hook": rows[0]["observation"]["hook"],
                "category": rows[0]["observation"]["category"],
                "hook_invocations": len(rows),
                "returned": sum(r["outcome"] == "RETURNED" for r in rows),
                "exceptions": sum(r["outcome"] == "EXCEPTION" for r in rows),
                "expectation_matches": sum(r["returned_matches_expectation"] for r in rows),
                "normalized_outcomes_identical": all(r == results[0] for r in results),
                "input_limitations": rows[0]["observation"]["input_limitations"],
            }
        )
    raw_sha = hashlib.sha256(paths[0].read_bytes()).hexdigest()
    Path(str(paths[0]) + ".sha256").write_text(
        raw_sha + "  " + paths[0].name + "\n", encoding="ascii"
    )
    report = {
        "status": "EXECUTION_COMPLETE_HQ_FITNESS_DECISION_PENDING",
        "runner_commit": runner_sha,
        "pre_run_authority": AUTHORITY,
        "execution_plan_sha256": hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        "raw_sha256": raw_sha,
        "actual_hook_invocations": len(calls),
        "returned_decisions": sum(r["outcome"] == "RETURNED" for r in calls),
        "exceptions": sum(r["outcome"] == "EXCEPTION" for r in calls),
        "privacy_calls": 0,
        "privacy_status": "INCONCLUSIVE / UNEXECUTED (96)",
        "filtering_status": "INCONCLUSIVE / UNCHANGED",
        "calibration": "BLOCKED",
        "action_33": "NOT AUTHORIZED",
        "prototype_0_3": "NOT AUTHORIZED",
        "fixture_pilot_scores": summaries,
    }
    save(paths[1], pretty(report))
    md = "# Pilot Fitness V3: Path A 288-call execution\n\n"
    md += f"Runner commit: `{runner_sha}`. Pre-run: `9fb8574`; spec: `c18a8fc`; Path A: `43bda04`. "
    md += "Preserved invalid attempts: `32e692b` / `b353537`; proof: `37054b7`; defect: `4bb9ed61`.\n\n"
    md += (
        f"Actual hook invocations: **288**; returned decisions: **{report['returned_decisions']}**; "
        f"exceptions without a returned decision: **{report['exceptions']}**. "
        "Each scheduled hook was entered once. No retries, option additions, oracle edits, "
        "game-state construction, or privacy calls occurred.\n\n"
    )
    md += "The JSONL records every actual return or exception with complete input and expected actions. "
    md += "The committed execution plan records source hashes, frozen oracles, transformations, "
    md += "hook arguments and known input limitations before this run.\n\n"
    md += "| Fixture | Hook/category | Pilot | Calls | Returns | Exceptions | Matches | Stable normalized outcomes |\n"
    md += "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |\n"
    for s in summaries:
        md += (
            f"| {s['fixture_id']} | {s['hook']}/{s['category']} | {s['pilot']} | "
            f"{s['hook_invocations']} | {s['returned']} | {s['exceptions']} | "
            f"{s['expectation_matches']} | {s['normalized_outcomes_identical']} |\n"
        )
    md += "\n## Interpretation limits recorded before execution\n\n"
    md += "- Priority inputs are sealed GameViewV2 objects, not the annotated PriorityViewV2 type. "
    md += "They are passed unchanged to the actual priority hook; policy output does not certify this interface.\n"
    md += "- V3-P1-005 includes land-play options despite its empty/pass-only label. "
    md += "Only the frozen boundary predicate is compared; the input contradiction is unresolved.\n"
    md += "- V3-P2-004 supplies zero Sneak options despite its pass-only label. "
    md += "An exception is a no-return outcome, not an invented pass action.\n"
    md += "- V3-P2-002 records winner null despite its lethal objective. "
    md += "Matching the sealed cast does not independently demonstrate lethal play.\n"
    md += "- Seats/IDs are invertible structural transforms; option order is reversed. "
    md += "Their exact reconstructed instances and main-stage argument are explicit in the pre-call plan. "
    md += "Canonical seal digests are not misrepresented as hashes of newly reconstructed variants.\n\n"
    md += "No pooled Pilot Fitness PASS/FAIL is issued; HQ review is pending. "
    md += "Privacy 96 remains INCONCLUSIVE/unexecuted; filtering unchanged; calibration blocked. "
    md += "Action #33 and Prototype 0.3 remain unauthorized.\n"
    save(paths[2], md.encode())
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    plan = construct_plan()
    if args.execute:
        execute(plan)
    else:
        path = DIRECTORY / (STEM + "_EXECUTION_PLAN.json")
        save(path, pretty(plan))
        print("Preflight: 72 typed observations; 288 planned hooks; zero Pilot invocations.")


if __name__ == "__main__":
    main()
