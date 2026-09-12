"""Execute hash-bound canonical proof; refuse an unreconstructed full schedule."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict, fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import get_args, get_origin, get_type_hints

from tmnt_design_studio.engine07 import ActionOption
from tmnt_design_studio.pilot07 import AcceptancePilot, PassingPilot
from tmnt_design_studio.pilot_input_v2 import GameViewV2

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = "9fb8574"


def frozen(path):
    payload = subprocess.check_output(["git", "show", f"{AUTHORITY}:{path}"], cwd=ROOT)
    if (
        subprocess.check_output(["git", "hash-object", "--path=" + path, path], cwd=ROOT).strip()
        != subprocess.check_output(["git", "rev-parse", f"{AUTHORITY}:{path}"], cwd=ROOT).strip()
    ):
        raise RuntimeError(f"Frozen file changed: {path}")
    return payload


def digest(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def decode(cls, value):
    if value is None:
        return None
    if get_origin(cls) is tuple:
        args = get_args(cls)
        return tuple(
            decode(args[0] if len(args) == 2 and args[1] is Ellipsis else args[i], x)
            for i, x in enumerate(value)
        )
    if isinstance(cls, type) and issubclass(cls, Enum):
        return cls(value)
    if is_dataclass(cls):
        hints = get_type_hints(cls)
        result = cls(
            **{f.name: decode(hints[f.name], value[f.name]) for f in fields(cls) if f.init}
        )
        return result
    return value


def encode(value):
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return encode(asdict(value))
    if isinstance(value, (list, tuple)):
        return [encode(x) for x in value]
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    return value


def proof():
    for path in (
        "src/tmnt_design_studio/engine07.py",
        "src/tmnt_design_studio/pilot07.py",
        "src/tmnt_design_studio/pilot_input_v2.py",
    ):
        frozen(path)
    directory = "docs/cardcade/"
    integration = json.loads(frozen(directory + "PILOT_FITNESS_V3_GLOBAL_PRERUN_INTEGRATION.json"))
    for source in integration["sources"].values():
        if isinstance(source, dict):
            payload = frozen(directory + source["path"])
            if hashlib.sha256(payload).hexdigest() != source["sha256"]:
                raise RuntimeError("Sealed source hash mismatch")
    sealed = json.loads(frozen(directory + integration["sources"]["phase1"]["path"]))
    candidate = json.loads(frozen(directory + "PILOT_FITNESS_V3_PHASE1_CANDIDATE.json"))
    fixture = next(f for f in candidate["fixtures"] if f["fixture_id"] == "V3-P1-002")
    seal = next(f for f in sealed["fixtures"] if f["fixture_id"] == fixture["fixture_id"])
    replay_digest = digest({k: fixture[k] for k in ("base", "branches", "oracle")})
    if seal["duplicate_replay_digests"] != [replay_digest, replay_digest]:
        raise RuntimeError("Canonical observation/oracle does not match seal")
    view = decode(GameViewV2, fixture["base"]["view"])
    options = tuple(decode(ActionOption, x) for x in fixture["base"]["options"])
    if encode(view) != fixture["base"]["view"] or encode(options) != fixture["base"]["options"]:
        raise RuntimeError("Lossy input reconstruction")
    acceptable = [fixture["branches"][i]["option"] for i in fixture["oracle"]["guaranteed_win"]]
    calls = []
    for cls in (AcceptancePilot, PassingPilot):
        returned = cls().choose_attack(view, options)
        action = encode(returned)
        calls.append(
            {
                "pilot": cls.__name__,
                "hook": "choose_attack",
                "returned_action": action,
                "returned_repr": repr(returned),
                "legal_option_member": returned in options,
                "acceptable_set_member": action in acceptable,
            }
        )
    report = {
        "status": "CANONICAL_EXECUTION_PROOF_ONLY",
        "pre_run_authority": AUTHORITY,
        "failed_execution_attempt": "32e692b",
        "rejected_generic_state_attempt": "b353537",
        "governing_spec": "c18a8fc",
        "fixture_id": fixture["fixture_id"],
        "sealed_replay_digest": replay_digest,
        "observation": fixture["base"],
        "acceptable_set": acceptable,
        "actual_pilot_invocations": len(calls),
        "calls": calls,
        "full_schedule_executed": False,
        "limitation": "Sealed privacy metadata lacks authoritative paired hidden-state observations.",
    }
    out = ROOT / directory / "PILOT_FITNESS_V3_EXECUTION_PROOF.json"
    payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    out.write_bytes(payload)
    Path(str(out) + ".sha256").write_text(
        hashlib.sha256(payload).hexdigest() + "  " + out.name + "\n", encoding="ascii"
    )
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof", action="store_true")
    args = parser.parse_args()
    if not args.proof:
        parser.error(
            "Full schedule blocked: frozen seal scripts contain privacy eligibility metadata, "
            "but no authoritative paired hidden-state observations. Generic states and repeated "
            "canonical observations cannot substitute for the frozen privacy experiment."
        )
    proof()


if __name__ == "__main__":
    main()
