"""Generic level-three Class permission and fixed-cost graveyard Sneak."""

from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import ActionKind, ActionOption, CardFact, Game, TurnStep

SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
BEAR = CardFact("Example Bear", "{1}{B}", 2, "Creature — Bear", power=2, toughness=2)
CLASS = CardFact(
    "Generic Night Class",
    "{2}{B}",
    3,
    "Enchantment — Class",
    "(Gain the next level as a sorcery to add its ability.)\n"
    "{1}{B}: Level 2\nCreatures you control get +1/+0 and have menace.\n"
    "{B}: Level 3\nCreature cards in your graveyard have sneak {3}{B}.\n"
    "You may cast creature spells from your graveyard using their sneak abilities.",
)
PRINTED_SNEAK = CardFact(
    "Example Scout",
    "{4}{B}",
    5,
    "Creature — Ninja",
    "Sneak {B} (You may cast this spell for {B} if you also return an unblocked attacker "
    "you control to hand during the declare blockers step. It enters tapped and attacking.)",
    power=4,
    toughness=4,
)


def resolve_priority(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def setup(*, mana=7, class_card=CLASS, card=BEAR, level=3):
    game = Game(([SWAMP] * 30, [SWAMP] * 30), seed=563)
    game.begin_turn()
    for _ in range(mana):
        game.create_permanent(SWAMP, 0, summoning_sick=False)
    source = game.create_permanent(class_card, 0)
    attacker = game.create_permanent(BEAR, 0, summoning_sick=False)
    graveyard_card = game._create_card_object(card, 0, "graveyard")
    game.players[0].graveyard.append(graveyard_card)
    if level >= 2:
        assert game.activate_ability(0, source, "{1}{B}: Level 2")
        resolve_priority(game)
    if level >= 3:
        assert game.activate_ability(0, source, "{B}: Level 3")
        resolve_priority(game)
    return game, source, attacker, graveyard_card


def blockers(game, attacker):
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        a for a in game.legal_attack_options(0) if a.attacker_ids == (attacker.object_id,)
    )
    game.execute_attack_action(attack)
    game.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))


def test_complete_level_three_is_required_and_incomplete_text_fails_closed():
    interpreter = CardInterpreter()
    grant = interpreter.class_graveyard_sneak(CLASS)
    assert grant == (
        "Creature cards in your graveyard have sneak {3}{B}.",
        "You may cast creature spells from your graveyard using their sneak abilities.",
        "{3}{B}",
    )
    assert interpreter.class_level_child(CLASS, 3) == grant[0]
    assert interpreter.activated_ability_semantics(CLASS, "{B}: Level 3").coverage.fully_supported
    assert all(
        fragment not in dict(interpreter.unsupported_fragments(CLASS)) for fragment in grant[:2]
    )
    for card in (
        replace(CLASS, name="Renamed Class"),
        replace(CLASS, oracle_text=CLASS.oracle_text + " Draw a card."),
        replace(
            CLASS,
            oracle_text=CLASS.oracle_text.replace(
                "You may cast creature spells", "You may play creature spells"
            ),
        ),
    ):
        if card.name == "Renamed Class":
            assert interpreter.class_graveyard_sneak(card) == grant
        else:
            assert interpreter.class_graveyard_sneak(card) is None
            assert not interpreter.activated_ability_semantics(
                card, "{B}: Level 3"
            ).coverage.fully_supported


def test_class_grant_is_executable_for_recipient_but_not_a_direct_sneak_keyword():
    grant = CardInterpreter().class_graveyard_sneak(CLASS)
    assert grant is not None
    semantics = CardInterpreter().sneak_semantic_coverage(CLASS, grant[0])
    assert semantics is not None and semantics.coverage.fully_supported
    assert semantics.program.granted_keyword_ability
    assert not semantics.program.direct_keyword_ability


def test_grant_source_in_hand_is_not_a_sneak_spell_and_graveyard_creature_still_is():
    def replay():
        game, source, attacker, grave = setup()
        card = game._create_card_object(replace(CLASS, name="Another Training Class"), 0, "hand")
        game.players[0].hand.append(card)
        blockers(game, attacker)
        options = game.legal_sneak_actions(0)
        assert not any(option.object_id == card.object_id for option in options)
        assert game.sneak_payment_plan(0, card, attacker) is None
        forged = ActionOption(
            ActionKind.CAST,
            0,
            object_id=card.object_id,
            cost_object_id=attacker.object_id,
            oracle_fragment="Creature cards in your graveyard have sneak {3}{B}.",
        )
        with pytest.raises(ValueError, match="not currently legal"):
            game.execute_sneak_action(forged)
        assert card.zone == "hand" and attacker.zone == "battlefield"
        option = next(option for option in options if option.object_id == grave.object_id)
        game.execute_sneak_action(option)
        game.move_object(source, "graveyard")
        resolve_priority(game)
        evidence = game.sneak_evidence[-1]
        assert evidence.source_zone == "graveyard"
        assert evidence.permission_source_id == source.object_id
        assert evidence.resolved_object_id in game._combat_attackers
        assert all(object_id != card.object_id for object_id in game._combat_attackers)
        game.check_invariants()
        return game.snapshot(), game.events

    assert replay() == replay()


def test_level_cost_timing_priority_and_source_zone_gate():
    game, source, attacker, grave = setup(level=2)
    assert source.class_level == 2
    assert game.activation_payment_plan(0, source, "{B}: Level 3") is not None
    assert game.activate_ability(0, source, "{B}: Level 3")
    assert source.class_level == 2
    resolve_priority(game)
    assert source.class_level == 3
    blockers(game, attacker)
    options = [a for a in game.legal_sneak_actions(0) if a.object_id == grave.object_id]
    assert len(options) == 1
    assert options[0].oracle_fragment == "Creature cards in your graveyard have sneak {3}{B}."
    assert game.sneak_payment_plan(0, grave, attacker, oracle_fragment=options[0].oracle_fragment)
    game.check_invariants()


def test_graveyard_cast_uses_normal_return_payment_stack_and_source_independence():
    game, source, attacker, grave = setup()
    blockers(game, attacker)
    option = next(a for a in game.legal_sneak_actions(0) if a.object_id == grave.object_id)
    game.execute_sneak_action(option)
    spell = game.stack[-1]
    assert spell.cast_from_graveyard
    assert grave.zone == "former" and attacker.zone == "former"
    assert game.sneak_evidence[-1].source_zone == "graveyard"
    assert game.sneak_evidence[-1].permission_source_id == source.object_id
    assert not any(card is grave for card in game.players[0].graveyard)
    assert any(
        e["event"] == "sneak_announced" and e["source_zone"] == "graveyard" for e in game.events
    )
    assert any(
        e["event"] == "spell_cast"
        and e["stack_object_id"] == spell.object_id
        and e["source_zone"] == "graveyard"
        for e in game.events
    )
    with pytest.raises(ValueError, match="before all players pass"):
        game.resolve_top_of_stack()
    game.move_object(source, "graveyard")
    resolve_priority(game)
    evidence = game.sneak_evidence[-1]
    entered = game._objects[evidence.resolved_object_id]
    assert entered.tapped and entered.object_id in game._combat_attackers
    assert entered.counters.get("finality", 0) == 0
    assert evidence.permission_source_id == source.object_id
    game.check_invariants()


def test_illegal_timing_payment_blocking_zone_and_controller_are_rejected():
    game, source, attacker, grave = setup(mana=3, level=2)
    assert not game.legal_sneak_actions(0)
    assert game.activate_ability(0, source, "{B}: Level 3")
    resolve_priority(game)
    assert not game.legal_sneak_actions(0)
    blockers(game, attacker)
    assert not [a for a in game.legal_sneak_actions(0) if a.object_id == grave.object_id]
    other, class_source, other_attacker, other_grave = setup()
    blockers(other, other_attacker)
    assert any(a.object_id == other_grave.object_id for a in other.legal_sneak_actions(0))
    other.change_controller(class_source, 1)
    assert not any(a.object_id == other_grave.object_id for a in other.legal_sneak_actions(0))
    game.check_invariants()
    other.check_invariants()


def test_multiple_printed_and_granted_sneak_costs_are_distinct_choices():
    game, source, attacker, grave = setup(card=PRINTED_SNEAK)
    blockers(game, attacker)
    options = [a for a in game.legal_sneak_actions(0) if a.object_id == grave.object_id]
    assert len(options) == 2
    costs = {
        a.oracle_fragment: game.sneak_payment_plan(
            0, grave, attacker, oracle_fragment=a.oracle_fragment
        ).requirement.total
        for a in options
    }
    assert sorted(costs.values()) == [1, 4]
    selected = next(a for a in options if costs[a.oracle_fragment] == 1)
    game.execute_sneak_action(selected)
    assert game.sneak_evidence[-1].mana_requirement.total == 1
    game.check_invariants()


def test_stale_permission_or_card_identity_rejected_and_replay_deterministic():
    game, source, attacker, grave = setup()
    blockers(game, attacker)
    option = next(a for a in game.legal_sneak_actions(0) if a.object_id == grave.object_id)
    game.move_object(source, "exile")
    with pytest.raises(ValueError, match="currently legal"):
        game.execute_sneak_action(option)
    assert grave.zone == "graveyard" and attacker.zone == "battlefield"

    other, _source, other_attacker, other_grave = setup()
    blockers(other, other_attacker)
    stale = next(a for a in other.legal_sneak_actions(0) if a.object_id == other_grave.object_id)
    other.move_object(other_grave, "hand")
    with pytest.raises(ValueError, match="currently legal"):
        other.execute_sneak_action(stale)

    blocked, _source, blocked_attacker, blocked_grave = setup()
    first = blocked.create_permanent(BEAR, 1)
    second = blocked.create_permanent(BEAR, 1)
    blocked.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(a for a in blocked.legal_attack_options(0) if a.attacker_ids)
    blocked.execute_attack_action(attack)
    block = next(
        action
        for action in blocked.legal_block_options(attack, 1)
        if {b for _a, b in action.blocks} == {first.object_id, second.object_id}
    )
    blocked.execute_block_action(block)
    assert blocked_attacker not in blocked._unblocked_attackers(0)
    assert not any(a.object_id == blocked_grave.object_id for a in blocked.legal_sneak_actions(0))

    def replay():
        g, _source, returning, creature = setup()
        blockers(g, returning)
        action = next(a for a in g.legal_sneak_actions(0) if a.object_id == creature.object_id)
        g.execute_sneak_action(action)
        resolve_priority(g)
        g.check_invariants()
        return g.snapshot(), g.events

    assert replay() == replay()
