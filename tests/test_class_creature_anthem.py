"""Generic Class level-two creature bonuses and granted menace."""

from dataclasses import replace

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TurnStep

SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
BEAR = CardFact("Bear", "{1}{B}", 2, "Creature — Bear", power=2, toughness=2)
LEVEL = "{1}{B}: Level 2"
ANTHEM = "Creatures you control get +1/+0 and have menace."
CLASS = CardFact(
    "Example Class",
    "{2}{B}",
    3,
    "Enchantment — Class",
    "(Gain the next level as a sorcery to add its ability.)\n"
    f"{LEVEL}\n{ANTHEM}\n{{B}}: Level 3\n"
    "Creature cards in your graveyard have sneak {3}{B}.\n"
    "You may cast creature spells from your graveyard using their sneak abilities.",
)
AURA = CardFact(
    "Fixture Mutation",
    "{1}{B}",
    2,
    "Enchantment — Aura",
    "Enchant creature\nEnchanted creature is a Turtle with base power and toughness "
    "0/1. It can't attack and loses all abilities. (It also loses all other creature types.)",
)


def setup(seed=401):
    game = Game(([SWAMP] * 20, [SWAMP] * 20), seed=seed)
    game.begin_turn()
    for _ in range(2):
        game.create_permanent(SWAMP, 0, summoning_sick=False)
    source = game.create_permanent(CLASS, 0)
    attacker = game.create_permanent(BEAR, 0, summoning_sick=False)
    return game, source, attacker


def resolve(game):
    for _ in range(2):
        game.execute_priority_action(
            game.legal_priority_actions(game.priority_state.player_index)[0]
        )
    game.process_priority_resolution()


def level_two(game, source):
    assert game.activate_ability(0, source, LEVEL)
    resolve(game)


def test_complete_clause_and_incomplete_class_levels_are_distinct():
    interpreter = CardInterpreter()
    assert interpreter.class_level_child(CLASS, 2) == ANTHEM
    assert interpreter.activated_ability_semantics(CLASS, LEVEL).coverage.fully_supported
    assert interpreter.class_creature_anthem(CLASS, ANTHEM) == (1, 0, "menace")
    unsupported = interpreter.unsupported_fragments(CLASS)
    assert ANTHEM not in {fragment for fragment, _ in unsupported}
    assert "{B}: Level 3" in {fragment for fragment, _ in unsupported}
    incomplete = replace(
        CLASS, oracle_text=CLASS.oracle_text.replace(ANTHEM, ANTHEM + " Draw a card.")
    )
    assert interpreter.class_level_child(incomplete, 2) is None
    assert not interpreter.activated_ability_semantics(incomplete, LEVEL).coverage.fully_supported
    misplaced = replace(
        CLASS,
        oracle_text=CLASS.oracle_text.replace(
            f"{LEVEL}\n{ANTHEM}\n{{B}}: Level 3",
            f"{LEVEL}\n{{B}}: Level 3\n{ANTHEM}",
        ),
    )
    assert interpreter.class_level_child(misplaced, 2) is None
    assert not interpreter.activated_ability_semantics(misplaced, LEVEL).coverage.fully_supported
    assert ANTHEM in {fragment for fragment, _ in interpreter.unsupported_fragments(misplaced)}
    assert interpreter.class_level_child(replace(CLASS, name="Renamed Class"), 2) == ANTHEM


def test_cost_timing_priority_and_level_state_control_bonus():
    game, source, attacker = setup()
    assert game.activation_payment_plan(0, source, LEVEL) is not None
    assert attacker.power == 2 and not game._has_menace(attacker)
    game.players[0].battlefield[0].tapped = True
    assert game.activation_payment_plan(0, source, LEVEL) is None
    game.players[0].battlefield[0].tapped = False
    assert game.activate_ability(0, source, LEVEL)
    assert attacker.power == 2 and source.class_level == 1
    resolve(game)
    assert source.class_level == 2 and attacker.power == 3 and attacker.toughness == 2
    assert game._has_menace(attacker)
    assert game.activation_payment_plan(0, source, LEVEL) is None
    assert game.activation_payment_plan(0, source, "{B}: Level 3") is None
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    assert game.activation_payment_plan(0, source, LEVEL) is None
    game.check_invariants()


def test_granted_menace_changes_legal_combat_assignments_and_damage():
    game, source, attacker = setup()
    one = game.create_permanent(BEAR, 1)
    two = game.create_permanent(BEAR, 1)
    level_two(game, source)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(option for option in game.legal_attack_options(0) if option.attacker_ids)
    game.execute_attack_action(attack)
    options = game.legal_block_options(attack, 1)
    assert all(len(option.blocks) != 1 for option in options)
    assert any(
        {blocker for _, blocker in option.blocks} == {one.object_id, two.object_id}
        for option in options
    )
    game.execute_block_action(next(option for option in options if not option.blocks))
    game.resolve_combat_damage()
    assert game.players[1].life == 17
    game.check_invariants()


def test_stackable_sources_new_entries_control_changes_and_source_exit():
    game, source, attacker = setup()
    other = game.create_permanent(CLASS, 0)
    for _ in range(2):
        game.create_permanent(SWAMP, 0, summoning_sick=False)
    level_two(game, source)
    level_two(game, other)
    assert attacker.power == 4
    newcomer = game.move_object(game.set_hand_for_testing(0, [BEAR])[0], "battlefield")
    assert newcomer.power == 4 and game._has_menace(newcomer)
    game.change_controller(attacker, 1)
    game.refresh_static_pt_modifiers()
    assert attacker.power == 2 and not game._has_menace(attacker)
    game.change_controller(attacker, 0)
    game.refresh_static_pt_modifiers()
    assert attacker.power == 4 and game._has_menace(attacker)
    game.move_object(source, "exile")
    game.check_state_based_actions()
    assert attacker.power == 3 and game._has_menace(attacker)
    game.move_object(other, "hand")
    game.check_state_based_actions()
    assert attacker.power == 2 and not game._has_menace(attacker)


def test_ability_loss_timestamp_removes_granted_keyword_but_not_power_modifier():
    game, source, attacker = setup()
    level_two(game, source)
    aura = game.create_permanent(AURA, 1)
    game.attach_aura(aura, attacker)
    assert (attacker.power, attacker.toughness) == (1, 1)
    assert not game._has_menace(attacker)
    game.move_object(aura, "graveyard")
    assert attacker.power == 3
    assert game._has_menace(attacker)

    # A creature Class losing its own abilities stops providing the same static rule.
    another = game.create_permanent(
        replace(CLASS, type_line="Enchantment Creature — Class", power=2, toughness=2), 0
    )
    for _ in range(2):
        game.create_permanent(SWAMP, 0, summoning_sick=False)
    level_two(game, another)
    assert attacker.power == 4
    second_aura = game.create_permanent(AURA, 1)
    game.attach_aura(second_aura, another)
    assert attacker.power == 3
    game.move_object(second_aura, "exile")
    assert attacker.power == 4


def test_source_departure_before_level_resolution_and_repeatable_event_history():
    def run():
        game, source, attacker = setup(seed=911)
        game.activate_ability(0, source, LEVEL)
        game.move_object(source, "graveyard")
        resolve(game)
        assert attacker.power == 2 and not game._has_menace(attacker)
        game.check_invariants()
        return game.snapshot(), game.events, game.rng.records

    assert run() == run()


def test_later_level_does_not_retimestamp_earlier_static_keyword_grant():
    third = replace(
        CLASS,
        oracle_text=CLASS.oracle_text.replace(
            "Creature cards in your graveyard have sneak {3}{B}.\n"
            "You may cast creature spells from your graveyard using their sneak abilities.",
            "When this Class becomes level 3, search your library for a card, "
            "put it into your hand, shuffle, then discard a card at random.",
        ),
    )
    game, original, attacker = setup()
    game.move_object(original, "graveyard")
    source = game.create_permanent(third, 0)
    level_two(game, source)
    aura = game.create_permanent(AURA, 1)
    game.attach_aura(aura, attacker)
    assert not game._has_menace(attacker)
    level_two_timestamp = source.class_level_timestamp
    game.create_permanent(SWAMP, 0, summoning_sick=False)
    assert game.activate_ability(0, source, "{B}: Level 3")
    resolve(game)
    assert source.class_level == 3
    assert source.class_level_timestamp == level_two_timestamp
    assert (attacker.power, attacker.toughness) == (1, 1)
    assert not game._has_menace(attacker)
    game.check_invariants()
