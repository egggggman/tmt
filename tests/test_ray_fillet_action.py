import pytest

from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game

LAND = CardFact("Plains", "", 0, "Basic Land — Plains", "({T}: Add {W}.)")
RAY = CardFact(
    "Ray Fillet, Man Ray",
    "{2}{U}",
    3,
    "Creature — Mutant",
    "{2}, Remove a +1/+1 counter from a creature you control: Draw a card.",
    2,
    2,
)
CREATURE = CardFact("Creature", "{1}", 1, "Creature", power=2, toughness=2)
FRAGMENT = RAY.oracle_text


def game(seed=2400):
    current = Game(([LAND] * 60, [LAND] * 60), seed=seed)
    current.begin_turn()
    return current


def pass_priority_and_resolve(current):
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            current.execute_priority_action(
                current.legal_priority_actions(current.priority_state.player_index)[0]
            )


def add_lands(current, count):
    return [current.create_permanent(LAND, 0, summoning_sick=False) for _ in range(count)]


def setup(*, lands=2, counter=1, target_controller=0, seed=2400):
    current = game(seed)
    add_lands(current, lands)
    source = current.create_permanent(RAY, 0, summoning_sick=False)
    target = current.create_permanent(CREATURE, target_controller, summoning_sick=False)
    target.counters["+1/+1"] = counter
    return current, source, target


def test_exact_ray_fillet_grammar_is_supported():
    semantics = CardInterpreter().activated_ability_semantics(RAY, FRAGMENT)
    assert semantics is not None and semantics.coverage.fully_supported
    assert semantics.program.effect_kind is ActivatedEffectKind.DRAW_CARD
    assert semantics.program.cost.remove_counter_target


def test_insufficient_mana_and_no_eligible_or_zero_counter_target_fail_closed():
    current, source, target = setup(lands=1)
    assert current.announce_activated_ability(0, source, FRAGMENT) is None
    assert not current.stack
    target.counters["+1/+1"] = 0
    current, source, _ = setup(lands=2, counter=0)
    assert current.announce_activated_ability(0, source, FRAGMENT) is None
    current, source, _ = setup(lands=2, target_controller=1)
    assert current.announce_activated_ability(0, source, FRAGMENT) is None


def test_payment_removes_exactly_one_counter_before_stack_placement():
    current, source, target = setup(counter=2)
    ability = current.announce_activated_ability(0, source, FRAGMENT)
    assert ability is not None and current.stack[-1] is ability
    assert ability.cost_target_id == target.object_id
    assert target.counters["+1/+1"] == 1
    assert all(land.tapped for land in current.players[0].battlefield if land.card.is_land)
    assert len(current.players[0].hand) == 7
    assert any(event["event"] == "counter_removed_as_activation_cost" for event in current.events)


def test_counter_cost_remains_spent_if_ability_leaves_stack_before_resolution():
    current, source, target = setup()
    ability = current.announce_activated_ability(0, source, FRAGMENT)
    assert ability is not None
    current.stack.remove(ability)
    ability.zone = "former"
    assert target.counters.get("+1/+1", 0) == 0
    assert len(current.players[0].hand) == 7


def test_stale_or_fabricated_cost_target_fails_closed():
    current, source, target = setup()
    ability = current.announce_activated_ability(0, source, FRAGMENT)
    assert ability is not None
    current._objects[ability.cost_target_id] = source
    with pytest.raises(ValueError, match="counter-cost target provenance"):
        current._resolve_activated_ability(ability)
    assert target.counters.get("+1/+1", 0) == 0


def test_draw_occurs_only_on_resolution_and_source_can_leave():
    current, source, target = setup()
    ability = current.announce_activated_ability(0, source, FRAGMENT)
    assert ability is not None
    assert len(current.players[0].hand) == 7
    current.put_into_graveyard(source)
    pass_priority_and_resolve(current)
    assert len(current.players[0].hand) == 8
    assert target.counters.get("+1/+1", 0) == 0
    assert any(event["event"] == "ray_fillets_draw_resolved" for event in current.events)


def test_cost_target_controller_and_identity_are_locked():
    selected = []

    def choose(player, source_id, ids):
        selected.append((player, source_id, ids))
        return ids[0]

    current = Game(([LAND] * 60, [LAND] * 60), seed=2401, counter_target_chooser=choose)
    current.begin_turn()
    add_lands(current, 2)
    source = current.create_permanent(RAY, 0, summoning_sick=False)
    target = current.create_permanent(CREATURE, 0, summoning_sick=False)
    opponent = current.create_permanent(CREATURE, 1, summoning_sick=False)
    target.counters["+1/+1"] = 1
    opponent.counters["+1/+1"] = 3
    ability = current.announce_activated_ability(0, source, FRAGMENT)
    assert ability is not None and ability.cost_target_id == target.object_id
    assert selected == [(0, source.object_id, (target.object_id,))]
    assert opponent.counters["+1/+1"] == 3
