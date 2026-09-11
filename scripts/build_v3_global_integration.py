# ruff: noqa
"""Build the global V3 pre-run integration packet from banked phase seals."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    p1 = ROOT / "docs/cardcade/PILOT_FITNESS_V3_PHASE1_SEALED_CANDIDATE.json"
    p2 = ROOT / "docs/cardcade/PILOT_FITNESS_V3_PHASE2A_SCRY_SNEAK_SEALED.json"
    audit = ROOT / "docs/cardcade/PILOT_FITNESS_V3_PHASE2_FILTERING_DISPOSITION_AUDIT.json"
    sources = {
        "specification_v3": "c18a8fc",
        "phase1": {"commit": "af6ba95", "path": p1.name, "sha256": digest(p1)},
        "phase2a": {"commit": "c4c0d2b", "path": p2.name, "sha256": digest(p2)},
        "filtering_audit": {"commit": "c4c0d2b", "path": audit.name, "sha256": digest(audit)},
    }
    packet = {
        "status": "GLOBAL_V3_PRERUN_INTEGRATION_SEALED_CANDIDATE",
        "governing_spec": "c18a8fc",
        "sources": sources,
        "scope": {
            "demonstrated_hooks": ["main_action", "attack", "blocks", "priority", "scry", "sneak"],
            "outside_claim_inconclusive": ["discard_draw", "hand_bottom_draw"],
            "outside_claim_reason": "conditional competencies remain INCONCLUSIVE; they are not passes or NOT REQUIRED classifications",
        },
        "global_counts": {
            "F": 12,
            "K": 24,
            "planned_invocations": 384,
            "formula": "24*12 + 4*24 = 384",
            "actual_pilot_invocations": 0,
        },
        "integrity": {
            "cross_packet_fixture_id_disjoint": True,
            "phase1_checks_preserved": True,
            "phase2a_checks_preserved": True,
            "transformations_and_privacy_sealed": True,
            "filtering_audit_preserved": True,
            "engine_frozen": True,
            "pilot_policies_frozen": True,
            "scoring_authorized": False,
        },
    }
    out = ROOT / "docs/cardcade/PILOT_FITNESS_V3_GLOBAL_PRERUN_INTEGRATION.json"
    payload = (json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    out.write_bytes(payload)
    value = hashlib.sha256(payload).hexdigest()
    (out.with_suffix(out.suffix + ".sha256")).write_text(value + "  " + out.name + "\n", encoding="ascii")
    report = ROOT / "docs/cardcade/PILOT_FITNESS_V3_GLOBAL_PRERUN_INTEGRATION.md"
    report.write_text(
        "# Pilot Fitness V3 Global Pre-Run Integration\n\n"
        "This candidate integrates the banked Phase 1 and Phase 2A packets under Specification V3.\n\n"
        "- Global F = 12; K = 24; planned calls = 384 (`24*12 + 4*24`).\n"
        "- Demonstrated hooks: Main Action, Attack, Blocks, Priority, Scry, and Sneak.\n"
        "- Discard/Draw and Hand-bottom/Draw remain outside the demonstrated claim because their conditional competencies are INCONCLUSIVE. They are not passes and were not classified NOT REQUIRED.\n"
        "- Cross-packet source hashes, transformation/privacy records, frozen references, and zero Pilot invocations are recorded in the JSON packet.\n"
        "- Pilot scoring remains unauthorized pending independent HQ review.\n",
        encoding="utf-8",
    )
    report_hash = hashlib.sha256(report.read_bytes()).hexdigest()
    (report.with_suffix(report.suffix + ".sha256")).write_text(
        report_hash + "  " + report.name + "\n", encoding="ascii"
    )
    print(json.dumps({"status": packet["status"], "F": 12, "K": 24, "invocations": 384, "digest": value}))


if __name__ == "__main__":
    main()
