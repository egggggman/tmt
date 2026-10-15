"""Intervening-if end-step triggers share departure history and stack priority."""

from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, ScryOption, TriggerEffect, TurnStep

LAND = CardFact("Island", "", 0, "Basic Land — Island")
SCRY = (
    "Disappear — At the beginning of your end step, if a permanent left the battlefield "
    "under your control this turn, scry 1. (Look at the top card of your library. "
    "You may put that card on the bottom.)"
)
COUNTER = (
    "Disappear — At the beginning of your end step, if a permanent left the battlefield "
    "under your control this turn, put a +1/+1 counter on Test Hero."
)
SCOUT = CardFact("Test Scout", "{1}{U}", 2, "Creature — Mutant", SCRY, 1, 2)
HERO = CardFact("Test Hero", "{1}{G}", 2, "Creature — Ninja", COUNTER, 2, 2)


def game():
    result = Game(([LAND] * 25, [LAND] * 25), seed=812)
    result.begin_turn()
    return result


def end_step(result):
    result.advance_to(TurnStep.COMBAT_DAMAGE)
    result.resolve_combat_damage()
    result.advance_to(TurnStep.END_STEP)


def pass_priority(result):
    while result.priority_state is not None:
        if result.priority_state.resolution_pending:
            result.process_priority_resolution()
        else:
            result.execute_priority_action(
                result.legal_priority_actions(result.priority_state.player_index)[0]
            )


def test_complete_oracle_parse_and_nonmatching_followup_is_rejected():
    interpreter = CardInterpreter()
    assert interpreter.disappear_end_step(SCOUT, SCRY) == ("scry", 1)
    assert interpreter.disappear_end_step(HERO, COUNTER) == ("self_counter", 1)
    assert not interpreter.unsupported_fragments(SCOUT)
    assert not interpreter.unsupported_fragments(HERO)
    assert interpreter.disappear_end_step(replace(HERO, name="Other Hero"), COUNTER) is None
    assert interpreter.disappear_end_step(SCOUT, SCRY + " Draw a card.") is None
    assert interpreter.disappear_end_step(HERO, COUNTER + " Draw a card.") is None


def test_end_step_checks_departure_controller_even_when_source_arrived_later():
    result = game()
    stolen = result.create_permanent(LAND, 1, controller=0)
    result.move_object(stolen, "hand")
    scout = result.create_permanent(SCOUT, 0)
    hero = result.create_permanent(HERO, 0)
    result.scry_chooser = lambda view, options: next(o for o in options if o.bottom_ids)
    top = result.players[0].library[-1]
    end_step(result)
    assert len(result.stack) == 2
    assert all(a.effect is TriggerEffect.DISAPPEAR_END_STEP for a in result.stack)
    assert not any(e["event"] == "scry_committed" for e in result.events)
    with pytest.raises(ValueError, match="all players pass"):
        result.resolve_top_of_stack()
    pass_priority(result)
    assert hero.counters["+1/+1"] == 1
    assert hero.power == 3
    assert result.players[0].library[0] is top
    assert scout.zone == "battlefield"
    checks = [e for e in result.events if e["event"] == "disappear_end_step_condition_checked"]
    assert len(checks) == 2
    result.check_invariants()


def test_no_history_or_opponents_history_does_not_trigger_and_next_turn_resets():
    result = game()
    result.create_permanent(SCOUT, 0)
    result.create_permanent(HERO, 0)
    result.move_object(result.create_permanent(LAND, 1), "graveyard")
    end_step(result)
    assert not result.stack
    result.advance_to(TurnStep.CLEANUP)
    result.begin_turn()
    assert not result._left_under_control_this_turn(0)
    result.check_invariants()


def test_source_departure_and_control_change_after_stacking_preserve_controller():
    result = game()
    result.move_object(result.create_permanent(LAND, 0), "exile")
    scout = result.create_permanent(SCOUT, 0)
    hero = result.create_permanent(HERO, 0)
    end_step(result)
    result.change_controller(hero, 1)
    result.move_object(scout, "graveyard")
    pass_priority(result)
    assert hero.counters["+1/+1"] == 1
    assert any(e["event"] == "scry_committed" for e in result.events)
    checks = [e for e in result.events if e["event"] == "disappear_end_step_condition_checked"]
    assert all(e["controller"] == 0 for e in checks)
    result.check_invariants()


def test_self_counter_does_not_follow_new_zone_object_and_rechecks_condition():
    result = game()
    result.move_object(result.create_permanent(LAND, 0), "graveyard")
    hero = result.create_permanent(HERO, 0)
    end_step(result)
    result.move_object(hero, "graveyard")
    replacement = result.create_permanent(HERO, 0)
    pass_priority(result)
    assert replacement.counters.get("+1/+1", 0) == 0
    result.check_invariants()

    # Departure history is monotone during a real turn. Removing the logged
    # condition in a synthetic state proves the resolution guard is consulted.
    other = game()
    other.move_object(other.create_permanent(LAND, 0), "graveyard")
    other.create_permanent(SCOUT, 0)
    end_step(other)
    other.events[:] = [e for e in other.events if e["event"] != "permanent_departed"]
    pass_priority(other)
    assert any(
        e["event"] == "disappear_end_step_condition_checked" and not e["satisfied"]
        for e in other.events
    )
    assert not any(e["event"] == "scry_committed" for e in other.events)


def test_illegal_scry_choice_is_transactional_and_full_replay_matches():
    result = game()
    result.move_object(result.create_permanent(LAND, 0), "graveyard")
    result.create_permanent(SCOUT, 0)
    end_step(result)
    before = tuple(result.players[0].library)
    result.scry_chooser = lambda _view, _options: ScryOption(("forged",), ())
    with pytest.raises(ValueError, match="listed option"):
        pass_priority(result)
    assert tuple(result.players[0].library) == before

    def replay():
        candidate = game()
        candidate.move_object(candidate.create_permanent(LAND, 0), "graveyard")
        candidate.create_permanent(SCOUT, 0)
        candidate.create_permanent(HERO, 0)
        end_step(candidate)
        pass_priority(candidate)
        candidate.check_invariants()
        return candidate.snapshot()

    assert replay() == replay()
