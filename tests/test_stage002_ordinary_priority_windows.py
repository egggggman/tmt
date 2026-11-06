"""Bounded, non-game Stage 002 ordinary priority window regressions.

No test calls run_game, any execution launcher, or end-to-end gameplay.
"""

from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TurnStep
from tmnt_design_studio.stage002 import _drain_ordinary_step_priority

LAND = CardFact("Plains", "", 0, "Basic Land — Plains")


class PassOnlyPilot:
    def choose_priority(self, _view, options):
        return next(option for option in options if option.kind is ActionKind.PASS_PRIORITY)


def _synthetic_game():
    game = Game(([LAND] * 20, [LAND] * 20), seed=383)
    game.begin_turn()
    return game


def _passes(game):
    return [
        (event["player_index"], event["priority_epoch"])
        for event in game.events
        if event["event"] == "priority_passed"
    ]


def test_empty_beginning_of_combat_offers_both_players_priority():
    game = _synthetic_game()
    game.advance_step()
    assert game.step is TurnStep.BEGINNING_OF_COMBAT
    assert game.stack == []
    assert game.priority_state is None

    _drain_ordinary_step_priority(game, PassOnlyPilot())

    assert game.step is TurnStep.BEGINNING_OF_COMBAT
    assert game.stack == []
    assert game.priority_state is None
    assert len(_passes(game)) == 2
    assert [entry[0] for entry in _passes(game)] == [0, 1]
    assert len({entry[1] for entry in _passes(game)}) == 1


def test_empty_end_step_offers_both_players_priority_before_cleanup():
    game = _synthetic_game()
    # Establish the preceding step without simulating any complete game.
    game._step = TurnStep.POSTCOMBAT_MAIN
    game.advance_step()
    assert game.step is TurnStep.END_STEP

    _drain_ordinary_step_priority(game, PassOnlyPilot())

    assert game.step is TurnStep.END_STEP
    assert game.priority_state is None
    assert [entry[0] for entry in _passes(game)] == [0, 1]
    assert any(event["event"] == "priority_window_passed" for event in game.events)


def test_existing_open_empty_window_is_not_reopened():
    game = _synthetic_game()
    game.advance_step()
    game._begin_priority_window(allow_empty=True)
    epoch = game.priority_state.epoch
    openings_before = sum(
        event["event"] == "response_window_opened" for event in game.events
    )

    _drain_ordinary_step_priority(game, PassOnlyPilot())

    openings_after = sum(
        event["event"] == "response_window_opened" for event in game.events
    )
    assert openings_after == openings_before
    assert {entry[1] for entry in _passes(game)} == {epoch}


def test_empty_window_does_not_create_stack_objects():
    game = _synthetic_game()
    game._step = TurnStep.POSTCOMBAT_MAIN
    game.advance_step()
    objects_before = set(game._objects)

    _drain_ordinary_step_priority(game, PassOnlyPilot())

    assert set(game._objects) == objects_before
    assert game.stack == []
    assert game.priority_state is None


ATTACKER = CardFact(
    "Synthetic Attacker", "{1}{W}", 2, "Creature — Human", power=2, toughness=2
)
BLOCKER = CardFact(
    "Synthetic Blocker", "{1}{W}", 2, "Creature — Human", power=1, toughness=3
)


def _declared_attacker_game():
    game = _synthetic_game()
    attacker = game.create_permanent(ATTACKER, 0, summoning_sick=False)
    game.create_permanent(BLOCKER, 1, summoning_sick=False)
    game.advance_step()
    _drain_ordinary_step_priority(game, PassOnlyPilot())
    game.advance_step()
    attack = next(
        option
        for option in game.legal_attack_options(0)
        if option.attacker_ids == (attacker.object_id,)
    )
    game.execute_attack_action(attack)
    return game, attack


def test_attacker_declaration_waits_for_both_players_to_pass():
    game, attack = _declared_attacker_game()

    assert game.step is TurnStep.DECLARE_ATTACKERS
    assert game._attackers_declared
    assert game.legal_block_options(attack, 1) == ()

    before = len(_passes(game))
    _drain_ordinary_step_priority(game, PassOnlyPilot())
    assert game.step is TurnStep.DECLARE_ATTACKERS
    assert [entry[0] for entry in _passes(game)[before:]] == [0, 1]

    game.advance_step()
    assert game.step is TurnStep.DECLARE_BLOCKERS
    assert game.legal_block_options(attack, 1)


def test_blocker_declaration_and_sneak_decline_preserve_priority_before_damage():
    game, attack = _declared_attacker_game()
    _drain_ordinary_step_priority(game, PassOnlyPilot())
    game.advance_step()

    block = next(
        option for option in game.legal_block_options(attack, 1) if option.blocks
    )
    game.execute_block_action(block)
    assert game.step is TurnStep.DECLARE_BLOCKERS
    assert game._blockers_declared

    sneak_pass = next(
        option
        for option in game.legal_sneak_actions(0)
        if option.kind is ActionKind.PASS
    )
    assert game.execute_sneak_action(sneak_pass)
    assert game.step is TurnStep.DECLARE_BLOCKERS

    before = len(_passes(game))
    _drain_ordinary_step_priority(game, PassOnlyPilot())
    assert [entry[0] for entry in _passes(game)[before:]] == [0, 1]
    assert game.step is TurnStep.DECLARE_BLOCKERS

    game.advance_step()
    assert game.step is TurnStep.COMBAT_DAMAGE


def test_legacy_combat_adapter_keeps_explicit_diagnostic_transitions():
    game = _synthetic_game()
    attacker = game.create_permanent(ATTACKER, 0, summoning_sick=False)
    game.create_permanent(BLOCKER, 1, summoning_sick=False)
    game.advance_step()
    game.advance_step()

    game.combat([attacker], blocks={})

    assert game.step is TurnStep.END_OF_COMBAT
    assert game._combat_damage_resolved
    assert game.priority_state is None


def test_postcombat_main_has_ordinary_priority_before_end_step():
    game = _synthetic_game()
    # Isolate a transition; do not execute any complete game.
    game._step = TurnStep.END_OF_COMBAT
    game.advance_step()
    assert game.step is TurnStep.POSTCOMBAT_MAIN

    _drain_ordinary_step_priority(game, PassOnlyPilot())

    assert game.step is TurnStep.POSTCOMBAT_MAIN
    assert [entry[0] for entry in _passes(game)] == [0, 1]
    assert game.priority_state is None


def test_defending_player_receives_priority_before_block_choices():
    game, attack = _declared_attacker_game()
    assert game.step is TurnStep.DECLARE_ATTACKERS
    assert game.legal_block_options(attack, 1) == ()

    _drain_ordinary_step_priority(game, PassOnlyPilot())
    passes = _passes(game)
    assert [player for player, _epoch in passes] == [0, 1]

    game.advance_step()
    assert game.step is TurnStep.DECLARE_BLOCKERS
    assert game.legal_block_options(attack, 1)
