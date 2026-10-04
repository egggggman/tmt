"""Execute Aura semantics using renamed fixtures as well as frozen card facts."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import (
    ActionKind,
    CardFact,
    CharacteristicEffect,
    CharacteristicLayer,
    CharacteristicOperation,
    Game,
    PowerToughnessSubLayer,
    TemporaryKeyword,
    TemporaryKeywordEffect,
)
from tmnt_design_studio.stage002 import _semantic_coverage, load_catalog

ROOT = Path(__file__).resolve().parents[1]
ROW = load_catalog(ROOT).resolve_name("Retro-Mutation")
AURA = CardFact(
    ROW.name,
    ROW.mana_cost,
    int(ROW.mana_value),
    ROW.type_line,
    ROW.oracle_text,
    keywords=ROW.keywords,
    oracle_id=ROW.oracle_id,
)
LAND = CardFact("Island", "", 0, "Basic Land — Island")
THREAT = CardFact(
    "Fixture threat",
    "{1}",
    1,
    "Legendary Artifact Creature — Robot Ninja",
    "Flying\nTrample\nLifelink\nFirst strike",
    4,
    5,
    ("Flying", "Trample", "Lifelink", "First strike"),
)


def setup():
    game = Game(([LAND] * 60, [LAND] * 60), seed=711)
    game.begin_turn()
    for side in (0, 1):
        for _ in range(12):
            game.create_permanent(LAND, side)
    target = game.create_permanent(THREAT, 1, summoning_sick=False)
    return game, target


def enchant(game, target, card=AURA):
    hand = game.set_hand_for_testing(0, [card])[0]
    spell = game.announce_spell(0, hand, target)
    assert spell is not None and spell.cast_kind is CastKind.AURA
    return game.resolve_top_of_stack()


def test_semantic_recognition_is_name_independent_and_coverage_is_executable():
    interpreter = CardInterpreter()
    renamed = replace(
        AURA,
        name="Unrelated fixture",
        oracle_text=AURA.oracle_text.replace("a Turtle", "a Frog").replace("0/1", "2/3"),
    )
    program = interpreter.aura_program(renamed)
    assert (program.creature_type, program.power, program.toughness) == ("Frog", 2, 3)
    assert not interpreter.unsupported_fragments(AURA)
    assert all(
        _semantic_coverage(interpreter, AURA, f, ())["fully_supported"]
        for f in interpreter.fragments(AURA)
    )
    assert (
        interpreter.cast_program(replace(AURA, oracle_text="Enchant artifact")).kind
        is CastKind.UNSUPPORTED
    )


def test_cast_requires_legal_target_and_resolves_with_attached_identity():
    game, target = setup()
    hand = game.set_hand_for_testing(0, [AURA])[0]
    before = game.authoritative_state_fingerprint()
    assert game.announce_spell(0, hand) is None
    assert game.announce_spell(0, hand, game.players[1].battlefield[0]) is None
    assert game.authoritative_state_fingerprint() == before
    aura = enchant(game, target)
    assert aura.attached_to == target.object_id
    assert target.type_line == "Legendary Artifact Creature — Turtle"
    assert (target.power, target.toughness) == (0, 1)
    assert target not in game.legal_attackers(1)
    assert not game._has_flying(target)
    assert not game.evaluated_trample(target)
    assert not game.evaluated_lifelink(target)
    assert not game.evaluated_strike_keywords(target)
    assert any(
        e["event"] == "aura_resolved" and e["target_id"] == target.object_id for e in game.events
    )


def test_layers_counters_temporary_modifiers_and_source_removal():
    game, target = setup()
    target.counters["+1/+1"] = 2
    game.apply_pt_modifier(
        target,
        3,
        0,
        duration="until_end_of_turn",
        source_card="Fixture boost",
        oracle_fragment="boost",
    )
    aura = enchant(game, target)
    assert (target.power, target.toughness) == (5, 3)
    game.add_characteristic_effect(
        target,
        CharacteristicEffect(
            "later-base",
            CharacteristicLayer.POWER_TOUGHNESS,
            PowerToughnessSubLayer.SET_BASE,
            CharacteristicOperation.SET,
            6,
            7,
            game._effect_timestamp(),
        ),
    )
    assert (target.power, target.toughness) == (11, 9)
    game.move_object(aura, "hand")
    assert target.ability_loss_timestamp is None
    assert target.type_line == THREAT.type_line
    assert game._has_flying(target)
    assert target in game.legal_attackers(1)
    assert (target.power, target.toughness) == (11, 9)


def test_retarget_and_overlapping_auras_do_not_restore_until_last_source_leaves():
    game, first = setup()
    second = game.create_permanent(replace(THREAT, name="Second fixture"), 1, summoning_sick=False)
    aura = enchant(game, first)
    another = enchant(game, first)
    timestamp = aura.attachment_timestamp
    game.attach_aura(aura, second)
    assert aura.attachment_timestamp > timestamp
    assert first.power == second.power == 0
    game.move_object(another, "exile")
    assert first.power == 4 and second.power == 0
    game.change_controller(second, 0)
    assert aura.controller == 0 and second.power == 0
    game.move_object(aura, "graveyard")
    assert second.power == 4


def test_target_leaves_and_returns_as_new_object_aura_goes_to_graveyard():
    game, target = setup()
    aura = enchant(game, target)
    returned = game.move_object(target, "hand")
    new_target = game.move_object(returned, "battlefield", controller=1)
    game.check_state_based_actions()
    assert aura.zone == "former"
    assert new_target.object_id != target.object_id and new_target.power == 4
    assert any(c.name == AURA.name for c in game.players[0].graveyard)


def test_target_becomes_illegal_before_resolution_and_on_battlefield():
    game, target = setup()
    hand = game.set_hand_for_testing(0, [AURA])[0]
    spell = game.announce_spell(0, hand, target)
    game.move_object(target, "hand")
    assert game.resolve_top_of_stack().zone == "graveyard"
    assert any(
        e["event"] == "aura_failed" and e["source_id"] == spell.object_id for e in game.events
    )
    target = game.create_permanent(THREAT, 1)
    aura = enchant(game, target)
    target.type_line_override = "Artifact"
    game.check_state_based_actions()
    assert aura.zone == "former" and target.ability_loss_timestamp is None


def test_ability_loss_suppresses_static_source_and_future_triggers():
    game, target = setup()
    lord = game.create_permanent(
        replace(
            THREAT,
            name="Fixture lord",
            oracle_text="Other artifact creatures you control get +2/+1.",
            keywords=(),
        ),
        1,
    )
    game.refresh_static_pt_modifiers()
    assert target.power == 6
    aura = enchant(game, lord)
    assert target.power == 4
    game.move_object(aura, "hand")
    assert target.power == 6
    watcher = game.create_permanent(
        replace(
            THREAT,
            name="Fixture watcher",
            oracle_text=(
                "Alliance — Whenever another creature you control enters, "
                "this creature gets +1/+0 until end of turn."
            ),
            keywords=(),
        ),
        1,
    )
    aura = enchant(game, watcher)
    before = len(game.events)
    entering = game.create_permanent(THREAT, 1)
    game.resolve_creature_entered_pt_effects(entering)
    assert not any(
        e.get("event") == "trigger_pending" and e.get("source") == watcher.card.name
        for e in game.events[before:]
    )
    assert watcher.power == 2  # 0 base plus the restored lord's layer-7c bonus.
    game.move_object(aura, "hand")
    restored_entry = game.create_permanent(THREAT, 1)
    game.resolve_creature_entered_pt_effects(restored_entry)
    assert watcher.power == 7  # Printed 4, lord +2, and the restored trigger +1.
    assert any(
        e.get("event") == "trigger_pending" and e.get("source") == watcher.card.name
        for e in game.events[before:]
    )


def test_keyword_grants_obey_layer_six_timestamp_and_restore_on_removal():
    game, target = setup()
    early = TemporaryKeywordEffect(
        TemporaryKeyword.REACH,
        "until_end_of_turn",
        target.object_id,
        "grant reach",
        game._effect_timestamp(),
    )
    target.temporary_keyword_effects.append(early)
    aura = enchant(game, target)
    assert not game._has_reach(target)
    target.temporary_keyword_effects.append(
        TemporaryKeywordEffect(
            TemporaryKeyword.FLYING,
            "until_end_of_turn",
            target.object_id,
            "grant flying",
            game._effect_timestamp(),
        )
    )
    assert game._has_flying(target)
    game.move_object(aura, "hand")
    assert game._has_reach(target)


def test_shroud_hexproof_and_unrepresented_dependencies_fail_closed():
    game, target = setup()
    target.card = replace(THREAT, keywords=("Hexproof",), oracle_text="Hexproof")
    assert not game.legal_aura_target(AURA, target, 0)
    assert game.legal_aura_target(AURA, target, 1)
    target.card = replace(THREAT, keywords=("Shroud",), oracle_text="Shroud")
    assert not game.legal_aura_target(AURA, target, 1)
    assert game.legal_aura_target(AURA, target, 1, targeted=False)
    target.card = replace(THREAT, keywords=(), oracle_text="Ward {2}")
    with pytest.raises(ValueError, match="dependency"):
        game.legal_aura_target(AURA, target, 0)


def test_flash_can_be_announced_by_nonactive_priority_holder():
    game, target = setup()
    hand = game.set_hand_for_testing(0, [THREAT])[0]
    game.announce_spell(0, hand)
    game._begin_priority_window()
    game.execute_priority_action(
        next(o for o in game.legal_priority_actions(0) if o.kind is ActionKind.PASS_PRIORITY)
    )
    game.set_hand_for_testing(1, [AURA])
    option = next(o for o in game.legal_priority_actions(1) if o.kind is ActionKind.CAST)
    game.execute_priority_action(option)
    assert game.stack[-1].cast_kind is CastKind.AURA
    while game.priority_state:
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
    assert target.power == 0


def test_repeated_refresh_is_idempotent_and_replay_is_deterministic():
    fingerprints = []
    for _ in range(2):
        game, target = setup()
        enchant(game, target)
        before = game.authoritative_state_fingerprint()
        events = list(game.events)
        game.refresh_static_pt_modifiers()
        game.refresh_static_pt_modifiers()
        assert game.events == events and game.authoritative_state_fingerprint() == before
        fingerprints.append(before)
    assert fingerprints[0] == fingerprints[1]


def test_activated_ability_is_removed_but_already_stacked_ability_still_resolves():
    game, _ = setup()
    fragment = "{1}: This creature gains first strike until end of turn."
    source = game.create_permanent(
        replace(THREAT, name="Fixture activator", oracle_text=fragment, keywords=()),
        0,
        summoning_sick=False,
    )
    assert game.activate_ability(0, source, fragment)
    # Attach through an existing resolving effect, leaving the older ability on the stack.
    aura = game.create_permanent(AURA, 1)
    game.attach_aura(aura, source)
    assert game.announce_activated_ability(0, source, fragment) is None
    assert game.activation_payment_plan(0, source, fragment) is None
    while game.priority_state:
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
    assert game.evaluated_strike_keywords(source)  # Later ability grant survives layer 6.


def test_dies_ability_is_absent_in_last_known_information():
    game, _ = setup()
    source = game.create_permanent(
        replace(
            THREAT,
            name="Fixture death",
            oracle_text="When this creature dies, draw a card.",
            keywords=(),
        ),
        1,
    )
    enchant(game, source)
    hand_size = len(game.players[1].hand)
    game.destroy(source)
    game.check_state_based_actions()
    assert not game.stack and len(game.players[1].hand) == hand_size


@pytest.mark.parametrize("aura_first", [True, False])
def test_simultaneous_aura_and_target_departure_uses_suppressed_last_known_abilities(aura_first):
    game, _ = setup()
    source = game.create_permanent(
        replace(
            THREAT,
            name="Fixture death",
            oracle_text="When this creature dies, draw a card.",
            keywords=(),
        ),
        1,
    )
    aura = enchant(game, source)
    hand_size = len(game.players[1].hand)
    batch = (aura, source) if aura_first else (source, aura)
    game.put_permanents_into_graveyard(batch)
    game.check_state_based_actions()
    assert not game.stack and len(game.players[1].hand) == hand_size


def test_flash_on_empty_stack_during_opponent_combat_and_nonflash_rejected():
    from tmnt_design_studio.engine07 import TurnStep

    game, target = setup()
    game.transition_to(TurnStep.BEGINNING_OF_COMBAT)
    game._begin_priority_window(allow_empty=True)
    game.execute_priority_action(
        next(o for o in game.legal_priority_actions(0) if o.kind is ActionKind.PASS_PRIORITY)
    )
    cards = game.set_hand_for_testing(
        1, [replace(AURA, oracle_text=AURA.oracle_text.replace("Flash\n", ""), keywords=()), AURA]
    )
    assert game.announce_spell(1, cards[0], target) is None
    options = game.legal_priority_actions(1)
    assert any(o.object_id == cards[1].object_id for o in options)
    choice = next(o for o in options if o.object_id == cards[1].object_id)
    game.execute_priority_action(choice)
    assert game.priority_state.player_index == 1


def test_suppression_before_damage_applies_sba_and_unattached_aura_is_cleaned_up():
    game, target = setup()
    target.damage = 1
    aura = enchant(game, target)
    assert target.zone == aura.zone == "former"
    assert len([x for x in game.players[0].graveyard if x.name == AURA.name]) == 1
