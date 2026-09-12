"""Build a no-Pilot Phase 1 evidence inventory from frozen acceptance records."""
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/cardcade/ACCEPTANCE_STAGE_002_RESULTS_03.json"

HOOKS = {
    "main_action": {
        "u": "NOT_APPLICABLE_STRUCTURAL",
        "u_basis": "Main-action options are generated before execution; the one supported hand-bottom replacement decision is a separate nested chooser, not a main-action U outcome.",
        "required": ["T", "R", "B"],
    },
    "attack": {
        "u": "NOT_APPLICABLE_STRUCTURAL",
        "u_basis": "Attack option generation contains attacker subsets and public combat state; no replacement Draw is part of the attack choice surface.",
        "required": ["T", "B"],
    },
    "blocks": {
        "u": "NOT_APPLICABLE_STRUCTURAL",
        "u_basis": "Block option generation contains assignments over visible attackers/blockers; no replacement Draw is part of the block choice surface.",
        "required": ["T", "B"],
    },
    "priority": {
        "u": "NOT_APPLICABLE_STRUCTURAL",
        "u_basis": "Priority options are pass/represented responses at a fixed epoch; random Draws occur only in later resolved effects and are not an input to this decision.",
        "required": ["T", "B"],
    },
}


def main() -> None:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    games = data["aggregate"]["games"]
    candidates = []
    for game in games:
        candidates.append(
            {
                "game_id": game["game_id"],
                "orientation": game["orientation"],
                "pairing_id": game["pairing_id"],
                "seats": game["seats"],
                "seed": game["seed"],
                "reachability_evidence": {
                    "opportunity_witness_count": len(game["opportunity_witnesses"]),
                    "authenticated_execution_count": len(game["authenticated_executed_references"]),
                    "transaction_counts": game["transaction_counts"],
                    "invariant_violations": len(game["invariant_violations"]),
                },
                "fitness_status": "REACHABILITY_ONLY_UNSEALED",
                "missing": [
                    "complete Pilot observation and option payload",
                    "independent T/R/B oracle contract and acceptable set",
                    "genuine seat counterpart transformation certificate",
                    "privacy eligibility and paired perturbation",
                    "option-order and runtime-ID transformations",
                ],
            }
        )
    packet = {
        "status": "PHASE1_INCOMPLETE_READINESS_STOP",
        "governing_spec": "c18a8fc",
        "phase": "Main Action, Attack, Blocks, Priority",
        "pilot_invocations": 0,
        "canonical_fixtures": 0,
        "F": None,
        "K": None,
        "invocation_formula": "24F + 4K",
        "hooks": HOOKS,
        "candidate_reachability_records": candidates,
        "source": {
            "path": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256_canonical_lf": hashlib.sha256(
                SOURCE.read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest(),
        },
        "disposition": "Required T/R/B evidence remains INCONCLUSIVE because existing acceptance records do not provide fitness oracle tables or seat/privacy transformations. No fixture is counted.",
    }
    out = ROOT / "docs/cardcade/PILOT_FITNESS_V3_PHASE1_PREPARATION_INVENTORY.json"
    payload = (json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    out.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    Path(str(out) + ".sha256").write_text(digest + "  " + out.name + "\n", encoding="ascii")
    print(json.dumps({"status": packet["status"], "games": len(games), "digest": digest}))


if __name__ == "__main__":
    main()
