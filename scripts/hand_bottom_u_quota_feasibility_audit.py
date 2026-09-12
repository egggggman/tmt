"""Produce the bounded Hand-bottom/Draw U-quota feasibility audit."""

# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEARCH = ROOT / "docs/cardcade/PILOT_FITNESS_V2_REPLACEMENT_SEARCH.json"
AUDIT = ROOT / "docs/cardcade/PILOT_FITNESS_V2_REPLACEMENT_AUDIT.json"

ROLES = {
    "strict_filter_preferred": {
        "required": 2,
        "classification": "NO WITNESS IN BOUNDED SEARCH",
        "basis": "The Casey land-filter witness is model-sensitive; no reversal-free two-seat witness was certified. Raphael was screened structurally but not reconstructed into a complete witness.",
    },
    "strict_retention_preferred": {
        "required": 2,
        "classification": "FEASIBLE BUT UNCONSTRUCTED",
        "basis": "One optimistic two-seat singleton-Mountain land-context witness survives the screened predicate, but it lacks the complete objective, transformation and canonical fixture certificates; the second required disjoint role is absent.",
    },
    "competing_hand_identity": {
        "required": 1,
        "classification": "STRUCTURALLY OBSTRUCTED",
        "basis": "The tested two-card identity comparisons either reverse between materially plausible objectives or fail support/multiplicity consistency; no stable two-seat comparison remains.",
    },
    "exact_ev_tie": {
        "required": 1,
        "classification": "NO WITNESS IN BOUNDED SEARCH",
        "basis": "The apparent Mountain/Mountain tie is objective-sensitive: land availability ties while creature availability changes. It cannot be accepted as a stable exact-EV tie.",
    },
}


def main() -> None:
    search = json.loads(SEARCH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    assert search["status"] == "READINESS_STOP_NOT_SEALED"
    assert audit["status"] == "BOUNDED_SEARCH_READINESS_STOP"
    assert audit["probes"] == 76
    assert audit["complete_prior_action_outcome_rows_audited"] == 1612
    assert audit["optimistic_two_seat_strict_retention_capacity"]
    report = {
        "status": "FEASIBILITY AUDIT / QUOTA BLOCKED / NOT SEALED",
        "specification": "V2 ACCEPTED / UNCHANGED",
        "scope": {
            "decks": ["Casey Jones", "Raphael"],
            "contexts": "bounded filter endpoints, two existing setup schedules, both seats, and the recorded two-seat optimistic capacity audit",
            "horizons": [
                "filter resolution plus automatic/state-based drain",
                "empty-library boundary remains B",
            ],
            "draws": "at most one replacement Draw; no second hidden Draw",
            "search_limit": "prospective feasibility evidence, not generic strategic search or a proof over every legal board",
        },
        "required_roles": ROLES,
        "observed_evidence": {
            "replacement_search_commit": "1673eab",
            "original_failed_diagnostic_commit": "3f60166",
            "prospective_probes": 76,
            "complete_prior_rows": 1612,
            "strict_objective_reversals": 9,
            "support_failures": 18,
            "setup_multiplicity_failures": 2,
            "unresolved_survivors": 47,
            "optimistic_two_seat_retention_capacity": 1,
            "required_disjoint_retention_roles": 2,
            "raphael_filter_effect": "Raphael contains four Manhole Missile copies; no separate supported Hand-bottom/Draw semantics were found in its frozen list.",
        },
        "decision": "Pause fixture construction. The accepted V2 quota is not shown satisfiable by this bounded search; authorize V3 review only after HQ decides whether to expand the bounded search or treat the quota as structurally unsupported.",
        "pilot_invocations": 0,
        "canonical_fixtures_sealed": 0,
        "quotas_changed": False,
        "gameplay_or_policies_changed": False,
    }
    out = ROOT / "docs/cardcade/HAND_BOTTOM_U_QUOTA_FEASIBILITY_AUDIT.json"
    payload = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(
        "utf-8"
    )
    out.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    (Path(str(out) + ".sha256")).write_text(digest + "  " + out.name + "\n", encoding="ascii")
    print(json.dumps({"status": report["status"], "sha256": digest, "roles": ROLES}))


if __name__ == "__main__":
    main()
