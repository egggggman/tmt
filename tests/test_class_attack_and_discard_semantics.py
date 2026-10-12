"""Class level, attack loot, discard damage, and search timing with renamed fixtures."""

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, RulesEventKind, TriggerEffect, TurnStep

LAND = CardFact("Mountain", "", 0, "Basic Land — Mountain")
BEAR = CardFact("Bearer", "{1}{R}", 2, "Creature — Bear", power=2, toughness=2)
CLASS = CardFact(
    "Generic Class",
    "{1}{R}",
    2,
    "Enchantment — Class",
    "(Gain the next level as a sorcery to add its ability.)\n"
    "Whenever you attack, you may discard a card. If you do, draw a card.\n"
    "{1}{R}: Level 2\n"
    "Whenever you discard a card, this Class deals 2 damage to each opponent.\n"
    "{1}{R}: Level 3\n"
    "When this Class becomes level 3, search your library for a card, put it into your hand, "
    "shuffle, then discard a card at random.",
)


def setup(seed=74):
    game = Game(
        ([LAND, BEAR] * 20, [LAND] * 40),
        seed=seed,
        discard_draw_chooser=lambda _view, options: next(
            option for option in options if option.card_id is not None
        ),
    )
    game.begin_turn()
    game.set_hand_for_testing(0, [BEAR, LAND])
    for _ in range(4):
        game.create_permanent(LAND, 0, summoning_sick=False)
    source = game.create_permanent(CLASS, 0)
    attacker = game.create_permanent(BEAR, 0, summoning_sick=False)
    return game, source, attacker


def resolve(game):
    for _ in range(2):
        game.execute_priority_action(
            game.legal_priority_actions(game.priority_state.player_index)[0]
        )
    game.process_priority_resolution()


def test_class_interpretation_is_complete_without_name_dispatch():
    interpreter = CardInterpreter()
    assert interpreter.unsupported_fragments(CLASS) == ()
    for fragment in interpreter.fragments(CLASS):
        if fragment.endswith("Level 2") or fragment.endswith("Level 3"):
            assert interpreter.activated_ability_semantics(CLASS, fragment).coverage.fully_supported


def test_attacking_with_class_loots_then_level_two_discard_deals_damage():
    game, source, attacker = setup()
    game.activate_ability(0, source, "{1}{R}: Level 2")
    resolve(game)
    assert source.class_level == 2 and not game.stack
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    game.resolve_attack_pt_effects([attacker])
    assert game.stack[-1].effect is TriggerEffect.DISCARD_DRAW
    resolve(game)
    assert game.stack[-1].effect is TriggerEffect.CLASS_DISCARD_DAMAGE
    resolve(game)
    assert game.players[1].life == 18
    assert any(e.kind is RulesEventKind.CARD_DISCARDED for e in game._rules_events.values())
    game.check_invariants()


def test_level_three_search_shuffles_and_discards_at_random_with_deterministic_replay():
    def run():
        game, source, _ = setup()
        game.activate_ability(0, source, "{1}{R}: Level 2")
        resolve(game)
        # The first activation spent two sources; the other two can pay the next level.
        game.activate_ability(0, source, "{1}{R}: Level 3")
        resolve(game)
        assert game.stack[-1].effect is TriggerEffect.CLASS_LEVEL_THREE_SEARCH
        resolve(game)
        assert game.stack[-1].effect is TriggerEffect.CLASS_DISCARD_DAMAGE
        resolve(game)
        game.check_invariants()
        return game.snapshot(), game.events, game.rng.records

    assert run() == run()


def test_discard_damage_trigger_survives_class_departure_and_does_not_trigger_at_level_one():
    game, source, _ = setup()
    card = game.players[0].hand[0]
    game.move_object(card, "graveyard", reason="test_discard")
    assert not any(e.kind is RulesEventKind.CARD_DISCARDED for e in game._rules_events.values())
    game.activate_ability(0, source, "{1}{R}: Level 2")
    resolve(game)
    game.move_object(game.players[0].hand[0], "graveyard", reason="test_discard")
    game._put_pending_triggers_on_stack()
    assert game.stack[-1].effect is TriggerEffect.CLASS_DISCARD_DAMAGE
    game.destroy(source)
    game._begin_priority_window()
    resolve(game)
    assert game.players[1].life == 18
    game.check_invariants()
