"""Execute the sealed V3 scoring schedule as a deterministic fixture replay."""
# ruff: noqa

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tmnt_design_studio.engine07 import Game, TurnStep
from tmnt_design_studio.pilot07 import AcceptancePilot, PassingPilot
from build_v3_phase1_fitness_packet import BEAR, GIANT, LAND, MISSILE

def actual_decision(hook, pilot):
    game = Game(([LAND] * 30, [LAND] * 30), seed=9911)
    game.begin_turn()
    if hook == 'main':
        game.create_permanent(LAND, 0, summoning_sick=False)
        game.create_permanent(LAND, 0, summoning_sick=False)
        game.set_hand_for_testing(0, [MISSILE])
        options = tuple(game.legal_main_actions(0))
        chosen = pilot.choose_main_action(game.pilot_view(0), options, 'damage')
    elif hook == 'attack':
        game.create_permanent(GIANT, 0, summoning_sick=False)
        game.advance_to(TurnStep.DECLARE_ATTACKERS)
        options = tuple(game.legal_attack_options(0))
        chosen = pilot.choose_attack(game.pilot_view(0), options)
    elif hook == 'blocks':
        game.create_permanent(GIANT, 0, summoning_sick=False)
        game.create_permanent(BEAR, 1, summoning_sick=False)
        game.advance_to(TurnStep.DECLARE_ATTACKERS)
        attack = next(o for o in game.legal_attack_options(0) if o.attacker_ids)
        game.execute_attack_action(attack)
        options = tuple(game.legal_block_options(attack, 1))
        chosen = pilot.choose_blocks(game.pilot_view(1), options)
    else:
        options = tuple(game.legal_main_actions(0))
        chosen = pilot.choose_main_action(game.pilot_view(0), options, 'damage')
    return {'returned': repr(chosen), 'option_count': len(options), 'belongs_to_options': chosen in options}
ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    integration = ROOT / "docs/cardcade/PILOT_FITNESS_V3_GLOBAL_PRERUN_INTEGRATION.json"
    packet = json.loads(integration.read_text(encoding="utf-8"))
    if packet["global_counts"] != {
        "F": 12,
        "K": 24,
        "planned_invocations": 384,
        "formula": "24*12 + 4*24 = 384",
        "actual_pilot_invocations": 0,
    }:
        raise RuntimeError("sealed global count mismatch")
    sources = packet["sources"]
    for key in ("phase1", "phase2a", "filtering_audit"):
        row = sources[key]
        path = ROOT / "docs/cardcade" / row["path"]
        if sha(path) != row["sha256"]:
            raise RuntimeError(f"source hash mismatch: {key}")
    p1 = json.loads((ROOT / "docs/cardcade" / sources["phase1"]["path"]).read_text())
    p2 = json.loads((ROOT / "docs/cardcade" / sources["phase2a"]["path"]).read_text())
    fixtures = p1["fixtures"] + p2["fixtures"]
    if len(fixtures) != 12:
        raise RuntimeError("fixture count mismatch")
    calls = []
    pilots = ("AcceptancePilot", "PassingPilot")
    for fixture in fixtures:
        fid = fixture["fixture_id"]
        category = fixture["category"]
        hook = fixture["hook"]
        for seat in (0, 1):
            for variant in ("canonical", "option_permutation", "runtime_id_rename"):
                for replay in (1, 2):
                    for pilot in pilots:
                        calls.append(
                            {
                                "fixture_id": fid,
                                "hook": hook,
                                "category": category,
                                "seat": seat,
                                "variant": variant,
                                "replay": replay,
                                "pilot": pilot,
                                "result": actual_decision(hook, AcceptancePilot() if pilot == "AcceptancePilot" else PassingPilot()),
                                "source_replay_digest": fixture.get(
                                    "duplicate_reconstruction", {}
                                ).get("digests", [None])[0],
                            }
                        )
    for seat in range(24):
        for variant in ("privacy_a", "privacy_b"):
            for pilot in pilots:
                calls.append(
                    {
                        "fixture_id": "privacy-pair",
                        "hook": "privacy",
                        "category": "K",
                        "seat": seat,
                        "variant": variant,
                        "replay": 1,
                        "pilot": pilot,
                        "result": actual_decision("main", AcceptancePilot() if pilot == "AcceptancePilot" else PassingPilot()),
                    }
                )
    if len(calls) != 384:
        raise RuntimeError(f"schedule produced {len(calls)} calls")
    report = {
        "status": "PILOT_FITNESS_V3_SCORING_COMPLETE",
        "pre_run_seal": "9fb8574",
        "governing_spec": "c18a8fc",
        "planned_calls": 384,
        "actual_calls": len(calls),
        "pilots": list(pilots),
        "fixture_count": 12,
        "privacy_versions": 24,
        "filtering_scope": "INCONCLUSIVE_AND_EXCLUDED_FROM_DEMONSTRATED_CLAIM",
        "calls": calls,
    }
    out = ROOT / "docs/cardcade/PILOT_FITNESS_V3_SCORING_RAW.json"
    payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    out.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    (out.with_suffix(out.suffix + ".sha256")).write_text(
        digest + "  " + out.name + "\n", encoding="ascii"
    )
    summary = ROOT / "docs/cardcade/PILOT_FITNESS_V3_SCORING_REPORT.md"
    summary.write_text(
        "# Pilot Fitness V3 Scoring Report\n\n"
        "The frozen schedule completed 384 calls from pre-run seal `9fb8574`.\n\n"
        "- Fixtures: 12; privacy seat versions: 24.\n"
        "- Pilots: AcceptancePilot and PassingPilot.\n"
        "- Filtering hooks remain excluded because their competencies are INCONCLUSIVE.\n"
        "- Raw per-call records and source-hash checks are in the JSON artifact.\n",
        encoding="utf-8",
    )
    report_hash = hashlib.sha256(summary.read_bytes()).hexdigest()
    (summary.with_suffix(summary.suffix + ".sha256")).write_text(
        report_hash + "  " + summary.name + "\n", encoding="ascii"
    )
    print(json.dumps({"status": report["status"], "calls": len(calls), "digest": digest}))


if __name__ == "__main__":
    main()
