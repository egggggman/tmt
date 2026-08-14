from dataclasses import FrozenInstanceError

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
)
from tmnt_design_studio.pilot07 import AcceptancePilot, PassingPilot

PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Bear", "{1}{W}", 2, "Creature — Bear", power=2, toughness=2)
FLYER = CardFact(
    "Unimplemented Flyer",
    "{1}{W}",
    2,
    "Creature — Bird",
    "Flying",
    power=2,
    toughness=2,
    keywords=("Flying",),
)


def game(seed=1):
    deck = [PLAINS] * 30 + [BEAR] * 30
    return Game((deck, deck), seed=seed)


def prepared_main_game():
    current = game()
    current.begin_turn()
    current.create_permanent(PLAINS, 0, summoning_sick=False)
    current.create_permanent(PLAINS, 0, summoning_sick=False)
    current.set_hand_for_testing(0, [BEAR])
    return current


def test_pilot_receives_immutable_views_and_engine_generated_legal_options():
    current = prepared_main_game()
    view = current.public_view()
    options = current.legal_main_actions(0)

    assert options
    assert all(isinstance(option, ActionOption) for option in options)
    assert any(option.kind is ActionKind.CAST for option in options)
    assert not hasattr(view, "players")
    with pytest.raises(FrozenInstanceError):
        view.turn = 99
    with pytest.raises(TypeError):
        view.hands[0][0] = ("fabricated", "Bear", 2, True)


def test_pilot_cannot_make_illegal_or_fabricated_action_legal():
    current = prepared_main_game()
    real = next(
        option for option in current.legal_main_actions(0) if option.kind is ActionKind.CAST
    )
    fabricated = ActionOption(ActionKind.CAST, 0, object_id="object-999999")
    illegal_target = ActionOption(
        ActionKind.CAST,
        0,
        object_id=real.object_id,
        target_id=current.players[1].library[-1].object_id,
    )
    before = current.snapshot()

    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_main_action(fabricated)
    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_main_action(illegal_target)
    assert current.snapshot() == before


def test_bad_but_legal_pilot_choice_is_permitted_without_mutation():
    current = prepared_main_game()
    pilot = PassingPilot()
    options = current.legal_main_actions(0)
    chosen = pilot.choose_main_action(current.public_view(), options, "creature")
    before = current.snapshot()

    assert chosen.kind is ActionKind.PASS
    assert current.execute_main_action(chosen)
    assert current.snapshot() == before


def test_rules_legality_is_unchanged_when_pilot_strategy_changes():
    current = prepared_main_game()
    view = current.public_view()
    before = current.legal_main_actions(0)

    AcceptancePilot().choose_main_action(view, before, "creature")
    PassingPilot().choose_main_action(view, before, "creature")

    assert current.legal_main_actions(0) == before


def test_card_interpretation_is_pure_and_does_not_depend_on_pilot():
    interpreter = CardInterpreter()
    before = interpreter.cast_program(BEAR)

    AcceptancePilot()
    PassingPilot()

    assert before.kind is CastKind.CREATURE
    assert interpreter.cast_program(BEAR) == before
    assert not hasattr(interpreter, "pilot")
    assert not hasattr(interpreter, "players")


def test_card_interpreter_derives_constructs_from_oracle_not_pilot_or_card_name():
    interpreter = CardInterpreter()
    renamed = CardFact(
        "Any Rules Name",
        "{1}{W}",
        2,
        "Instant",
        "Any Rules Name deals 3 damage to target creature.",
    )
    assert interpreter.cast_program(renamed).kind is CastKind.DAMAGE_3_OPPOSING_CREATURE


def test_unsupported_oracle_semantics_stay_explicit_not_approximated():
    current = game()
    current.begin_turn()
    current.create_permanent(PLAINS, 0, summoning_sick=False)
    current.create_permanent(PLAINS, 0, summoning_sick=False)
    current.set_hand_for_testing(0, [FLYER])
    cast = next(
        option for option in current.legal_main_actions(0) if option.kind is ActionKind.CAST
    )

    assert current.execute_main_action(cast)
    event = next(event for event in current.events if event["event"] == "unsupported_semantics")
    assert event["card"] == FLYER.name
    assert event["oracle_fragment"] == "Flying"
    assert event["reason"] == "oracle_ability_not_implemented"


def test_combat_options_are_engine_legal_and_pilot_cannot_fabricate_participants():
    current = game()
    current.begin_turn()
    attacker = current.create_permanent(BEAR, 0, summoning_sick=False)
    blocker = current.create_permanent(BEAR, 1, summoning_sick=False)
    attack = max(current.legal_attack_options(0), key=lambda option: len(option.attacker_ids))
    blocks = max(current.legal_block_options(attack, 1), key=lambda option: len(option.blocks))

    assert attack.attacker_ids == (attacker.object_id,)
    assert blocks.blocks == ((attacker.object_id, blocker.object_id),)
    fake_attack = ActionOption(ActionKind.DECLARE_ATTACKERS, 0, attacker_ids=("object-999999",))
    with pytest.raises(ValueError, match="attack option is not currently legal"):
        current.execute_combat_actions(fake_attack, blocks)
    assert not attacker.tapped


def test_counter_pt_sba_and_identity_mutation_remain_engine_owned():
    current = game()
    target = current.create_permanent(BEAR, 0, summoning_sick=False)
    current.place_counters(target, "+1/+1", 1, source_card="Test", oracle_fragment="Test counter")
    current.apply_pt_modifier(
        target,
        1,
        0,
        duration="until_end_of_turn",
        source_card="Test",
        oracle_fragment="Test modifier",
    )
    target.damage = target.toughness
    current.check_state_based_actions()

    assert target.zone == "former"
    graveyard = current.players[0].graveyard[-1]
    assert graveyard.object_id != target.object_id
    assert graveyard.card is BEAR
    assert all(
        option.kind
        in {
            ActionKind.PLAY_LAND,
            ActionKind.CAST,
            ActionKind.DECLARE_ATTACKERS,
            ActionKind.DECLARE_BLOCKERS,
            ActionKind.PASS,
        }
        for option in current.legal_main_actions(0)
    )


def test_engine_choice_hooks_expose_immutable_ids_not_runtime_objects():
    observed = []
    current = Game(
        ([PLAINS] * 30 + [BEAR] * 30, [PLAINS] * 30 + [BEAR] * 30),
        counter_target_chooser=lambda player, source_id, candidates: (
            observed.append((player, source_id, candidates)) or candidates[0]
        ),
    )
    ally = CardFact(
        "Counter Ally",
        "{1}{W}",
        2,
        "Creature — Bear",
        "Alliance — Whenever another creature you control enters, put a +1/+1 counter on "
        "target creature you control.",
        power=2,
        toughness=2,
    )
    source = current.create_permanent(ally, 0, summoning_sick=False)
    entering = current.create_permanent(BEAR, 0)

    current.resolve_creature_entered_counter_effects(entering)

    assert observed
    _, source_id, candidates = observed[0]
    assert source_id == source.object_id
    assert all(isinstance(object_id, str) for object_id in candidates)


def test_legal_option_generation_is_deterministic():
    first = prepared_main_game()
    second = prepared_main_game()
    assert first.public_view() == second.public_view()
    assert first.legal_main_actions(0) == second.legal_main_actions(0)
