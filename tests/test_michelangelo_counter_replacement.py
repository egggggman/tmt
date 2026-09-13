from tmnt_design_studio.engine07 import CardFact, Game

LAND = CardFact("Forest", "", 0, "Basic Land ? Forest")
MICHELANGELO = CardFact(
    "Michelangelo, Weirdness to 11",
    "{1}{G}",
    2,
    "Legendary Creature ? Mutant Ninja Turtle",
    "When Michelangelo enters, create a Mutagen token.\n"
    "If one or more +1/+1 counters would be put on a creature you control, "
    "that many plus one +1/+1 counters are put on it instead.",
    power=2,
    toughness=2,
)
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature ? Bear", power=2, toughness=2)


def test_michelangelo_adds_one_plus_one_counter_through_place_counters():
    g = Game(([LAND] * 20, [LAND] * 20), seed=9191)
    source = g.create_permanent(MICHELANGELO, 0, summoning_sick=False)
    target = g.create_permanent(BEAR, 0, summoning_sick=False)
    fragment = g.interpreter.fragments(source.card)[-1]
    g._register_semantic_occurrence(source, 0, fragment, ())
    g.place_counters(
        target, "+1/+1", 1, source_card="test", oracle_fragment="test", source_id=source.object_id
    )
    assert target.counters["+1/+1"] == 2
    event = next(e for e in g.events if e["event"] == "counter_replacement_applied")
    assert (
        event["source_id"] == source.object_id
        and event["target_id"] == target.object_id
        and event["quantity_after"] == 2
    )


def test_michelangelo_replacement_requires_authoritative_source_and_plus_counter():
    g = Game(([LAND] * 20, [LAND] * 20), seed=9191)
    source = g.create_permanent(MICHELANGELO, 0, summoning_sick=False)
    target = g.create_permanent(BEAR, 0, summoning_sick=False)
    fragment = g.interpreter.fragments(source.card)[-1]
    g._register_semantic_occurrence(source, 0, fragment, ())
    g.place_counters(target, "stun", 1, source_card="test", oracle_fragment="test")
    assert target.counters["stun"] == 1
    g.destroy(source)
    g.place_counters(target, "+1/+1", 1, source_card="test", oracle_fragment="test")
    assert target.counters["+1/+1"] == 1
