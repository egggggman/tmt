"""Level-one Class attack targeting through the ordinary combat and stack paths."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TurnStep, load_facts

LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
CREATURE = CardFact("Sample Ninja", "{1}{W}", 2, "Creature — Ninja", power=2, toughness=2)
FRAGMENT = "Whenever you attack, put a +1/+1 counter on target attacking creature."
CLASS = CardFact(
    "Example Leadership",
    "{1}{W}",
    2,
    "Enchantment — Class",
    "(Gain the next level as a sorcery to add its ability.)\n" + FRAGMENT + "\n{2}{W}: Level 2\n"
    "Whenever a creature you control leaves the battlefield, if it had a counter on it, "
    "you gain 2 life.\n{3}{W}: Level 3\n"
    "Whenever you cast a spell, put a +1/+1 counter on each creature you control.",
)


def resolve(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def setup(seed=289):
    game = Game(([LAND] * 30, [LAND] * 30), seed=seed)
    game.begin_turn()
    source = game.create_permanent(CLASS, 0)
    first = game.create_permanent(CREATURE, 0, summoning_sick=False)
    second = game.create_permanent(CREATURE, 0, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    return game, source, first, second


def attack(game, ids):
    action = next(option for option in game.legal_attack_options(0) if option.attacker_ids == ids)
    game.execute_attack_action(action)


def test_parser_supports_complete_level_one_without_unlocking_later_levels():
    interpreter = CardInterpreter()
    assert interpreter.attack_target_counter(CLASS, FRAGMENT)
    assert FRAGMENT not in {fragment for fragment, _ in interpreter.unsupported_fragments(CLASS)}
    for level in ("{2}{W}: Level 2", "{3}{W}: Level 3"):
        assert not interpreter.activated_ability_semantics(CLASS, level).coverage.fully_supported
    assert not interpreter.attack_target_counter(
        replace(CLASS, oracle_text=CLASS.oracle_text.replace(FRAGMENT, FRAGMENT + " Draw a card.")),
        FRAGMENT + " Draw a card.",
    )
    moved = replace(
        CLASS,
        oracle_text=CLASS.oracle_text.replace(
            FRAGMENT + "\n{2}{W}: Level 2\n", "{2}{W}: Level 2\n" + FRAGMENT + "\n"
        ),
    )
    assert not interpreter.attack_target_counter(moved, FRAGMENT)
    assert interpreter.attack_target_counter(replace(CLASS, name="Other Leadership"), FRAGMENT)


def test_frozen_oracle_fixture_and_illegal_choice_fail_closed():
    catalog = Path(__file__).resolve().parents[1] / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    frozen = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")), {"Leader's Talent"}
    )["Leader's Talent"]
    assert frozen.oracle_text == CLASS.oracle_text
    assert CardInterpreter().attack_target_counter(frozen, FRAGMENT)
    game, _source, first, second = setup()
    game.counter_target_chooser = lambda _controller, _source_id, _offered: "invalid"
    with pytest.raises(ValueError, match="attacking creature"):
        attack(game, (first.object_id, second.object_id))
    assert not first.counters and not second.counters


def test_target_identity_is_bound_to_the_original_stack_selection():
    game, _source, first, second = setup(295)
    attack(game, (first.object_id, second.object_id))
    trigger = game.stack[-1]
    trigger.target_id = (
        second.object_id if trigger.target_id == first.object_id else first.object_id
    )
    with pytest.raises(ValueError, match="original provenance"):
        resolve(game)
    assert not first.counters and not second.counters


def test_target_choice_priority_and_source_departure():
    game, source, first, second = setup()
    game.counter_target_chooser = lambda _controller, _source, offered: second.object_id
    attack(game, (first.object_id, second.object_id))
    trigger = game.stack[-1]
    assert trigger.source_id == source.object_id
    assert trigger.target_id == second.object_id
    assert not second.counters
    with pytest.raises(ValueError, match="before all players pass"):
        game.resolve_top_of_stack()
    game.move_object(source, "graveyard")
    resolve(game)
    assert second.counters["+1/+1"] == 1 and first.counters.get("+1/+1", 0) == 0
    assert any(e["event"] == "attack_counter_resolved" and e["applied"] for e in game.events)
    game.check_invariants()


def test_invalid_target_and_ability_suppression():
    game, source, first, second = setup()
    attack(game, (first.object_id, second.object_id))
    target = game._objects[game.stack[-1].target_id]
    game.move_object(target, "graveyard")
    resolve(game)
    assert not target.counters
    assert any(e["event"] == "attack_counter_resolved" and not e["applied"] for e in game.events)
    game.check_invariants()

    suppressed, source, first, second = setup(290)
    source.ability_loss_timestamp = (9999, 9999)
    attack(suppressed, (first.object_id, second.object_id))
    assert not suppressed.stack
    suppressed.check_invariants()

    changed, source, first, second = setup(293)
    changed.change_controller(source, 1)
    attack(changed, (first.object_id, second.object_id))
    assert not changed.stack
    changed.check_invariants()

    retargeted, _source, first, second = setup(294)
    attack(retargeted, (first.object_id, second.object_id))
    target = retargeted._objects[retargeted.stack[-1].target_id]
    retargeted.change_controller(target, 1)
    resolve(retargeted)
    assert not target.counters
    assert any(
        e["event"] == "attack_counter_resolved" and not e["applied"] for e in retargeted.events
    )
    retargeted.check_invariants()


def test_empty_attack_and_deterministic_replay():
    def replay(seed):
        game, source, first, second = setup(seed)
        attack(game, (first.object_id, second.object_id))
        resolve(game)
        game.check_invariants()
        return game.events, game.snapshot()

    assert replay(291) == replay(291)
    game, _source, first, _second = setup(292)
    attack(game, ())
    assert not game.stack and not first.counters
    game.check_invariants()
