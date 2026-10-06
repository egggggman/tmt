from pathlib import Path

from tmnt_design_studio.card_interpreter07 import (
    CardInterpreter,
    TokenCreationProgram,
    TokenDefinition,
)
from tmnt_design_studio.engine07 import CardFact, Game, TriggeredAbilityObject, TriggerEffect
from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec

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
NONARTIFACT = CardFact("Bear", "{1}{G}", 2, "Creature - Bear", power=2, toughness=2)
ARTIFACT_TOKEN = TokenDefinition("Robot", "Artifact Creature - Robot", power=1, toughness=1)
ROOT = Path(__file__).resolve().parents[1]


def test_exact_recognizer_and_neighbors_fail_closed():
    i = CardInterpreter()
    assert i.artifact_entry_self_counter_semantic_coverage(SOURCE, FRAGMENT).fully_supported
    short_fragment = FRAGMENT.replace("Donatello, Way with Machines", "Donatello")
    assert i.artifact_entry_self_counter_semantic_coverage(SOURCE, short_fragment).fully_supported
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


def test_nonartifact_entry_does_not_trigger():
    g = Game(([SOURCE], [NONARTIFACT]), seed=25)
    g.begin_turn()
    g.create_permanent(SOURCE, 0)
    entering = g.create_permanent(NONARTIFACT, 0)
    g._process_creature_entered_triggers(entering, defer_triggers=True)
    assert not any(
        isinstance(x, TriggeredAbilityObject)
        and x.effect is TriggerEffect.ARTIFACT_ENTRY_SELF_COUNTER
        for x in g.stack
    )


def test_artifact_creature_token_entry_qualifies_by_type_and_controller():
    g = Game(([SOURCE], [NONARTIFACT]), seed=26)
    g.begin_turn()
    source = g.create_permanent(SOURCE, 0)
    g.create_tokens(
        0,
        TokenCreationProgram(ARTIFACT_TOKEN, 1),
        source_card="test",
        oracle_fragment="test token",
    )
    assert source.counters.get("+1/+1") == 1


def test_artifact_entry_replay_is_deterministic():
    def trace():
        g = Game(([SOURCE, ARTIFACT], [NONARTIFACT]), seed=27)
        g.begin_turn()
        g.create_permanent(SOURCE, 0)
        for _ in range(2):
            entering = g.create_permanent(ARTIFACT, 0)
            g._process_creature_entered_triggers(entering, defer_triggers=True)
        g.resolve_top_of_stack()
        g.resolve_top_of_stack()
        return g.events

    assert trace() == trace()


def test_multiple_entries_log_counters_and_update_power_toughness():
    g = Game(([SOURCE, ARTIFACT], [NONARTIFACT]), seed=23)
    g.begin_turn()
    source = g.create_permanent(SOURCE, 0)
    first = g.create_permanent(ARTIFACT, 0)
    second = g.create_permanent(ARTIFACT, 0)
    g._process_creature_entered_triggers(first, defer_triggers=True)
    g._process_creature_entered_triggers(second, defer_triggers=True)
    assert (
        sum(
            isinstance(x, TriggeredAbilityObject)
            and x.effect is TriggerEffect.ARTIFACT_ENTRY_SELF_COUNTER
            for x in g.stack
        )
        == 2
    )
    g.resolve_top_of_stack()
    g.resolve_top_of_stack()
    assert source.counters == {"+1/+1": 2}
    assert (source.power, source.toughness) == (4, 4)
    resolved = [x for x in g.events if x["event"] == "artifact_entry_counter_resolved"]
    assert len(resolved) == 2
    assert [x["quantity"] for x in resolved] == [1, 1]


def test_recovered_artifact_reentry_uses_the_same_trigger_path():
    g = Game(([SOURCE, ARTIFACT], [NONARTIFACT]), seed=24)
    g.begin_turn()
    source = g.create_permanent(SOURCE, 0)
    card = g.set_hand_for_testing(0, [ARTIFACT])[0]
    graveyard_card = g.move_object(card, "graveyard", reason="test_recovery")
    recovered = g.move_object(graveyard_card, "battlefield", controller=0, reason="test_recovery")
    assert recovered.card is ARTIFACT
    g._process_creature_entered_triggers(recovered, defer_triggers=True)
    g.resolve_top_of_stack()
    assert source.counters.get("+1/+1") == 1
    assert any(
        event["event"] == "artifact_entry_counter_resolved"
        and event["entered_id"] == recovered.object_id
        for event in g.events
    )


def test_real_donatello_seed_converts_artifact_entry_into_counter_payoff():
    result = run_smoke_game(
        ROOT,
        GameSpec(
            "donatello-shredder-way-3004",
            "donatello/shredder",
            3004,
            "donatello-first",
            (
                DeckSpec("donatello-p0.3a", "decks/donatello/PROTOTYPE_0.3a.txt"),
                DeckSpec("shredder-p0.3", "decks/shredder/PROTOTYPE_0.3.txt"),
            ),
        ),
    )
    assert result.get("error") is None
    assert any(
        event["event"] == "spell_cast" and event["card"] == "Donatello, Way with Machines"
        for event in result["events"]
    )
    assert (
        sum(event["event"] == "artifact_entry_counter_resolved" for event in result["events"]) >= 2
    )
    assert sum(event["event"] == "counters_placed" for event in result["events"]) >= 2
