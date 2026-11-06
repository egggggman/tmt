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
    openings_before = sum(event["event"] == "response_window_opened" for event in game.events)

    _drain_ordinary_step_priority(game, PassOnlyPilot())

    openings_after = sum(event["event"] == "response_window_opened" for event in game.events)
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
