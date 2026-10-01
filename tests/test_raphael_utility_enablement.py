from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter, CastKind
from tmnt_design_studio.engine07 import CardFact, Game
from tmnt_design_studio.pilot07 import AcceptancePilot

LAND = CardFact("Mountain", "", 0, "Basic Land — Mountain")
CREATURE = CardFact("Test Turtle", "{1}{R}", 2, "Creature — Turtle", power=2, toughness=2)
SKATEBOARD = CardFact(
    "Skateboard",
    "{1}",
    1,
    "Artifact — Equipment",
    "When this Equipment enters, tap target permanent.\n"
    "Equipped creature gets +1/+0 and has haste.\n"
    "Equip {1} ({1}: Attach to target creature you control. Equip only as a sorcery.)",
)
PIZZA = CardFact(
    "Spicy Oatmeal Pizza",
    "{2}{R}",
    3,
    "Artifact — Food",
    "When this artifact enters, it deals 4 damage to any target and 3 damage to you.\n"
    "{2}, {T}, Sacrifice this artifact: You gain 3 life.",
)


def game():
    current = Game(([LAND] * 60, [LAND] * 60), seed=41)
    current.begin_turn()
    return current


def resolve(current):
    if current.priority_state is None:
        current._begin_priority_window()
    for _ in range(2):
        player = current.priority_state.player_index
        current.execute_priority_action(current.legal_priority_actions(player)[0])
    current.process_priority_resolution()


def test_interpreter_recognizes_utility_cards_and_equip():
    interpreter = CardInterpreter()
    assert interpreter.cast_program(SKATEBOARD).kind is CastKind.PERMANENT
    assert interpreter.cast_program(PIZZA).kind is CastKind.PERMANENT
    equip = interpreter.activated_ability_semantics(
        SKATEBOARD, SKATEBOARD.oracle_text.splitlines()[2]
    )
    assert equip is not None and equip.coverage.fully_supported
    assert equip.program.effect_kind is ActivatedEffectKind.ATTACH_EQUIPMENT


def test_skateboard_cast_and_deterministic_equip():
    current = game()
    lands = [current.create_permanent(LAND, 0, summoning_sick=False) for _ in range(2)]
    creature = current.create_permanent(CREATURE, 0, summoning_sick=False)
    current.players[0].battlefield = [*lands, creature]
    current.players[0].hand = current.set_hand_for_testing(0, [SKATEBOARD])
    option = next(
        item
        for item in current.legal_main_actions(0)
        if item.object_id == current.players[0].hand[0].object_id
    )
    current.execute_main_action(option)
    equipment = next(item for item in current.players[0].battlefield if item.card is SKATEBOARD)
    assert any(
        event["event"] == "permanent_resolved" and event["card"] == "Skateboard"
        for event in current.events
    )
    equip_option = next(
        item
        for item in current.legal_main_actions(0)
        if item.object_id == equipment.object_id and item.target_id == creature.object_id
    )
    current.execute_main_action(equip_option)
    resolve(current)
    assert equipment.attached_to == creature.object_id
    assert any(event["event"] == "equipment_attached" for event in current.events)


def test_pizza_cast_and_food_activation():
    current = game()
    lands = [current.create_permanent(LAND, 0, summoning_sick=False) for _ in range(5)]
    current.players[0].battlefield = lands
    current.players[0].hand = current.set_hand_for_testing(0, [PIZZA])
    option = next(
        item
        for item in current.legal_main_actions(0)
        if item.object_id == current.players[0].hand[0].object_id
    )
    current.execute_main_action(option)
    pizza = next(item for item in current.players[0].battlefield if item.card is PIZZA)
    before = current.players[0].life
    activation = next(
        item for item in current.legal_main_actions(0) if item.object_id == pizza.object_id
    )
    current.execute_main_action(activation)
    resolve(current)
    assert current.players[0].life == before + 3
    assert any(event["event"] == "activated_ability_resolved" for event in current.events)


def test_acceptance_pilot_selects_utility_when_no_creature_has_priority():
    current = game()
    land = current.create_permanent(LAND, 0, summoning_sick=False)
    current.players[0].battlefield = [land]
    current.players[0].hand = current.set_hand_for_testing(0, [SKATEBOARD])
    options = current.legal_main_actions(0)
    choice = AcceptancePilot().choose_main_action(current.pilot_view(0), options, "creature")
    assert choice.object_id == current.players[0].hand[0].object_id
