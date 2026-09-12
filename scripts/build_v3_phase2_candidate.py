"""Build Phase 2 Scry/Sneak candidates and preserve U applicability evidence."""
# ruff: noqa

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from tmnt_design_studio.card_interpreter07 import ScryProgram
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, ScryOption, TurnStep

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Bear", "{1}{W}", 2, "Creature — Bear", power=2, toughness=2)
SNEAK = CardFact(
    "Anonymous Sneak",
    "{3}{W}",
    4,
    "Creature — Ninja",
    "Sneak {W} (You may cast this spell for {W} if you also return an unblocked attacker you control to hand during the declare blockers step. It enters tapped and attacking.)",
    power=4,
    toughness=4,
    keywords=("Sneak",),
)


def enc(v):
    if hasattr(v, "value"):
        return v.value
    if isinstance(v, tuple):
        return [enc(x) for x in v]
    if isinstance(v, list):
        return [enc(x) for x in v]
    if isinstance(v, dict):
        return {k: enc(x) for k, x in v.items()}
    return v


def scry_fixture():
    deck = [LAND, BEAR] * 10
    game = Game((deck, deck), seed=4101)
    game.begin_turn()
    inspected = tuple(reversed(game.players[0].library[-2:]))
    options = game.legal_scry_options(inspected)
    captured = []
    best = next(
        option
        for option in options
        if option.top_ids and game._objects[option.top_ids[0]].card.is_creature
    )

    def chooser(view, offered):
        captured.append({"view": enc(asdict(view)), "options": enc([asdict(o) for o in offered])})
        return best

    game.scry_chooser = chooser
    game.scry(0, ScryProgram(2), source_card="Phase2 Scry", oracle_fragment="Scry 2.")
    assert captured and captured[0]["options"] == enc([asdict(o) for o in options])
    branch = copy.deepcopy(game)
    return {
        "fixture_id": "V3-P2-001",
        "hook": "scry",
        "category": "R",
        "base": captured[0],
        "oracle": {
            "objective": "top inspected card is a creature at the endpoint",
            "acceptable": [enc(asdict(best))],
        },
        "horizon": "Scry 2 transaction completion and library mutation",
        "branch_digest": hashlib.sha256(
            json.dumps(enc(asdict(best)), sort_keys=True).encode()
        ).hexdigest(),
        "status": "CANDIDATE_UNSEALED",
    }


def sneak_fixture():
    game = Game(([LAND] * 20, [LAND] * 20), seed=4102)
    game.begin_turn()
    game.set_hand_for_testing(0, [SNEAK])
    game.create_permanent(LAND, 0, summoning_sick=False)
    attacker = game.create_permanent(BEAR, 0, controller=0, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack_option = next(o for o in game.legal_attack_options(0) if o.attacker_ids)
    game.execute_attack_action(attack_option)
    game.execute_block_action(
        next(o for o in game.legal_block_options(attack_option, 1) if not o.blocks)
    )
    options = game.legal_sneak_actions(0)
    captured = {
        "view": enc(asdict(game.pilot_view(0))),
        "options": enc([asdict(o) for o in options]),
    }
    cast = next(o for o in options if o.kind is ActionKind.CAST)
    branch = copy.deepcopy(game)
    branch.execute_sneak_action(cast)
    while branch.priority_state is not None:
        if branch.priority_state.resolution_pending:
            branch.process_priority_resolution()
        else:
            branch.execute_priority_action(
                branch.legal_priority_actions(branch.priority_state.player_index)[0]
            )
    while branch.step is TurnStep.COMBAT_DAMAGE:
        branch.resolve_combat_damage()
    return {
        "fixture_id": "V3-P2-002",
        "hook": "sneak",
        "category": "T",
        "base": captured,
        "oracle": {
            "objective": "Sneak cast produces lethal 4 combat damage within horizon",
            "acceptable": [enc(asdict(cast))],
            "winner": branch.winner,
        },
        "horizon": "Sneak announcement, Priority drain, resolution and combat damage",
        "branch_digest": hashlib.sha256(
            json.dumps(enc(asdict(cast)), sort_keys=True).encode()
        ).hexdigest(),
        "status": "CANDIDATE_UNSEALED",
    }


def scry_boundary():
    game = Game(([LAND] * 10, [LAND] * 10), seed=4103)
    game.begin_turn()
    game.players[0].library.clear()
    captured = []

    def chooser(view, options):
        captured.append({"view": enc(asdict(view)), "options": enc([asdict(o) for o in options])})
        return options[0]

    game.scry_chooser = chooser
    game.scry(0, ScryProgram(2), source_card="Phase2 Scry B", oracle_fragment="Scry 2.")
    return {
        "fixture_id": "V3-P2-003",
        "hook": "scry",
        "category": "B",
        "base": captured[0],
        "oracle": {"boundary": "empty_library_sole_choice"},
        "horizon": "empty-library Scry transaction",
        "status": "CANDIDATE_UNSEALED",
    }


def sneak_boundary():
    game = Game(([LAND] * 10, [LAND] * 10), seed=4104)
    game.begin_turn()
    game.set_hand_for_testing(0, [SNEAK])
    game.create_permanent(LAND, 0, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(o for o in game.legal_attack_options(0) if not o.attacker_ids)
    game.execute_attack_action(attack)
    block = next(o for o in game.legal_block_options(attack, 1) if not o.blocks)
    game.execute_block_action(block)
    options = game.legal_sneak_actions(0)
    return {
        "fixture_id": "V3-P2-004",
        "hook": "sneak",
        "category": "B",
        "base": {
            "view": enc(asdict(game.pilot_view(0))),
            "options": enc([asdict(o) for o in options]),
        },
        "oracle": {"boundary": "no_unblocked_attacker_pass_only"},
        "horizon": "empty Sneak decision",
        "status": "CANDIDATE_UNSEALED",
    }


def main():
    packet = {
        "status": "PHASE2_CANDIDATE_UNSEALED",
        "governing_spec": "c18a8fc",
        "phase1_sealed": "af6ba95",
        "pilot_invocations": 0,
        "fixtures": [scry_fixture(), sneak_fixture(), scry_boundary(), sneak_boundary()],
        "boundary_candidates": [],
        "discard_draw": {
            "status": "INCONCLUSIVE",
            "basis": "No complete V3 discard/Draw oracle and objective-stable direction has been sealed; no witness manufactured.",
        },
        "hand_bottom_draw": {
            "status": "INCONCLUSIVE",
            "filter_direction": "NO WITNESS IN BOUNDED SEARCH",
            "retention_direction": "FEASIBLE BUT UNCONSTRUCTED",
            "basis": "Preserved feasibility audit a577c0c; no restart or manufactured witness.",
        },
        "missing_before_phase2_seal": [
            "complete Scry/Sneak seat counterparts and privacy pairs",
            "independent oracle review",
            "Discard/Draw U table",
            "Hand-bottom/Draw conditional direction disposition",
        ],
    }
    out = ROOT / "docs/cardcade/PILOT_FITNESS_V3_PHASE2_CANDIDATE.json"
    payload = (json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    out.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    Path(str(out) + ".sha256").write_text(digest + "  " + out.name + "\n", encoding="ascii")
    print(
        json.dumps(
            {"status": packet["status"], "fixtures": len(packet["fixtures"]), "digest": digest}
        )
    )


if __name__ == "__main__":
    main()
