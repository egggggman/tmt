"""Generic complete Class level-three spell-cast team counter behavior."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
    TriggerEffect,
    TurnStep,
    load_facts,
)

LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Example Bear", "{0}", 0, "Creature — Bear", power=2, toughness=2)
ARTIFACT = CardFact("Example Cog", "{0}", 0, "Artifact")
SNEAK = CardFact(
    "Example Ninja",
    "{2}{W}",
    3,
    "Creature — Ninja",
    "Sneak {W} (You may cast this spell for {W} if you also return an unblocked attacker "
    "you control to hand during the declare blockers step. It enters tapped and attacking.)",
    power=2,
    toughness=2,
)
EFFECT = "Whenever you cast a spell, put a +1/+1 counter on each creature you control."
CLASS = CardFact(
    "Example Leadership",
    "{1}{W}",
    2,
    "Enchantment — Class",
    "(Gain the next level as a sorcery to add its ability.)\n"
    "Whenever you attack, put a +1/+1 counter on target attacking creature.\n"
    "{2}{W}: Level 2\n"
    "Whenever a creature you control leaves the battlefield, if it had a counter on it, "
    "you gain 2 life.\n"
    "{3}{W}: Level 3\n" + EFFECT,
)


def drain(game):
    while game.stack or game.priority_state is not None:
        if game.priority_state is None:
            game._begin_priority_window()
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def setup(seed=300, mana=7, class_card=CLASS):
    game = Game(([LAND] * 30, [LAND] * 30), seed=seed)
    game.begin_turn()
    for _ in range(mana):
        game.create_permanent(LAND, 0, summoning_sick=False)
    source = game.create_permanent(class_card, 0)
    assert game.activate_ability(0, source, "{2}{W}: Level 2")
    drain(game)
    return game, source


def advance(game, source):
    assert game.activate_ability(0, source, "{3}{W}: Level 3")
    assert source.class_level == 2
    drain(game)
    assert source.class_level == 3


def test_frozen_oracle_complete_section_and_cost_timing():
    catalog = Path(__file__).resolve().parents[1] / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    frozen = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")), {"Leader's Talent"}
    )["Leader's Talent"]
    interpreter = CardInterpreter()
    assert frozen.oracle_text == CLASS.oracle_text
    for card in (frozen, replace(CLASS, name="Another Class")):
        assert interpreter.class_spell_cast_team_counter(card, EFFECT)
        assert interpreter.class_level_child(card, 3) == EFFECT
        assert interpreter.activated_ability_semantics(
            card, "{3}{W}: Level 3"
        ).coverage.fully_supported
    for text in (EFFECT + " Draw a card.", EFFECT + "\nScry 1."):
        altered = replace(CLASS, oracle_text=CLASS.oracle_text.replace(EFFECT, text))
        assert interpreter.class_level_child(altered, 3) is None
        assert not interpreter.activated_ability_semantics(
            altered, "{3}{W}: Level 3"
        ).coverage.fully_supported
    misplaced = replace(CLASS, oracle_text=CLASS.oracle_text.replace("{3}{W}: Level 3\n", ""))
    assert not interpreter.class_spell_cast_team_counter(misplaced, EFFECT)
    game, source = setup(mana=6)
    assert game.activation_payment_plan(0, source, "{3}{W}: Level 3") is None
    game, source = setup(seed=301)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    assert not game.activate_ability(0, source, "{3}{W}: Level 3")
    game.check_invariants()


def test_authenticated_frozen_class_spell_cast_resolves_before_spell():
    catalog = Path(__file__).resolve().parents[1] / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    frozen = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")), {"Leader's Talent"}
    )["Leader's Talent"]
    game, source = setup(seed=305, class_card=frozen)
    recipient = game.create_permanent(BEAR, 0)
    advance(game, source)
    hand = game.set_hand_for_testing(0, [BEAR])[0]
    spell = game.announce_spell(0, hand)
    assert spell is not None
    assert game.stack[-1].effect is TriggerEffect.CLASS_SPELL_CAST_TEAM_COUNTER
    game._begin_priority_window()
    while game.priority_state is not None and not game.priority_state.resolution_pending:
        state = game.priority_state
        game.execute_priority_action(game.legal_priority_actions(state.player_index)[0])
    game.process_priority_resolution()
    assert recipient.counters["+1/+1"] == 1
    assert game.stack == [spell]
    drain(game)
    game.check_invariants()


def test_spell_cast_trigger_priority_current_team_source_departure_and_replay():
    def replay():
        game, source = setup()
        own = game.create_permanent(BEAR, 0)
        opposing = game.create_permanent(BEAR, 1)
        advance(game, source)
        hand = game.set_hand_for_testing(0, [BEAR])[0]
        spell = game.announce_spell(0, hand)
        assert spell is not None
        assert len(game.stack) == 2
        trigger = game.stack[-1]
        assert trigger.effect is TriggerEffect.CLASS_SPELL_CAST_TEAM_COUNTER
        assert trigger.event.subject_ids == (spell.object_id,)
        assert own.counters.get("+1/+1", 0) == 0
        with pytest.raises(ValueError, match="before all players pass"):
            game.resolve_top_of_stack()
        newcomer = game.create_permanent(BEAR, 0)
        game.change_controller(source, 1)
        game.move_object(source, "graveyard", reason="response")
        drain(game)
        assert own.counters["+1/+1"] == newcomer.counters["+1/+1"] == 1
        assert opposing.counters.get("+1/+1", 0) == 0
        assert any(e["event"] == "class_spell_cast_team_counters_resolved" for e in game.events)
        game.check_invariants()
        return game.events, game.snapshot()

    assert replay() == replay()


def test_nonartifact_and_artifact_casts_no_cast_at_entry_and_suppression():
    game, source = setup(seed=302)
    advance(game, source)
    own = game.create_permanent(BEAR, 0)
    assert not game.stack and not own.counters
    source.ability_loss_timestamp = (9999, 9999)
    hand = game.set_hand_for_testing(0, [ARTIFACT])[0]
    assert game.announce_spell(0, hand)
    assert len(game.stack) == 1
    drain(game)
    assert not own.counters
    source.ability_loss_timestamp = None
    hand = game.set_hand_for_testing(0, [ARTIFACT])[0]
    assert game.announce_spell(0, hand)
    assert len(game.stack) == 2
    drain(game)
    assert own.counters["+1/+1"] == 1
    game.check_invariants()


def test_level_two_remains_active_and_trigger_relink_fails_closed():
    game, source = setup(seed=303)
    creature = game.create_permanent(BEAR, 0)
    hand = game.set_hand_for_testing(0, [BEAR])[0]
    assert game.announce_spell(0, hand)
    assert len(game.stack) == 1  # Level two cannot trigger on spell cast.
    drain(game)
    game.place_counters(creature, "stun", 1, source_card="Fixture", oracle_fragment="test")
    game.move_object(creature, "graveyard")
    game.check_state_based_actions()
    drain(game)
    assert game.players[0].life == 22
    game.check_invariants()
    # Tampering with the linked cast ID cannot authorize counter placement.
    game, source = setup(seed=304)
    advance(game, source)
    hand = game.set_hand_for_testing(0, [BEAR])[0]
    assert game.announce_spell(0, hand)
    game.stack[-1].source_id = "fabricated"
    with pytest.raises(ValueError, match="source is invalid"):
        drain(game)


def test_sneak_cast_uses_same_event_and_does_not_counter_spell_before_entry():
    game, source = setup(seed=306, mana=8)
    attacker = game.create_permanent(BEAR, 0, summoning_sick=False)
    staying = game.create_permanent(BEAR, 0)
    advance(game, source)
    game.set_hand_for_testing(0, [SNEAK])
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        option
        for option in game.legal_attack_options(0)
        if option.attacker_ids == (attacker.object_id,)
    )
    game.execute_attack_action(attack)
    drain(game)
    game.advance_to(TurnStep.DECLARE_BLOCKERS)
    game.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))
    options = [option for option in game.legal_sneak_actions(0) if option.kind is ActionKind.CAST]
    assert len(options) == 1
    game.execute_sneak_action(options[0])
    assert game.stack[-1].effect is TriggerEffect.CLASS_SPELL_CAST_TEAM_COUNTER
    spell = game.stack[0]
    drain(game)
    assert staying.counters["+1/+1"] == 1
    assert attacker.zone == "former"
    entered = next(p for p in game.players[0].battlefield if p.card is SNEAK)
    assert entered.counters.get("+1/+1", 0) == 0
    assert any(
        record["event"] == "class_spell_cast_team_counters_resolved"
        and record["spell_id"] == spell.object_id
        for record in game.events
    )
    game.check_invariants()
