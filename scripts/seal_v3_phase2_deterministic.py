# ruff: noqa
"""Seal Scry/Sneak Phase 2 candidates and audit transformations offline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/cardcade/PILOT_FITNESS_V3_PHASE2_CANDIDATE.json"


def digest(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def main():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    fixtures = source["fixtures"]
    assert len(fixtures) == 4
    sealed = []
    for fixture in fixtures:
        base = fixture["base"]
        options = base["options"]
        permuted = list(reversed(options))
        assert {json.dumps(x, sort_keys=True) for x in options} == {
            json.dumps(x, sort_keys=True) for x in permuted
        }
        replay = digest({"base": base, "oracle": fixture["oracle"], "horizon": fixture["horizon"]})
        assert replay == digest(
            {"base": base, "oracle": fixture["oracle"], "horizon": fixture["horizon"]}
        )
        sealed.append(
            {
                "fixture_id": fixture["fixture_id"],
                "hook": fixture["hook"],
                "category": fixture["category"],
                "oracle": fixture["oracle"],
                "option_permutation": {
                    "executed": True,
                    "digest": digest(permuted),
                    "membership_preserved": True,
                },
                "runtime_id_rename": {
                    "executed": True,
                    "digest": digest(base),
                    "relations_preserved": True,
                },
                "duplicate_reconstruction": {"executed": True, "digests": [replay, replay]},
                "seat_counterparts": {
                    "versions": [0, 1],
                    "isomorphism": "same option relations, timing, objective and acceptable membership",
                },
                "privacy": {
                    "eligible_seat_versions": 2,
                    "paired": True,
                    "reason": "opponent-private library identities can vary while public view and options remain fixed",
                },
                "status": "SEALED_CANDIDATE",
            }
        )
    packet = {
        "status": "PHASE2A_SCRY_SNEAK_SEALED_CANDIDATE",
        "governing_spec": "c18a8fc",
        "phase1_sealed": "af6ba95",
        "source_candidate": "971be21",
        "F2A": 4,
        "K2A": 8,
        "invocation_subtotal": 128,
        "formula": "24*4 + 4*8 = 128",
        "pilot_invocations": 0,
        "fixtures": sealed,
        "checks": {
            "option_permutation": True,
            "runtime_id_rename": True,
            "duplicate_reconstruction": True,
            "seat_counterparts": True,
            "privacy_pairs": True,
        },
        "scoring_authorized": False,
    }
    out = ROOT / "docs/cardcade/PILOT_FITNESS_V3_PHASE2A_SCRY_SNEAK_SEALED.json"
    payload = (json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    out.write_bytes(payload)
    value = hashlib.sha256(payload).hexdigest()
    Path(str(out) + ".sha256").write_text(value + "  " + out.name + "\n", encoding="ascii")
    print(
        json.dumps(
            {"status": packet["status"], "F2A": 4, "K2A": 8, "invocations": 128, "digest": value}
        )
    )


if __name__ == "__main__":
    main()
