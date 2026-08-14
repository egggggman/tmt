from dataclasses import FrozenInstanceError

import pytest

from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
    TurnPhase,
    TurnStep,
)

PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Bear", "{1}{W}", 2, "Creature — Bear", power=2, toughness=2)


def game(seed=1):
    deck = [PLAINS] * 30 + [BEAR] * 30
    return Game((deck, deck), seed=seed)


def test_exact_turn_graph_rejects_illegal_or_external_state_changes():
    current = game()
    assert (current.turn, current.active_player, current.phase, current.step) == (
        0,
        0,
        TurnPhase.SETUP.value,
        TurnStep.SETUP,
    )
    with pytest.raises(ValueError, match="illegal turn transition"):
        current.transition_to(TurnStep.DRAW)
    with pytest.raises(AttributeError):
        current.turn = 9
    with pytest.raises(AttributeError):
        current.active_player = 1
    with pytest.raises(AttributeError):
        current.step = TurnStep.CLEANUP
    with pytest.raises(AttributeError):
        current.phase = TurnPhase.ENDING.value
    view = current.public_view()
    with pytest.raises(FrozenInstanceError):
        view.step = TurnStep.CLEANUP.value


def test_engine_owns_rotation_first_draw_untap_land_reset_and_sickness():
    current = game()
    current.begin_turn()
    assert len(current.players[0].hand) == 7
    land = current.create_permanent(PLAINS, 0, summoning_sick=False)
    creature = current.create_permanent(BEAR, 0, summoning_sick=True)
    land.tapped = True
    current.players[0].lands_played = 1
    current.end_turn()

    current.begin_turn()
    assert (current.turn, current.active_player) == (2, 1)
    assert len(current.players[1].hand) == 8
    assert land.tapped
    assert creature.summoning_sick
    current.end_turn()

    current.begin_turn()
    assert (current.turn, current.active_player) == (3, 0)
    assert not land.tapped
    assert not creature.summoning_sick
    assert current.players[0].lands_played == 0


def test_actions_are_available_only_at_their_engine_owned_steps():
    current = game()
    current.begin_turn()
    attacker = current.create_permanent(BEAR, 0, summoning_sick=False)
    current.create_permanent(BEAR, 1, summoning_sick=False)
    assert current.legal_main_actions(0)
    assert not current.legal_attack_options(0)

    current.advance_step()
    assert current.step is TurnStep.BEGINNING_OF_COMBAT
    assert not current.legal_main_actions(0)
    assert not current.legal_attack_options(0)
    current.advance_step()
    attack = max(current.legal_attack_options(0), key=lambda option: len(option.attacker_ids))
    assert attack.attacker_ids == (attacker.object_id,)
    current.execute_attack_action(attack)
    with pytest.raises(ValueError, match="attack option is not currently legal"):
        current.execute_attack_action(attack)
    assert current.legal_block_options(attack, 1)
    blocks = ActionOption(ActionKind.DECLARE_BLOCKERS, 1)
    current.execute_block_action(blocks)
    with pytest.raises(ValueError, match="combat damage"):
        current.advance_step()
    current.resolve_combat_damage()
    with pytest.raises(ValueError, match="combat damage"):
        current.resolve_combat_damage()
    assert current.step is TurnStep.END_OF_COMBAT


def test_main_actions_are_rejected_during_combat_and_ending_steps():
    current = game()
    current.begin_turn()
    current.set_hand_for_testing(0, [PLAINS, BEAR])
    land = current.players[0].hand[0]
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    assert current.legal_main_actions(0) == ()
    assert not current.play_land(0, land)
    current.advance_step()
    current.advance_step()
    current.resolve_combat_damage()
    current.advance_to(TurnStep.END_STEP)
    assert current.legal_main_actions(0) == ()
    assert not current.play_land(0, land)


def test_cleanup_is_the_boundary_for_eot_damage_and_combat_reset():
    current = game()
    current.begin_turn()
    creature = current.create_permanent(BEAR, 0, summoning_sick=False)
    current.apply_pt_modifier(
        creature,
        1,
        0,
        duration="until_end_of_turn",
        source_card="Test",
        oracle_fragment="Test gets +1/+0 until end of turn.",
    )
    creature.damage = 1
    current.advance_to(TurnStep.COMBAT_DAMAGE)
    current.resolve_combat_damage()
    current.advance_to(TurnStep.END_STEP)
    assert creature.power == 3
    assert creature.damage == 1
    current.advance_step()
    assert creature.power == 2
    assert creature.damage == 0
    current.begin_turn()
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    assert current.legal_attack_options(current.active_player) == (
        ActionOption(ActionKind.DECLARE_ATTACKERS, current.active_player),
    )


def test_turn_replay_and_identity_invariants_are_deterministic():
    def replay(seed):
        current = game(seed)
        for _ in range(3):
            current.begin_turn()
            current.end_turn()
        current.check_invariants()
        return current.snapshot()

    assert replay(44) == replay(44)
