"""Generic full entry pump and untap through an authenticated creature target."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    ActionKind,
    CardFact,
    Game,
    TemporaryKeyword,
    TemporaryKeywordEffect,
    TriggerEffect,
    TurnStep,
    load_facts,
)

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Forest", "", 0, "Basic Land — Forest")
FRAGMENT = "When this artifact enters, target creature gets +2/+2 until end of turn. Untap it."
SOURCE = CardFact("Unnamed Food", "{G}", 1, "Artifact — Food", FRAGMENT)
CREATURE = CardFact("Target", "{1}", 1, "Creature", power=2, toughness=2)
HEXPROOF = replace(CREATURE, name="Protected", oracle_text="Hexproof", keywords=("Hexproof",))


def setup(*, chooser=None):
    game = Game(([LAND] * 35, [LAND] * 35), seed=342, counter_target_chooser=chooser)
    game.begin_turn()
    return game


def resolve(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                next(
                    o
                    for o in game.legal_priority_actions(game.priority_state.player_index)
                    if o.kind is ActionKind.PASS_PRIORITY
                )
            )


def entry(game, source=SOURCE):
    permanent = game.create_permanent(source, 0)
    game._process_creature_entered_triggers(permanent)
    return permanent


def test_complete_frozen_oracle_and_generic_grammar():
    path = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    frozen = load_facts(
        load_card_data(path, path.with_suffix(".manifest.json")),
        {"Guac & Marshmallow Pizza"},
    )["Guac & Marshmallow Pizza"]
    interpreter = CardInterpreter()
    assert interpreter.etb_target_creature_pump_untap(frozen, FRAGMENT) == (2, 2)
    assert (FRAGMENT, "oracle_ability_not_implemented") not in interpreter.unsupported_fragments(
        frozen
    )
    creature = replace(CREATURE, oracle_text=FRAGMENT.replace("artifact", "creature"))
    assert interpreter.etb_target_creature_pump_untap(creature, creature.oracle_text) == (2, 2)
    for text in (
        FRAGMENT.replace("Untap it.", ""),
        FRAGMENT.replace("until end of turn", ""),
        FRAGMENT + " Draw a card.",
        FRAGMENT.replace("+2/+2", "+0/+2"),
    ):
        assert interpreter.etb_target_creature_pump_untap(SOURCE, text) is None
    assert interpreter.etb_target_creature_pump_untap(CREATURE, FRAGMENT) is None


def test_frozen_cast_entry_priority_target_payment_modifier_untap_and_cleanup():
    path = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    frozen = load_facts(
        load_card_data(path, path.with_suffix(".manifest.json")),
        {"Guac & Marshmallow Pizza"},
    )["Guac & Marshmallow Pizza"]
    offered = []

    def choose(_controller, _source_id, options):
        offered.append(options)
        return options[-1]

    game = setup(chooser=choose)
    own = game.create_permanent(CREATURE, 0)
    enemy = game.create_permanent(CREATURE, 1)
    shielded = game.create_permanent(HEXPROOF, 1)
    enemy.tapped = True
    game.create_permanent(LAND, 0)
    game.set_hand_for_testing(0, [frozen])
    option = next(
        o for o in game.legal_main_actions(0) if o.object_id == game.players[0].hand[0].object_id
    )
    game.execute_main_action(option)
    resolve(game)
    assert set(offered[0]) == {own.object_id, enemy.object_id}
    assert shielded.object_id not in offered[0]
    assert enemy.power == 4 and enemy.toughness == 4 and not enemy.tapped
    assert any(e["event"] == "cost_paid" and e["card"] == frozen.name for e in game.events)
    assert any(
        e["event"] == "etb_pump_untap_resolved" and e["legal_target"] and e["untapped"]
        for e in game.events
    )
    game.advance_to(TurnStep.COMBAT_DAMAGE)
    game.resolve_combat_damage()
    game.advance_to(TurnStep.END_STEP)
    assert enemy.power == 4
    game.advance_to(TurnStep.CLEANUP)
    assert enemy.power == 2 and enemy.toughness == 2
    game.check_invariants()


def test_source_departure_target_departure_and_invalidation():
    game = setup()
    target = game.create_permanent(CREATURE, 1)
    target.tapped = True
    source = entry(game)
    assert game.stack[-1].effect is TriggerEffect.ETB_TARGET_CREATURE_PUMP_UNTAP
    game.move_object(source, "graveyard", reason="response")
    resolve(game)
    assert target.power == 4 and not target.tapped
    game.check_invariants()

    game = setup()
    target = game.create_permanent(CREATURE, 1)
    entry(game)
    game.move_object(target, "graveyard", reason="response")
    replacement = game.create_permanent(CREATURE, 1)
    resolve(game)
    assert replacement.power == 2
    assert any(
        e["event"] == "etb_pump_untap_resolved" and not e["legal_target"] for e in game.events
    )
    game.check_invariants()

    game = setup()
    target = game.create_permanent(CREATURE, 1)
    entry(game)
    target.type_line_override = "Artifact"
    resolve(game)
    assert target.power == 2
    game.check_invariants()

    game = setup()
    target = game.create_permanent(CREATURE, 1)
    entry(game)
    target.temporary_keyword_effects.append(
        TemporaryKeywordEffect(
            TemporaryKeyword.HEXPROOF, "until_end_of_turn", target.object_id, "gain hexproof"
        )
    )
    resolve(game)
    assert target.power == 2
    game.check_invariants()


def test_no_target_invalid_choice_and_forged_selection_fail_closed():
    game = setup()
    game.create_permanent(HEXPROOF, 1)
    entry(game)
    assert not game.stack
    assert any(e["event"] == "etb_pump_no_legal_target" for e in game.events)

    game = setup(chooser=lambda *_: "fabricated")
    game.create_permanent(CREATURE, 1)
    with pytest.raises(ValueError, match="listed creature"):
        entry(game)

    game = setup()
    game.create_permanent(CREATURE, 1)
    entry(game)
    game.stack[-1].target_id = "fabricated"
    with pytest.raises(AssertionError, match="invalid target provenance"):
        game.check_invariants()


def test_exact_replay_with_independent_target_permanent():
    def run():
        game = setup()
        target = game.create_permanent(CREATURE, 0)
        target.tapped = True
        entry(game)
        resolve(game)
        game.check_invariants()
        return game.snapshot(), game.events, target.power, target.tapped

    assert run() == run()
