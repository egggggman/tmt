"""C6: generic mana-value-gated Food creation after permanent removal."""

from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import CardFact, CardObject, Game

TAINTED = CardFact(
    "Conditional removal fixture",
    "{1}{B}{G}",
    3,
    "Instant",
    "Destroy target artifact or creature. If its mana value was 4 or less, create a Food token. "
    '(It\'s an artifact with "{2}, {T}, Sacrifice this token: You gain 3 life.")',
)
LAND = CardFact("Forest", "", 0, "Basic Land — Forest")
SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
ARTIFACT_4 = CardFact("Relic", "{4}", 4, "Artifact")
CREATURE_5 = CardFact("Bruiser", "{3}{G}{G}", 5, "Creature — Beast", power=5, toughness=5)
CREATURE_4 = CardFact("Bear", "{2}{G}{G}", 4, "Creature — Bear", power=4, toughness=4)
ENCHANTMENT = CardFact("Rune", "{2}{G}", 3, "Enchantment")


def ready(seed: int = 6001) -> Game:
    game = Game(([LAND] * 20, [LAND] * 20), seed=seed)
    game.begin_turn()
    for _ in range(2):
        game.create_permanent(LAND, 0, summoning_sick=False)
    game.create_permanent(SWAMP, 0, summoning_sick=False)
    return game


def foods(game: Game):
    return [p for p in game.players[0].battlefield if p.card.name == "Food"]


def test_interpreter_requires_complete_conditional_food_grammar():
    interpreter = CardInterpreter()
    assert interpreter.cast_program(TAINTED).kind is CastKind.CONDITIONAL_REMOVAL_TOKEN
    program = interpreter.conditional_removal_token_program(TAINTED)
    assert program is not None and program.executable
    assert program.mana_value_at_most == 4
    assert program.token_program.definition.type_line == "Artifact — Food"
    assert interpreter.unsupported_fragments(TAINTED) == ()

    incomplete = replace(TAINTED, oracle_text=TAINTED.oracle_text + " Draw a card.")
    assert interpreter.conditional_removal_token_program(incomplete) is None
    assert interpreter.cast_program(incomplete).kind is CastKind.UNSUPPORTED


@pytest.mark.parametrize("target_card", [ARTIFACT_4, CREATURE_4])
def test_value_at_or_below_threshold_creates_exactly_one_food(target_card):
    game = ready()
    target = game.create_permanent(target_card, 1, summoning_sick=False)
    card = game.set_hand_for_testing(0, [TAINTED])[0]

    assert game.cast(0, card, target)
    assert target.zone == "former"
    assert len(foods(game)) == 1
    event = next(e for e in game.events if e["event"] == "conditional_removal_token_resolved")
    assert event["target_mana_value"] == target_card.mana_value
    assert event["token_created"] is True
    assert event["ordering"] == ("removal", "conditional_token_creation")


def test_value_above_threshold_removes_without_food():
    game = ready(6002)
    target = game.create_permanent(CREATURE_5, 1, summoning_sick=False)
    card = game.set_hand_for_testing(0, [TAINTED])[0]

    assert game.cast(0, card, target)
    assert target.zone == "former"
    assert not foods(game)
    event = next(e for e in game.events if e["event"] == "conditional_removal_token_resolved")
    assert event["target_mana_value"] == 5
    assert event["token_created"] is False


def test_resolution_rechecks_current_target_legality_and_does_not_create_food():
    game = ready(6003)
    target = game.create_permanent(CREATURE_4, 1, summoning_sick=False)
    card = game.set_hand_for_testing(0, [TAINTED])[0]
    spell = game.announce_spell(0, card, target)
    assert spell is not None
    game.move_object(target, "graveyard", reason="c6_target_departed")

    result = game.resolve_top_of_stack()

    assert isinstance(result, CardObject)
    assert not foods(game)
    assert any(
        event["event"] == "spell_resolved_no_effect" and event["reason"] == "all_targets_illegal"
        for event in game.events
    )


def test_non_artifact_non_creature_target_is_rejected_without_payment():
    game = ready(6004)
    target = game.create_permanent(ENCHANTMENT, 1, summoning_sick=False)
    card = game.set_hand_for_testing(0, [TAINTED])[0]

    assert game.announce_spell(0, card, target) is None
    assert card.zone == "hand"
    assert not foods(game)


def test_food_creation_replays_deterministically():
    def run(seed: int):
        game = ready(seed)
        target = game.create_permanent(ARTIFACT_4, 1, summoning_sick=False)
        card = game.set_hand_for_testing(0, [TAINTED])[0]
        assert game.cast(0, card, target)
        return game.snapshot()

    assert run(6005) == run(6005)
