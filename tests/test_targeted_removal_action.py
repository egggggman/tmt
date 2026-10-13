"""Current-characteristic targeting and zone changes for direct removal spells."""

from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import ActionKind, ActionOption, CardFact, Game, TurnStep

SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
LARGE = CardFact("Large", "{4}{G}", 5, "Creature — Beast", power=5, toughness=5)
ENCHANTMENT = CardFact("Enchantment", "{2}{W}", 3, "Enchantment")
EXILE = CardFact(
    "Generic Exile", "{1}{B}", 2, "Instant", "Exile target creature with mana value 3 or less."
)
DESTROY = CardFact(
    "Generic Destroy",
    "{2}{B}",
    3,
    "Sorcery",
    "Sneak {B} (You may cast this spell for {B} if you also return an unblocked attacker "
    "you control to hand during the declare blockers step.)\n"
    "Destroy target creature or enchantment. If an enchantment was destroyed this way, "
    "you lose 2 life.",
)


def game(card, *, mana=3):
    current = Game(([SWAMP] * 60, [SWAMP] * 60), seed=801)
    current.begin_turn()
    current.set_hand_for_testing(0, [card])
    for _ in range(mana):
        current.create_permanent(SWAMP, 0, summoning_sick=False)
    return current


def test_exile_checks_mana_value_and_current_creature_type_then_locks_target():
    current = game(EXILE, mana=2)
    small = current.create_permanent(BEAR, 1, summoning_sick=False)
    large = current.create_permanent(LARGE, 1, summoning_sick=False)
    actions = current.legal_main_actions(0)
    assert {a.target_id for a in actions if a.kind is ActionKind.CAST} == {small.object_id}
    spell = current.announce_spell(0, current.players[0].hand[0], small)
    assert spell is not None and spell.cast_kind is CastKind.TARGETED_REMOVAL
    current.resolve_top_of_stack()
    assert small.zone == "former"
    assert [c.name for c in current.players[1].exile] == [BEAR.name]
    assert current.is_authoritative(large, "battlefield")
    assert any(
        e["event"] == "zone_changed" and e.get("reason") == "targeted_removal_exile"
        for e in current.events
    )
    current.check_invariants()


def test_illegal_target_on_resolution_fizzles_and_saves_conditional_life():
    current = game(DESTROY)
    target = current.create_permanent(ENCHANTMENT, 1)
    spell = current.announce_spell(0, current.players[0].hand[0], target)
    assert spell is not None
    current.move_object(target, "hand", reason="test_bounce")
    before = current.players[0].life
    current.resolve_top_of_stack()
    assert current.players[0].life == before
    assert any(e["event"] == "spell_resolved_no_effect" for e in current.events)


def test_destroy_creature_and_enchantment_life_condition_and_indestructible():
    for card, indestructible, expected_loss in (
        (BEAR, False, 0),
        (ENCHANTMENT, False, 2),
        (replace(ENCHANTMENT, oracle_text="Indestructible", keywords=("Indestructible",)), True, 0),
    ):
        current = game(DESTROY)
        target = current.create_permanent(card, 1)
        spell = current.announce_spell(0, current.players[0].hand[0], target)
        assert spell is not None
        before = current.players[0].life
        current.resolve_top_of_stack()
        assert current.players[0].life == before - expected_loss
        assert current.is_authoritative(target, "battlefield") is indestructible
        current.check_invariants()


def test_sneak_targeted_removal_pays_return_and_mana_with_replay():
    def run():
        current = game(DESTROY, mana=1)
        attacker = current.create_permanent(BEAR, 0, summoning_sick=False)
        target = current.create_permanent(ENCHANTMENT, 1)
        current.advance_to(TurnStep.DECLARE_ATTACKERS)
        current.execute_attack_action(
            ActionOption(ActionKind.DECLARE_ATTACKERS, 0, attacker_ids=(attacker.object_id,))
        )
        current.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))
        options = [a for a in current.legal_sneak_actions(0) if a.kind is ActionKind.CAST]
        assert len(options) == 2  # attacking creature and enchantment are both legal
        option = next(a for a in options if a.target_id == target.object_id)
        current.execute_sneak_action(option)
        assert current.stack[-1].target_id == target.object_id
        assert any(card.name == BEAR.name for card in current.players[0].hand)
        while current.priority_state is not None:
            if current.priority_state.resolution_pending:
                current.process_priority_resolution()
            else:
                current.execute_priority_action(
                    current.legal_priority_actions(current.priority_state.player_index)[0]
                )
        current.check_invariants()
        assert not current.is_authoritative(target, "battlefield")
        assert current.players[0].life == 18
        return current.snapshot()

    assert run() == run()


def test_only_complete_oracle_parent_and_legal_spelling_are_executable():
    interpreter = CardInterpreter()
    assert interpreter.targeted_removal_program(replace(EXILE, name="Unknown Spell")) is not None
    for text in (
        "Exile target creature.",
        "Exile target creature with mana value 3 or less. Draw a card.",
        "Destroy target creature or enchantment. Draw a card.",
    ):
        # The first is valid generic text; the other two require an unrepresented follow-up.
        card = replace(EXILE, oracle_text=text)
        assert (interpreter.targeted_removal_program(card) is not None) is (
            text == "Exile target creature."
        )
