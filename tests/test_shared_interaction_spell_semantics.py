"""Full Oracle clauses for generic kicked modifiers and top-card selection."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TurnStep, load_facts

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
FACTS = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")),
    {"Stomped by the Foot", "Cowabunga!"},
)
STOMP = FACTS["Stomped by the Foot"]
SELECT = FACTS["Cowabunga!"]
SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
FOREST = CardFact("Forest", "", 0, "Basic Land — Forest")
BEAR = CardFact("Bear", "{2}", 2, "Creature — Bear", power=3, toughness=3)
MUTANT = CardFact("Mutant Friend", "{2}", 2, "Creature — Mutant", power=2, toughness=2)
NINJA = CardFact("Quiet Friend", "{2}", 2, "Creature — Ninja", power=2, toughness=2)
TURTLE = CardFact("Shell Friend", "{2}", 2, "Creature — Turtle", power=2, toughness=2)
ARTIFACT = CardFact("Anonymous Relic", "{1}", 1, "Artifact")


def game(seed=2899, **kwargs):
    current = Game(([SWAMP] * 40, [FOREST] * 40), seed=seed, **kwargs)
    current.begin_turn()
    return current


def pass_priority(current):
    while current.priority_state is not None:
        state = current.priority_state
        if state.resolution_pending:
            current.process_priority_resolution()
        else:
            current.execute_priority_action(
                next(
                    action
                    for action in current.legal_priority_actions(state.player_index)
                    if action.kind is ActionKind.PASS_PRIORITY
                )
            )


def test_complete_frozen_and_renamed_grammar_fail_closed_on_followups():
    interpreter = CardInterpreter()
    for card in (STOMP, replace(STOMP, name="Other Spell")):
        assert interpreter.cast_program(card).kind is CastKind.KICKED_CREATURE_PT
        assert interpreter.unsupported_fragments(card) == ()
        assert (
            interpreter.kicked_creature_pt_program(
                replace(card, oracle_text=card.oracle_text + " Draw a card.")
            )
            is None
        )
    for card in (SELECT, replace(SELECT, name="Other Selection")):
        assert interpreter.cast_program(card).kind is CastKind.TOP_CARD_SELECTION
        assert interpreter.unsupported_fragments(card) == ()
        assert (
            interpreter.top_card_selection_program(
                replace(card, oracle_text=card.oracle_text + " Draw a card.")
            )
            is None
        )


def test_kicker_payment_choice_and_target_legality_at_announcement():
    current = game()
    target = current.create_permanent(BEAR, 1)
    cost = current.create_permanent(ARTIFACT, 0)
    swamp = current.create_permanent(SWAMP, 0)
    extra = current.create_permanent(FOREST, 0)
    card = current.set_hand_for_testing(0, [STOMP])[0]
    actions = [a for a in current.legal_main_actions(0) if a.object_id == card.object_id]
    assert {a.cost_object_id for a in actions} == {None, cost.object_id}
    assert current.announce_spell(0, card, target, sacrifice_cost=target) is None
    assert not swamp.tapped and not extra.tapped and cost.zone == "battlefield"
    spell = current.announce_spell(0, card, target, sacrifice_cost=cost)
    assert spell is not None and spell.kicker_sacrifice_id == cost.object_id
    assert cost.zone == "former" and swamp.tapped and extra.tapped
    assert target.toughness == 3
    current.resolve_top_of_stack()
    assert target.zone == "former" and spell.zone == "former"
    assert any(e["event"] == "kicker_cost_paid" for e in current.events)
    current.check_invariants()


def test_engine_main_action_uses_priority_before_resolution_for_both_spells():
    for source, lands in ((STOMP, (SWAMP, FOREST)), (SELECT, (FOREST,))):
        current = game()
        target = current.create_permanent(BEAR, 1)
        for land in lands:
            current.create_permanent(land, 0)
        card = current.set_hand_for_testing(0, [source])[0]
        choice = next(
            option
            for option in current.legal_main_actions(0)
            if option.object_id == card.object_id
            and option.cost_object_id is None
            and (source is SELECT or option.target_id == target.object_id)
        )
        assert current.execute_main_action(choice)
        assert current.stack and current.priority_state is not None
        if source is STOMP:
            assert target.power == 3
        pass_priority(current)
        assert not current.stack and current.priority_state is None
        if source is STOMP:
            assert target.power == 1
        current.check_invariants()


def test_ordinary_kicked_and_all_targets_illegal_after_paid_cost():
    current = game()
    target = current.create_permanent(BEAR, 1)
    current.create_permanent(SWAMP, 0)
    current.create_permanent(FOREST, 0)
    first = current.set_hand_for_testing(0, [STOMP])[0]
    assert current.announce_spell(0, first, target) is not None
    current.resolve_top_of_stack()
    assert target.toughness == 1 and target.power == 1
    current.end_turn()
    assert target.toughness == 3

    current2 = game()
    target2 = current2.create_permanent(BEAR, 1)
    cost = current2.create_permanent(ARTIFACT, 0)
    current2.create_permanent(SWAMP, 0)
    current2.create_permanent(FOREST, 0)
    card = current2.set_hand_for_testing(0, [STOMP])[0]
    spell = current2.announce_spell(0, card, target2, sacrifice_cost=cost)
    assert spell is not None
    current2.move_object(target2, "graveyard", reason="test_target_departed")
    current2.resolve_top_of_stack()
    assert cost.zone == "former" and spell.zone == "former"
    assert any(e["event"] == "spell_resolved_no_effect" for e in current2.events)
    current2.check_invariants()


def test_sacrificing_the_target_as_kicker_cost_fizzles_on_resolution():
    current = game()
    target = current.create_permanent(BEAR, 0)
    current.create_permanent(SWAMP, 0)
    current.create_permanent(FOREST, 0)
    spell = current.announce_spell(
        0, current.set_hand_for_testing(0, [STOMP])[0], target, sacrifice_cost=target
    )
    assert spell is not None and target.zone == "former"
    current.resolve_top_of_stack()
    assert any(e["event"] == "spell_resolved_no_effect" for e in current.events)
    current.check_invariants()


def test_instant_is_offered_in_priority_and_can_modify_blocked_creature():
    current = game()
    attacker = current.create_permanent(BEAR, 0, summoning_sick=False)
    blocker = current.create_permanent(BEAR, 1, summoning_sick=False)
    current.create_permanent(SWAMP, 1)
    current.create_permanent(FOREST, 1)
    card = current.set_hand_for_testing(1, [STOMP])[0]
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(a for a in current.legal_attack_options(0) if a.attacker_ids)
    current.execute_attack_action(attack)
    blocks = next(a for a in current.legal_block_options(attack, 1) if a.blocks)
    current.execute_block_action(blocks)
    assert current.priority_state is not None
    current.execute_priority_action(
        next(a for a in current.legal_priority_actions(0) if a.kind is ActionKind.PASS_PRIORITY)
    )
    action = next(
        a
        for a in current.legal_priority_actions(1)
        if a.object_id == card.object_id
        and a.target_id == attacker.object_id
        and a.cost_object_id is None
    )
    assert current.execute_priority_action(action)
    pass_priority(current)
    assert attacker.power == 1 and blocker.power == 3
    current.transition_to(TurnStep.COMBAT_DAMAGE)
    current.resolve_combat_damage()
    assert attacker.zone == "former" and blocker.zone == "battlefield"
    current.check_invariants()


@pytest.mark.parametrize("keyword", ["First strike", "Double strike"])
def test_pre_damage_modifier_respects_first_and_double_strike_steps(keyword):
    current = game()
    striker = replace(BEAR, name="Striker", oracle_text=keyword, keywords=(keyword,))
    attacker = current.create_permanent(striker, 0, summoning_sick=False)
    blocker = current.create_permanent(BEAR, 1, summoning_sick=False)
    current.create_permanent(SWAMP, 0)
    current.create_permanent(FOREST, 0)
    current.set_hand_for_testing(0, [STOMP])
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(a for a in current.legal_attack_options(0) if a.attacker_ids)
    current.execute_attack_action(attack)
    current.execute_block_action(
        next(a for a in current.legal_block_options(attack, 1) if a.blocks)
    )
    option = next(
        option
        for option in current.legal_priority_actions(0)
        if option.kind is ActionKind.CAST
        and option.target_id == blocker.object_id
        and option.cost_object_id is None
    )
    assert current.execute_priority_action(option)
    pass_priority(current)
    current.transition_to(TurnStep.COMBAT_DAMAGE)
    current.resolve_combat_damage()
    assert blocker.zone == "former" and attacker.zone == "battlefield"
    current.check_invariants()


def put_top(current, cards):
    for card in cards:
        obj = current.set_hand_for_testing(0, [card])[0]
        current.move_object(obj, "library", library_position="top", reason="test_top")


def test_top_four_reveal_eligibility_optional_choice_and_random_bottom():
    current = game()
    put_top(current, [BEAR, MUTANT, NINJA, TURTLE])
    before = tuple(current.players[0].library)
    current.create_permanent(FOREST, 0)
    spell = current.announce_spell(0, current.set_hand_for_testing(0, [SELECT])[0])
    assert spell is not None
    current.resolve_top_of_stack()
    effect = next(e for e in current.events if e["event"] == "top_card_selection_resolved")
    assert effect["revealed_id"] == before[-1].object_id
    assert len(effect["bottom_ids"]) == 3
    assert [c.object_id for c in current.players[0].library[:3]] == effect["bottom_ids"]
    assert all(c.object_id != effect["revealed_id"] for c in current.players[0].library)
    assert current.players[0].hand[-1].name == TURTLE.name
    current.check_invariants()

    declined = game(top_card_chooser=lambda _view, options: options[0])
    put_top(declined, [MUTANT, NINJA, TURTLE, BEAR])
    declined.create_permanent(FOREST, 0)
    card = declined.set_hand_for_testing(0, [SELECT])[0]
    assert declined.announce_spell(0, card) is not None
    declined.resolve_top_of_stack()
    event = next(e for e in declined.events if e["event"] == "top_card_selection_resolved")
    assert event["revealed_id"] is None and len(event["bottom_ids"]) == 4
    declined.check_invariants()


def test_land_qualifies_and_chooser_can_select_another_eligible_card():
    offered = []

    def choose(view, options):
        offered.extend(option.card_id for option in options)
        return next(option for option in options if option.card_id == view.cards[2].object_id)

    current = game(top_card_chooser=choose)
    put_top(current, [BEAR, FOREST, MUTANT, BEAR])
    eligible_land = current.players[0].library[-3]
    current.create_permanent(FOREST, 0)
    card = current.set_hand_for_testing(0, [SELECT])[0]
    assert current.announce_spell(0, card)
    current.resolve_top_of_stack()
    assert eligible_land.object_id in offered
    assert current.players[0].hand[-1].name == FOREST.name
    current.check_invariants()


def test_illegal_private_choice_has_no_resolution_zone_or_rng_mutation():
    current = game(top_card_chooser=lambda _view, _options: "fabricated")
    put_top(current, [MUTANT])
    current.create_permanent(FOREST, 0)
    assert current.announce_spell(0, current.set_hand_for_testing(0, [SELECT])[0])
    before = current.snapshot()
    with pytest.raises(ValueError, match="eligible option"):
        current.resolve_top_of_stack()
    assert current.snapshot() == before


def test_identical_seeds_replay_both_spell_choices_and_bottom_permutation():
    def run():
        current = game(seed=991)
        put_top(current, [MUTANT, BEAR, NINJA, TURTLE])
        current.create_permanent(FOREST, 0)
        current.create_permanent(SWAMP, 0)
        target = current.create_permanent(BEAR, 1)
        cost = current.create_permanent(ARTIFACT, 0)
        select, stomp = current.set_hand_for_testing(0, [SELECT, STOMP])
        assert current.announce_spell(0, select)
        current.resolve_top_of_stack()
        current.untap_permanent(current.players[0].battlefield[0])
        current.untap_permanent(current.players[0].battlefield[1])
        assert current.announce_spell(0, stomp, target, sacrifice_cost=cost)
        current.resolve_top_of_stack()
        current.check_invariants()
        return current.snapshot(), current.events

    assert run() == run()
