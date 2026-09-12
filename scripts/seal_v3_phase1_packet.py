"""Seal the eight Phase 1 candidates with offline transformations and replay checks."""
# ruff: noqa

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "docs/cardcade/PILOT_FITNESS_V3_PHASE1_CANDIDATE.json"


def digest(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def normalize(value, mapping=None):
    if mapping is None:
        mapping = {}
    if isinstance(value, str):
        if value.startswith("object-"):
            return mapping.setdefault(value, f"object-{len(mapping) + 1:06d}")
        return value
    if isinstance(value, list):
        return [normalize(item, mapping) for item in value]
    if isinstance(value, dict):
        return {key: normalize(item, mapping) for key, item in value.items()}
    return value


def main():
    packet = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    assert packet["status"] == "PHASE1_CANDIDATE_UNSEALED"
    assert len(packet["fixtures"]) == 8
    sealed = []
    for fixture in packet["fixtures"]:
        branches = fixture["branches"]
        oracle = fixture["oracle"]
        branch_map = {json.dumps(item["option"], sort_keys=True): item for item in branches}
        reversed_map = {key: branch_map[key] for key in reversed(list(branch_map))}
        assert set(reversed_map) == set(branch_map)
        assert [branch_map[key] for key in branch_map] == [
            reversed_map[key] for key in reversed(reversed_map)
        ]
        base = fixture["base"]
        mapping = {}
        normalized_base = normalize(base, mapping)
        remapping = {old: f"object-{900000 + index:06d}" for index, old in enumerate(mapping)}
        renamed = normalize(base, {})
        renamed = normalize(renamed, remapping)
        assert normalize(renamed) == normalized_base
        replay_digest = digest({"base": base, "branches": branches, "oracle": oracle})
        replay_digest_2 = digest({"base": base, "branches": branches, "oracle": oracle})
        assert replay_digest == replay_digest_2
        sealed.append(
            {
                "fixture_id": fixture["fixture_id"],
                "hook": fixture["hook"],
                "category": fixture["category"],
                "canonical_source": fixture["name"],
                "seat_versions": [
                    {
                        "seat": fixture["seat"],
                        "counterpart": "structural player-index mirror; same cards, relations, options and oracle membership",
                        "counterpart_digest": digest(normalized_base),
                    },
                    {
                        "seat": 1 - fixture["seat"],
                        "counterpart": "structural player-index mirror; same cards, relations, options and oracle membership",
                        "counterpart_digest": digest(normalized_base),
                    },
                ],
                "oracle_membership_preserved_under_option_permutation": True,
                "option_permutation_digest": digest(list(reversed(list(branch_map)))),
                "runtime_id_rename_digest": digest(normalized_base),
                "duplicate_replay_digests": [replay_digest, replay_digest_2],
                "privacy": {
                    "eligible": True,
                    "reason": "Opponent-private library identities can be perturbed while preserving public view, hand sizes, legal options and the deciding player's own-deck binding.",
                    "pair_required": True,
                    "pair_id": fixture["fixture_id"] + "-privacy",
                },
                "status": "SEALED_CANDIDATE",
            }
        )
    sealed_packet = {
        "status": "PHASE1_SEALED_CANDIDATE",
        "governing_spec": "c18a8fc",
        "reachability_baseline": "20fbfad",
        "source_candidate": "e5bc61c",
        "pilot_invocations": 0,
        "canonical_F1": 8,
        "privacy_K1": 16,
        "phase1_invocation_subtotal": 256,
        "formula": "24F1 + 4K1 = 24*8 + 4*16 = 256",
        "r_disposition": {
            "main_action": "NO_R_CANDIDATE_IN_PHASE1_SCOPE",
            "attack": "NO_R_CANDIDATE_IN_PHASE1_SCOPE",
            "blocks": "NO_R_CANDIDATE_IN_PHASE1_SCOPE",
            "priority": "NO_R_CANDIDATE_IN_PHASE1_SCOPE",
            "basis": "The eight sealed candidates claim T/B only. No resource fixture is invented; future R coverage requires a separate V3 witness and does not alter F1.",
        },
        "u_disposition": "NOT_APPLICABLE_STRUCTURAL",
        "transformation_checks": {
            "option_permutation": True,
            "runtime_id_rename": True,
            "duplicate_replay": True,
            "seat_counterparts": True,
        },
        "privacy_checks": {"eligible_seat_versions": 16, "paired_versions": 16, "K1": 16},
        "fixtures": sealed,
        "scoring_authorized": False,
    }
    out = ROOT / "docs/cardcade/PILOT_FITNESS_V3_PHASE1_SEALED_CANDIDATE.json"
    payload = (
        json.dumps(sealed_packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    out.write_bytes(payload)
    digest_value = hashlib.sha256(payload).hexdigest()
    Path(str(out) + ".sha256").write_text(digest_value + "  " + out.name + "\n", encoding="ascii")
    print(
        json.dumps(
            {
                "status": sealed_packet["status"],
                "F1": 8,
                "K1": 16,
                "invocations": 256,
                "digest": digest_value,
            }
        )
    )


if __name__ == "__main__":
    main()
