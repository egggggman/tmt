import pytest

from tmnt_design_studio.engine07 import (
    CardFact,
    CharacteristicEffect,
    CharacteristicLayer,
    CharacteristicOperation,
    Game,
    PowerToughnessSubLayer,
    _ordered_characteristic_effects,
)

PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Bear", "{1}{W}", 2, "Creature — Bear", power=2, toughness=2)


def game() -> Game:
    deck = [PLAINS] * 60
    return Game((deck, deck), seed=84)


def effect(
    effect_id: str,
    sublayer: PowerToughnessSubLayer,
    operation: CharacteristicOperation,
    power: int = 0,
    toughness: int = 0,
    timestamp: tuple[int, int] = (0, 0),
    depends_on: tuple[str, ...] = (),
) -> CharacteristicEffect:
    return CharacteristicEffect(
        effect_id,
        CharacteristicLayer.POWER_TOUGHNESS,
        sublayer,
        operation,
        power,
        toughness,
        timestamp,
        depends_on,
        "Layer Test",
    )


def test_existing_counters_and_modifiers_flow_through_typed_modify_sublayer():
    current = game()
    permanent = current.create_permanent(BEAR, 0, summoning_sick=False)
    permanent.counters["+1/+1"] = 2
    current.apply_pt_modifier(
        permanent,
        3,
        0,
        duration="until_end_of_turn",
        source_card="Test",
        oracle_fragment="Test gets +3/+0 until end of turn.",
    )

    assert permanent.evaluate_power_toughness() == (7, 4)
    assert (permanent.power, permanent.toughness) == (7, 4)
    assert permanent.pt_modifiers[0].created_order > 0


def test_sublayers_apply_set_then_modify_then_switch_regardless_of_insertion_order():
    current = game()
    permanent = current.create_permanent(BEAR, 0, summoning_sick=False)
    switch = effect(
        "switch",
        PowerToughnessSubLayer.SWITCH,
        CharacteristicOperation.SWITCH,
    )
    modify = effect(
        "modify",
        PowerToughnessSubLayer.MODIFY,
        CharacteristicOperation.ADD,
        1,
        0,
    )
    set_base = effect(
        "set",
        PowerToughnessSubLayer.SET_BASE,
        CharacteristicOperation.SET,
        5,
        1,
    )
    for item in (switch, modify, set_base):
        current.add_characteristic_effect(permanent, item)

    assert permanent.evaluate_power_toughness() == (1, 6)


def test_timestamp_orders_independent_effects_within_one_sublayer():
    current = game()
    permanent = current.create_permanent(BEAR, 0, summoning_sick=False)
    later = effect(
        "later",
        PowerToughnessSubLayer.SET_BASE,
        CharacteristicOperation.SET,
        4,
        4,
        (2, 0),
    )
    earlier = effect(
        "earlier",
        PowerToughnessSubLayer.SET_BASE,
        CharacteristicOperation.SET,
        1,
        1,
        (1, 0),
    )
    current.add_characteristic_effect(permanent, later)
    current.add_characteristic_effect(permanent, earlier)

    assert permanent.evaluate_power_toughness() == (4, 4)


def test_declared_dependency_overrides_timestamp_order_within_a_sublayer():
    first = effect(
        "first",
        PowerToughnessSubLayer.SET_BASE,
        CharacteristicOperation.SET,
        3,
        3,
        (10, 0),
    )
    dependent = effect(
        "dependent",
        PowerToughnessSubLayer.SET_BASE,
        CharacteristicOperation.SET,
        5,
        5,
        (1, 0),
        ("first",),
    )

    assert [item.effect_id for item in _ordered_characteristic_effects([dependent, first])] == [
        "first",
        "dependent",
    ]


def test_cycle_and_wrong_sublayer_operation_are_rejected_without_state_corruption():
    cyclic_a = effect(
        "a",
        PowerToughnessSubLayer.MODIFY,
        CharacteristicOperation.ADD,
        depends_on=("b",),
    )
    cyclic_b = effect(
        "b",
        PowerToughnessSubLayer.MODIFY,
        CharacteristicOperation.ADD,
        depends_on=("a",),
    )
    with pytest.raises(ValueError, match="cyclic"):
        _ordered_characteristic_effects([cyclic_a, cyclic_b])

    current = game()
    permanent = current.create_permanent(BEAR, 0, summoning_sick=False)
    invalid = effect(
        "invalid",
        PowerToughnessSubLayer.SWITCH,
        CharacteristicOperation.ADD,
        1,
        0,
    )
    with pytest.raises(ValueError, match="does not match"):
        current.add_characteristic_effect(permanent, invalid)
    assert permanent.characteristic_effects == []
    assert (permanent.power, permanent.toughness) == (2, 2)


def test_layer_effects_reset_with_new_object_identity_after_zone_changes():
    current = game()
    permanent = current.create_permanent(BEAR, 0, summoning_sick=False)
    current.add_characteristic_effect(
        permanent,
        effect(
            "set",
            PowerToughnessSubLayer.SET_BASE,
            CharacteristicOperation.SET,
            5,
            5,
        ),
    )

    graveyard = current.put_into_graveyard(permanent)
    returned = current.move_object(graveyard, "battlefield", controller=0)

    assert returned.object_id != permanent.object_id
    assert returned.characteristic_effects == []
    assert (returned.power, returned.toughness) == (2, 2)
