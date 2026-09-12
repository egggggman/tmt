"""Construct and audit a small V3 Phase 1 fitness corpus without Pilots."""
# ruff: noqa

from __future__ import annotations

import copy
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

from tmnt_design_studio.card_interpreter07 import CastKind
from tmnt_design_studio.engine07 import (
    ActionKind,
    CardFact,
    CastKind as EngineCastKind,
    Game,
    StackObject,
    TurnStep,
)

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Mountain", "", 0, "Basic Land — Mountain")
BEAR = CardFact("Bear", "{1}{R}", 2, "Creature — Bear", power=2, toughness=2)
GIANT = CardFact("Giant", "{R}", 1, "Creature — Giant", power=20, toughness=20)
MISSILE = CardFact(
    "Manhole Missile", "{1}{R}", 2, "Instant", "Manhole Missile deals 3 damage to target creature."
)
FUGITIVE = CardFact(
    "Fugitive Droid",
    "{2}{U}",
    3,
    "Artifact Creature — Robot",
    "{U}, Sacrifice this creature: Counter target spell that targets an artifact or creature you control.",
    power=2,
    toughness=2,
    oracle_id="fugitive",
)
BOLT = CardFact(
    "Bolt", "{R}", 1, "Instant", "Bolt deals 3 damage to target creature.", oracle_id="bolt"
)


def deck(card=LAND):
    return [card] * 60


def encode(value):
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, tuple):
        return [encode(x) for x in value]
    if isinstance(value, list):
        return [encode(x) for x in value]
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    return value


def capture(game, seat, options):
    return {
        "view": encode(asdict(game.pilot_view(seat))),
        "options": encode([asdict(o) for o in options]),
    }


def drain_priority(game):
    for _ in range(20):
        if game.priority_state is None:
            return
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            options = game.legal_priority_actions(game.priority_state.player_index)
            game.execute_priority_action(options[0])
    raise AssertionError("priority did not drain")


def main_t():
    game = Game((deck(), deck()), seed=3001)
    game.begin_turn()
    game.create_permanent(LAND, 0, summoning_sick=False)
    game.create_permanent(LAND, 0, summoning_sick=False)
    attacker = game.create_permanent(GIANT, 0, summoning_sick=False)
    target = game.create_permanent(BEAR, 1, summoning_sick=False)
    game.set_hand_for_testing(0, [MISSILE])
    options = game.legal_main_actions(0)
    base = capture(game, 0, options)
    outcomes = []
    for option in options:
        branch = copy.deepcopy(game)
        branch.execute_main_action(option)
        drain_priority(branch)
        branch.advance_to(TurnStep.DECLARE_ATTACKERS)
        attack = next(o for o in branch.legal_attack_options(0) if o.attacker_ids)
        branch.combat(
            [next(p for p in branch.players[0].battlefield if p.card.name == "Giant")],
            auto_assign_blockers=True,
        )
        outcomes.append(
            {
                "option": encode(asdict(option)),
                "winner": branch.winner,
                "target_zone": next(
                    (p.zone for p in branch.players[1].battlefield if p.card.name == "Bear"), "gone"
                ),
            }
        )
    return (
        "main_t_missile_clears_blocker",
        0,
        base,
        outcomes,
        {"guaranteed_win": [i for i, o in enumerate(outcomes) if o["winner"] == 0]},
    )


def attack_t():
    game = Game((deck(), deck()), seed=3002)
    game.begin_turn()
    attacker = game.create_permanent(GIANT, 0, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    options = game.legal_attack_options(0)
    base = capture(game, 0, options)
    outcomes = []
    for option in options:
        branch = copy.deepcopy(game)
        if option.attacker_ids:
            branch.combat(
                [next(p for p in branch.players[0].battlefield if p.card.name == "Giant")],
                auto_assign_blockers=True,
            )
        outcomes.append(
            {
                "option": encode(asdict(option)),
                "winner": branch.winner,
                "life": [p.life for p in branch.players],
            }
        )
    return (
        "attack_t_unblocked_lethal",
        0,
        base,
        outcomes,
        {"guaranteed_win": [i for i, o in enumerate(outcomes) if o["winner"] == 0]},
    )


def blocks_t():
    game = Game((deck(), deck()), seed=3003)
    game.begin_turn()
    attacker = game.create_permanent(GIANT, 0, summoning_sick=False)
    blocker = game.create_permanent(BEAR, 1, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(o for o in game.legal_attack_options(0) if o.attacker_ids)
    game.execute_attack_action(attack)
    options = game.legal_block_options(attack, 1)
    base = capture(game, 1, options)
    outcomes = []
    for option in options:
        branch = copy.deepcopy(game)
        branch.execute_block_action(option)
        if branch.step is TurnStep.DECLARE_BLOCKERS:
            branch.execute_sneak_action(
                ActionKind.PASS
                and next(o for o in branch.legal_sneak_actions(0) if o.kind is ActionKind.PASS)
            )
        while branch.step is TurnStep.COMBAT_DAMAGE:
            branch.resolve_combat_damage()
        outcomes.append(
            {
                "option": encode(asdict(option)),
                "winner": branch.winner,
                "life": [p.life for p in branch.players],
            }
        )
    return (
        "blocks_t_prevent_lethal",
        1,
        base,
        outcomes,
        {"acceptable": [i for i, o in enumerate(outcomes) if o["winner"] is None]},
    )


def priority_t():
    game = Game((deck(), deck()), seed=3004)
    game.begin_turn()
    mana = game.create_permanent(
        CardFact("Island", "", 0, "Basic Land — Island"), 0, summoning_sick=False
    )
    target = game.create_permanent(BEAR, 0, summoning_sick=False)
    source = game.create_permanent(FUGITIVE, 0, summoning_sick=False)
    spell = StackObject(
        game._allocate_object_id(), BOLT, 1, 1, EngineCastKind.DEAL_DAMAGE, target.object_id
    )
    game._register(spell)
    game.stack.append(spell)
    game._begin_priority_window()
    options = game.legal_priority_actions(0)
    base = capture(game, 0, options)
    outcomes = []
    for option in options:
        branch = copy.deepcopy(game)
        branch.execute_priority_action(option)
        drain_priority(branch)
        outcomes.append(
            {
                "option": encode(asdict(option)),
                "target_zone": next(
                    (p.zone for p in branch.players[0].battlefield if p.card.name == "Bear"), "gone"
                ),
                "spell_zone": next(
                    (s.zone for s in branch.players[1].graveyard if s.card.name == "Bolt"), "gone"
                ),
            }
        )
    return (
        "priority_t_counter_response",
        0,
        base,
        outcomes,
        {"acceptable": [i for i, o in enumerate(outcomes) if o["target_zone"] == "battlefield"]},
    )


def boundary(hook, seat, seed):
    game = Game((deck(), deck()), seed=seed)
    game.begin_turn()
    if hook == "main_action":
        options = game.legal_main_actions(0)
        owner = 0
    elif hook == "attack":
        game.advance_to(TurnStep.DECLARE_ATTACKERS)
        options = game.legal_attack_options(0)
        owner = 0
    elif hook == "blocks":
        game.advance_to(TurnStep.DECLARE_ATTACKERS)
        attack = next(o for o in game.legal_attack_options(0) if not o.attacker_ids)
        game.execute_attack_action(attack)
        options = game.legal_block_options(attack, 1)
        owner = 1
    else:
        options = ()
        owner = seat
    return (
        f"{hook}_b_empty",
        owner,
        capture(game, owner, options),
        [],
        {"boundary": "empty_or_pass_only"},
    )


def priority_b():
    game = Game((deck(), deck()), seed=3014)
    game.begin_turn()
    spell = StackObject(game._allocate_object_id(), BOLT, 1, 1, EngineCastKind.DEAL_DAMAGE, None)
    game._register(spell)
    game.stack.append(spell)
    game._begin_priority_window()
    options = game.legal_priority_actions(0)
    return (
        "priority_b_pass_only",
        0,
        capture(game, 0, options),
        [],
        {"boundary": "pass_only_no_counter_source"},
    )


def main():
    records = [main_t(), attack_t(), blocks_t(), priority_t()]
    records += [boundary(h, 0, 3010 + i) for i, h in enumerate(("main_action", "attack", "blocks"))]
    records.append(priority_b())
    fixtures = []
    for fid, (name, seat, base, outcomes, oracle) in enumerate(records, 1):
        fixtures.append(
            {
                "fixture_id": f"V3-P1-{fid:03d}",
                "name": name,
                "hook": name.split("_")[0] if name.startswith("main") else name.split("_")[0],
                "seat": seat,
                "category": "B" if "_b_" in name else "T",
                "base": base,
                "branches": outcomes,
                "oracle": oracle,
                "horizon": "immediate engine resolution; combat fixtures drain combat damage and SBAs; priority drains all represented passes/resolution",
                "distinctness": "distinct decision hook or empty boundary",
                "seat_counterpart": "required and not yet sealed",
                "transformations": {
                    "option_permutation": "required",
                    "runtime_id_rename": "required",
                },
                "privacy": "eligibility pending paired reconstruction",
                "status": "CANDIDATE_UNSEALED",
            }
        )
    packet = {
        "status": "PHASE1_CANDIDATE_UNSEALED",
        "governing_spec": "c18a8fc",
        "reachability_baseline": "20fbfad",
        "pilot_invocations": 0,
        "F": len(fixtures),
        "K": None,
        "invocation_formula": "24F + 4K",
        "u_applicability": "NOT_APPLICABLE_STRUCTURAL",
        "fixtures": fixtures,
        "missing_before_seal": [
            "justified opposite-seat counterparts",
            "executed option-order permutations",
            "executed runtime-ID renamings",
            "privacy eligibility pairs",
            "independent oracle review",
        ],
    }
    out = ROOT / "docs/cardcade/PILOT_FITNESS_V3_PHASE1_CANDIDATE.json"
    payload = (json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    out.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    Path(str(out) + ".sha256").write_text(digest + "  " + out.name + "\n", encoding="ascii")
    print(json.dumps({"status": packet["status"], "fixtures": len(fixtures), "digest": digest}))


if __name__ == "__main__":
    main()
