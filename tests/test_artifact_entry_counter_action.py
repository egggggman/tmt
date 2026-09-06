from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TriggeredAbilityObject, TriggerEffect

FRAGMENT = (
    "Whenever an artifact you control enters, put a +1/+1 counter on Donatello, Way with Machines."
)
SOURCE = CardFact(
    "Donatello, Way with Machines",
    "{2}{U}",
    3,
    "Creature - Turtle",
    FRAGMENT,
    power=2,
    toughness=2,
    oracle_id="donatello-way",
)
ARTIFACT = CardFact("Relic", "{1}", 1, "Artifact", oracle_id="relic")


def test_exact_recognizer_and_neighbors_fail_closed():
    i = CardInterpreter()
    assert i.artifact_entry_self_counter_semantic_coverage(SOURCE, FRAGMENT).fully_supported
    assert (
        i.artifact_entry_self_counter_semantic_coverage(
            SOURCE, FRAGMENT.replace("artifact", "creature")
        )
        is None
    )


def test_artifact_entry_stacks_once_and_resolves_counter_on_source():
    g = Game(([SOURCE], [ARTIFACT]), seed=21)
    g.begin_turn()
    source = g.create_permanent(SOURCE, 0)
    entering = g.create_permanent(ARTIFACT, 0)
    g._process_creature_entered_triggers(entering, defer_triggers=True)
    abilities = [
        x
        for x in g.stack
        if isinstance(x, TriggeredAbilityObject)
        and x.effect is TriggerEffect.ARTIFACT_ENTRY_SELF_COUNTER
    ]
    assert len(abilities) == 1
    assert source.counters.get("+1/+1", 0) == 0
    g.resolve_top_of_stack()
    assert source.counters.get("+1/+1", 0) == 1


def test_wrong_controller_entry_does_not_trigger():
    g = Game(([SOURCE], [ARTIFACT]), seed=22)
    g.begin_turn()
    g.create_permanent(SOURCE, 0)
    entering = g.create_permanent(ARTIFACT, 1)
    g._process_creature_entered_triggers(entering, defer_triggers=True)
    assert not any(
        isinstance(x, TriggeredAbilityObject)
        and x.effect is TriggerEffect.ARTIFACT_ENTRY_SELF_COUNTER
        for x in g.stack
    )
