"""Focused synthetic coverage for Ravenous Robots artifact-cast triggers."""

from pathlib import Path

from tmnt_design_studio.engine07 import CardFact, Game, TriggerEffect, TriggeredAbilityObject, load_facts
from tmnt_design_studio.stage002 import load_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG = load_catalog(ROOT)
RAVENOUS = load_facts(CATALOG, {"Ravenous Robots"})["Ravenous Robots"]
PIZZA = load_facts(CATALOG, {"Spicy Oatmeal Pizza"})["Spicy Oatmeal Pizza"]
MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land — Mountain")
ARTIFACT_CAST_FRAGMENT = "Whenever you cast an artifact spell, create a 1/1 colorless Robot artifact creature token."


def test_ravenous_robots_triggers_for_normally_cast_spicy_oatmeal_pizza():
    game = Game(([MOUNTAIN] * 20, [MOUNTAIN] * 20), seed=8391)
    game.begin_turn()
    source = game.create_permanent(RAVENOUS, 0, summoning_sick=False)
    for _ in range(3):
        game.create_permanent(MOUNTAIN, 0, summoning_sick=False)
    card = game.set_hand_for_testing(0, [PIZZA])[0]
    spell = game.announce_spell(0, card)
    assert spell is not None

    cast_event = next(
        event
        for event in game._rules_events.values()
        if event.kind.value == "spell_cast" and event.source_id == spell.object_id
    )
    assert "Artifact" in game._card_types_from_type_line(cast_event.card_type_line)

    triggers = [
        item
        for item in game.stack
        if isinstance(item, TriggeredAbilityObject)
        and item.effect is TriggerEffect.CREATE_TOKEN
        and item.source_id == source.object_id
    ]
    assert len(triggers) == 1
