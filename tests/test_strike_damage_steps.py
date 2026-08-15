import hashlib
import inspect
import json
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import (
    CardInterpreter,
    StrikeKeyword,
)
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    CombatDamageStepKind,
    Game,
    TurnStep,
)
from tmnt_design_studio.semantic_coverage import SemanticCoverage

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
NORMAL = CardFact("Normal", "{1}{W}", 2, "Creature — Bear", power=2, toughness=3)
FIRST = CardFact(
    "First",
    "{1}{W}",
    2,
    "Creature — Soldier",
    "First strike",
    2,
    3,
    ("First strike",),
)
DOUBLE = CardFact(
    "Double",
    "{1}{W}",
    2,
    "Creature — Soldier",
    "Double strike",
    2,
    3,
    ("Double strike",),
)
RECOGNIZED_NAMES = {
    "Baxter Stockman",
    "Casey Jones, Asphalt Hooligan",
    "Hard-Won Jitte",
    "Leonardo, Leader in Blue",
    "Leonardo, Sewer Samurai",
    "Leonardo, Worldly Warrior",
    "Mouser Attack!",
    "Null Group Biological Assets",
    "Raphael, the Nightwatcher",
    "Shark Shredder, Killer Clone",
    "Ticked Off",
    "Tokka & Rahzar, Unsupervised",
}
FULL_NAMES = {
    "Casey Jones, Asphalt Hooligan",
    "Leonardo, Sewer Samurai",
    "Leonardo, Worldly Warrior",
    "Null Group Biological Assets",
    "Raphael, the Nightwatcher",
    "Shark Shredder, Killer Clone",
    "Tokka & Rahzar, Unsupervised",
}
ROSTER_RECOGNIZED = {
    "Hard-Won Jitte",
    "Leonardo, Leader in Blue",
    "Leonardo, Sewer Samurai",
    "Mouser Attack!",
    "Null Group Biological Assets",
    "Raphael, the Nightwatcher",
    "Shark Shredder, Killer Clone",
}
ROSTER_FULL = {
    "Leonardo, Sewer Samurai",
    "Null Group Biological Assets",
    "Raphael, the Nightwatcher",
    "Shark Shredder, Killer Clone",
}
UNKNOWN_NAMES = {
    "Arcane Signet",
    "Chromatic Lantern",
    "Command Tower",
    "Double Jump // Flying Kick",
    "Exotic Orchard",
    "Fast Forward",
    "Plague of Vermin",
}


def game(seed=41):
    current = Game(([LAND] * 60, [LAND] * 60), seed=seed)
    current.begin_turn()
    return current


def declare(current, attacker, blocker=None):
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        option
        for option in current.legal_attack_options(0)
        if option.attacker_ids == (attacker.object_id,)
    )
    current.execute_attack_action(attack)
    blocks = ActionOption(
        ActionKind.DECLARE_BLOCKERS,
        1,
        blocks=() if blocker is None else ((attacker.object_id, blocker.object_id),),
    )
    current.execute_block_action(blocks)
    return attack


def permanent(current, fact, controller, *, sick=False):
    return current.create_permanent(fact, controller, summoning_sick=sick)


def catalog():
    return load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )


def coverage_sets():
    interpreter = CardInterpreter()
    recognized, executable, full = [], [], []
    seen = set()
    for card in sorted(catalog().cards, key=lambda value: (value.name, value.oracle_id)):
        if card.oracle_id in seen:
            continue
        seen.add(card.oracle_id)
        for fragment in interpreter.fragments(card):
            semantics = interpreter.strike_semantic_coverage(card, fragment)
            if semantics is None:
                continue
            member = (card.oracle_id, card.name, fragment)
            recognized.append(member)
            if semantics.coverage.payload_executable:
                executable.append(member)
            if semantics.coverage.fully_supported:
                full.append(member)
    return recognized, executable, full


def digest(members):
    encoded = json.dumps(members, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@pytest.mark.parametrize(
    ("attacker_fact", "blocker_fact", "first_roles", "regular_roles"),
    [
        (FIRST, NORMAL, ("first_strike",), ("regular",)),
        (NORMAL, FIRST, ("first_strike",), ("regular",)),
        (FIRST, FIRST, ("first_strike", "first_strike"), ()),
        (DOUBLE, NORMAL, ("double_strike_first",), ("double_strike_second", "regular")),
        (NORMAL, DOUBLE, ("double_strike_first",), ("regular", "double_strike_second")),
        (DOUBLE, FIRST, ("double_strike_first", "first_strike"), ("double_strike_second",)),
        (
            DOUBLE,
            DOUBLE,
            ("double_strike_first", "double_strike_first"),
            ("double_strike_second", "double_strike_second"),
        ),
    ],
)
def test_strike_pairings_use_two_authoritative_damage_steps(
    attacker_fact, blocker_fact, first_roles, regular_roles
):
    current = game()
    attacker = permanent(current, attacker_fact, 0)
    blocker = permanent(current, blocker_fact, 1)
    declare(current, attacker, blocker)

    first = current.resolve_combat_damage()
    assert first.kind is CombatDamageStepKind.FIRST_STRIKE
    assert tuple(assignment.role for assignment in first.assignments) == first_roles
    assert current.step is TurnStep.COMBAT_DAMAGE
    regular = current.resolve_combat_damage()
    assert regular.kind is CombatDamageStepKind.REGULAR
    assert tuple(assignment.role for assignment in regular.assignments) == regular_roles
    assert current.step is TurnStep.END_OF_COMBAT


def test_unblocked_first_strike_deals_once_but_still_creates_second_step():
    current = game()
    attacker = permanent(current, FIRST, 0)
    declare(current, attacker)
    first = current.resolve_combat_damage()
    assert current.players[1].life == 18
    regular = current.resolve_combat_damage()
    assert current.players[1].life == 18
    assert len(first.assignments) == 1 and not regular.assignments


def test_unblocked_double_strike_deals_in_both_steps_exactly_once_each():
    current = game()
    attacker = permanent(current, DOUBLE, 0)
    declare(current, attacker)
    first = current.resolve_combat_damage()
    regular = current.resolve_combat_damage()
    assert current.players[1].life == 16
    assert [item.assignments[0].role for item in (first, regular)] == [
        "double_strike_first",
        "double_strike_second",
    ]


def test_lethal_first_strike_sba_removes_blocker_before_regular_step():
    lethal_first = CardFact(
        "Lethal First", "{W}", 1, "Creature", "First strike", 3, 3, ("First strike",)
    )
    small = CardFact("Small", "{W}", 1, "Creature", power=2, toughness=2)
    current = game()
    attacker = permanent(current, lethal_first, 0)
    blocker = permanent(current, small, 1)
    declare(current, attacker, blocker)
    first = current.resolve_combat_damage()
    assert first.removed_before_next_step == (blocker.object_id,)
    assert current.is_authoritative(attacker, "battlefield")
    assert not current.is_authoritative(blocker, "battlefield")
    regular = current.resolve_combat_damage()
    assert not regular.assignments and attacker.damage == 0


def test_surviving_double_striker_deals_in_both_steps_and_damage_stays_marked():
    durable_double = CardFact(
        "Durable Double", "{W}", 1, "Creature", "Double strike", 2, 5, ("Double strike",)
    )
    durable = CardFact("Durable", "{W}", 1, "Creature", power=1, toughness=5)
    current = game()
    attacker = permanent(current, durable_double, 0)
    blocker = permanent(current, durable, 1)
    declare(current, attacker, blocker)
    current.resolve_combat_damage()
    assert blocker.damage == 2 and attacker.damage == 0
    current.resolve_combat_damage()
    assert blocker.damage == 4 and attacker.damage == 1


def test_creature_removed_between_steps_cannot_deal_again():
    current = game()
    attacker = permanent(current, DOUBLE, 0)
    declare(current, attacker)
    current.resolve_combat_damage()
    current.put_into_graveyard(attacker)
    regular = current.resolve_combat_damage()
    assert not regular.assignments
    assert current.players[1].life == 18


def test_normal_creature_that_skips_first_step_deals_in_regular_step_if_alive():
    weak_first = CardFact(
        "Weak First", "{W}", 1, "Creature", "First strike", 1, 4, ("First strike",)
    )
    current = game()
    attacker = permanent(current, NORMAL, 0)
    blocker = permanent(current, weak_first, 1)
    declare(current, attacker, blocker)
    first = current.resolve_combat_damage()
    assert tuple(item.source_id for item in first.assignments) == (blocker.object_id,)
    regular = current.resolve_combat_damage()
    assert tuple(item.source_id for item in regular.assignments) == (attacker.object_id,)


def test_fabricated_combatant_rejects_without_partial_mutation():
    current = game()
    attacker = permanent(current, DOUBLE, 0)
    declare(current, attacker)
    before = (current.players[1].life, attacker.damage, len(current.combat_damage_evidence))
    current._combat_attackers = ("object-fabricated",)
    with pytest.raises(ValueError, match="fabricated"):
        current.resolve_combat_damage()
    assert (current.players[1].life, attacker.damage, len(current.combat_damage_evidence)) == before


def test_stale_attacker_action_is_rejected_before_combat_mutation():
    current = game()
    attacker = permanent(current, FIRST, 0)
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    option = next(value for value in current.legal_attack_options(0) if value.attacker_ids)
    current.put_into_graveyard(attacker)
    with pytest.raises(ValueError, match="currently legal"):
        current.execute_attack_action(option)
    assert current.step is TurnStep.DECLARE_ATTACKERS


def test_combat_damage_steps_cannot_be_skipped_repeated_or_resolved_out_of_order():
    current = game()
    attacker = permanent(current, DOUBLE, 0)
    declare(current, attacker)
    with pytest.raises(ValueError, match="must be resolved"):
        current.transition_to(TurnStep.END_OF_COMBAT)
    current.resolve_combat_damage()
    with pytest.raises(ValueError, match="must be resolved"):
        current.transition_to(TurnStep.END_OF_COMBAT)
    current.resolve_combat_damage()
    with pytest.raises(ValueError, match="not ready"):
        current.resolve_combat_damage()


def test_postcombat_main_clears_current_combat_state_but_preserves_evidence():
    current = game()
    attacker = permanent(current, DOUBLE, 0)
    blocker = permanent(current, NORMAL, 1)
    declare(current, attacker, blocker)

    assert current._combat_attackers == (attacker.object_id,)
    assert current._combat_blocks == ((attacker.object_id, blocker.object_id),)
    first = current.resolve_combat_damage()
    assert current._combat_attackers and current._combat_blocks
    assert current._combat_damage_step_kind is CombatDamageStepKind.REGULAR
    regular = current.resolve_combat_damage()
    assert current.step is TurnStep.END_OF_COMBAT
    assert current._combat_attackers and current._combat_blocks
    assert current._combat_damage_step_kind is CombatDamageStepKind.COMPLETE

    evidence = tuple(current.combat_damage_evidence)
    current.transition_to(TurnStep.POSTCOMBAT_MAIN)

    assert current._combat_attackers == ()
    assert current._combat_blocks == ()
    assert not current._attackers_declared
    assert not current._blockers_declared
    assert not current._combat_damage_resolved
    assert current._combat_damage_step_kind is CombatDamageStepKind.NONE
    assert current._combat_damage_step_number == 0
    assert current._combat_damage_total_steps == 0
    assert current._first_damage_qualified_ids == ()
    assert current._first_double_strike_ids == ()
    assert current._regular_damage_initial_ids == ()
    assert tuple(current.combat_damage_evidence) == evidence == (first, regular)
    current.check_invariants()
    with pytest.raises(ValueError, match="not ready"):
        current.resolve_combat_damage()


def test_following_turn_and_later_combat_start_without_residual_state():
    current = game()
    attacker = permanent(current, DOUBLE, 0)
    declare(current, attacker)
    current.resolve_combat_damage()
    current.resolve_combat_damage()
    current.advance_to(TurnStep.CLEANUP)
    current.begin_turn()

    assert current._combat_attackers == ()
    assert current._combat_blocks == ()
    assert current._combat_damage_step_kind is CombatDamageStepKind.NONE
    current.advance_to(TurnStep.BEGINNING_OF_COMBAT)
    assert current._combat_attackers == ()
    assert current._combat_blocks == ()
    assert current._first_damage_qualified_ids == ()


def test_failed_transition_does_not_clear_or_fabricate_live_combat_state():
    current = game()
    attacker = permanent(current, DOUBLE, 0)
    declare(current, attacker)
    first = current.resolve_combat_damage()
    before = (
        current._combat_attackers,
        current._combat_blocks,
        current._combat_damage_step_kind,
        tuple(current.combat_damage_evidence),
    )

    with pytest.raises(ValueError, match="must be resolved"):
        current.transition_to(TurnStep.END_OF_COMBAT)

    assert (
        current._combat_attackers,
        current._combat_blocks,
        current._combat_damage_step_kind,
        tuple(current.combat_damage_evidence),
    ) == before
    assert before[-1] == (first,)


def test_first_step_game_end_is_coherent_without_postcombat_transition():
    current = game()
    attacker = permanent(current, FIRST, 0)
    declare(current, attacker)
    current.players[1].life = attacker.power

    evidence = current.resolve_combat_damage()

    assert current.winner == 0
    assert current.step is TurnStep.END_OF_COMBAT
    assert current._combat_attackers == (attacker.object_id,)
    assert current._combat_damage_step_kind is CombatDamageStepKind.COMPLETE
    assert tuple(current.combat_damage_evidence)[-1] == evidence
    with pytest.raises(ValueError, match="not ready"):
        current.resolve_combat_damage()


def test_wrong_zone_blocker_remains_a_block_but_deals_no_later_damage():
    durable_double = CardFact(
        "Durable Double", "{W}", 1, "Creature", "Double strike", 1, 5, ("Double strike",)
    )
    current = game()
    attacker = permanent(current, durable_double, 0)
    blocker = permanent(current, NORMAL, 1)
    declare(current, attacker, blocker)
    current.resolve_combat_damage()
    current.put_into_graveyard(blocker)
    regular = current.resolve_combat_damage()
    assert not regular.assignments
    assert current.players[1].life == 20


def test_no_strike_combat_retains_one_regular_damage_step():
    current = game()
    attacker = permanent(current, NORMAL, 0)
    declare(current, attacker)
    evidence = current.resolve_combat_damage()
    assert evidence.kind is CombatDamageStepKind.REGULAR
    assert (evidence.sequence, evidence.total_steps) == (1, 1)
    assert current.step is TurnStep.END_OF_COMBAT


def test_turn_scoped_first_strike_and_attack_scoped_double_strike_are_evaluated():
    conditional = CardFact(
        "Renamed Conditional",
        "{1}{R}",
        2,
        "Creature — Mutant",
        "During your turn, this creature has first strike.",
        2,
        2,
    )
    grant = CardFact(
        "Renamed Grant",
        "{1}{R}",
        2,
        "Creature — Turtle",
        "Attacking creatures you control have double strike.",
        2,
        3,
    )
    current = game()
    first = permanent(current, conditional, 0)
    source = permanent(current, grant, 0)
    assert current.evaluated_strike_keywords(first) == {StrikeKeyword.FIRST_STRIKE}
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(option for option in current.legal_attack_options(0) if option.attacker_ids)
    current.execute_attack_action(attack)
    assert current.evaluated_strike_keywords(source) == {StrikeKeyword.DOUBLE_STRIKE}


def test_turn_scoped_first_strike_does_not_apply_while_blocking_on_opponents_turn():
    conditional = CardFact(
        "Renamed Conditional",
        "{1}{R}",
        2,
        "Creature — Mutant",
        "During your turn, this creature has first strike.",
        2,
        2,
    )
    current = game()
    blocker = permanent(current, conditional, 1)
    assert not current.evaluated_strike_keywords(blocker)


def test_semantic_coverage_keeps_supported_rule_separate_from_unsupported_delivery():
    interpreter = CardInterpreter()
    activated = CardFact(
        "Renamed", "", 0, "Creature", "{1}{W}: Renamed gains first strike until end of turn."
    )
    semantics = interpreter.strike_semantic_coverage(activated, activated.oracle_text)
    assert semantics is not None
    assert semantics.coverage == SemanticCoverage(
        True, False, True, ("strike_activation_context_not_implemented",)
    )
    assert semantics.program.applicability is None


def test_unsupported_activated_or_temporary_grant_does_not_change_combat_keywords():
    activated = CardFact(
        "Renamed Activated",
        "{1}{W}",
        2,
        "Creature — Soldier",
        "{1}{W}: Renamed Activated gains first strike until end of turn.",
        2,
        2,
    )
    current = game()
    source = permanent(current, activated, 0)
    assert not current.evaluated_strike_keywords(source)


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("Equipped creature has double strike.", "strike_attachment_context_not_implemented"),
        (
            "At the beginning of combat on your turn, target creature gains first strike "
            "and vigilance until end of turn.",
            "strike_trigger_context_not_implemented",
        ),
        (
            "Target creature gains double strike until end of turn.",
            "strike_temporary_grant_context_not_implemented",
        ),
    ],
)
def test_unsupported_strike_contexts_remain_explicit(text, reason):
    card = CardFact("Renamed", "", 0, "Instant", text)
    semantics = CardInterpreter().strike_semantic_coverage(card, text)
    assert semantics is not None and reason in semantics.limitations
    assert not semantics.coverage.fully_supported


def test_authoritative_memberships_and_digests_are_locked():
    recognized, executable, full = coverage_sets()
    assert len({item[0] for item in recognized}) == 12 and len(recognized) == 12
    assert executable == recognized
    assert len({item[0] for item in full}) == 7 and len(full) == 7
    assert {item[1] for item in recognized} == RECOGNIZED_NAMES
    assert {item[1] for item in full} == FULL_NAMES
    assert digest(recognized) == "32e10abed618dd875abd28047910371b0ee1be4ad7b634f071bab0e6dbf93725"
    assert digest(executable) == "32e10abed618dd875abd28047910371b0ee1be4ad7b634f071bab0e6dbf93725"
    assert digest(full) == "7c03c57d6d1c84a769e0a834597914c718d6bb983381a408b50dc35a553f8ebc"


def test_frozen_roster_memberships_and_deck_exposure_are_locked():
    recognized, executable, full = coverage_sets()
    decks = {
        path.parent.name: {
            line.split(" ", 1)[1]
            for line in path.read_text(encoding="utf-8").splitlines()
            if line and line != "Deck"
        }
        for path in ROOT.glob("decks/*/PROTOTYPE_0.1.txt")
    }
    all_names = set().union(*decks.values())
    assert {item[1] for item in recognized} & all_names == ROSTER_RECOGNIZED
    assert {item[1] for item in executable} & all_names == ROSTER_RECOGNIZED
    assert {item[1] for item in full} & all_names == ROSTER_FULL
    assert {name for name, cards in decks.items() if cards & ROSTER_RECOGNIZED} == {
        "casey_jones",
        "leonardo",
        "raphael",
        "shredder",
        "splinter",
    }
    assert {name for name, cards in decks.items() if cards & ROSTER_FULL} == {
        "casey_jones",
        "leonardo",
        "raphael",
        "shredder",
        "splinter",
    }


def test_no_card_name_dispatch_multiple_blocker_broadening_or_unknown_reclassification():
    sources = (
        inspect.getsource(CardInterpreter.strike_program),
        inspect.getsource(CardInterpreter.strike_semantic_coverage),
        inspect.getsource(Game.evaluated_strike_keywords),
        inspect.getsource(Game.resolve_combat_damage),
    )
    for name in RECOGNIZED_NAMES | UNKNOWN_NAMES:
        assert all(name not in source for source in sources)
    assert "multiple" not in inspect.getsource(Game.resolve_combat_damage).casefold()
    assert {
        "Arcane Signet",
        "Chromatic Lantern",
        "Command Tower",
        "Double Jump // Flying Kick",
        "Exotic Orchard",
        "Fast Forward",
        "Plague of Vermin",
    } == UNKNOWN_NAMES


def test_deterministic_strike_step_evidence():
    def exercise():
        current = game(seed=7001)
        attacker = permanent(current, DOUBLE, 0)
        blocker = permanent(current, FIRST, 1)
        declare(current, attacker, blocker)
        current.resolve_combat_damage()
        current.resolve_combat_damage()
        return current.snapshot()["combat_damage"], current.events

    assert exercise() == exercise()
