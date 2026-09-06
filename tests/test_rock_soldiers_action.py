import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game

FRAGMENT = "When this creature enters, destroy up to one target noncreature artifact."
SOURCE = CardFact(
    "Rock Soldiers", "{2}{R}", 3, "Creature - Soldier", FRAGMENT, power=3, toughness=3
)
ART = CardFact("Relic", "{2}", 2, "Artifact")


def resolve_priority(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            option = game.legal_priority_actions(game.priority_state.player_index)[0]
            game.execute_priority_action(option)


def test_exact_and_neighbor():
    interpreter = CardInterpreter()
    assert interpreter.rock_soldiers_etb_semantic_coverage(SOURCE, FRAGMENT).fully_supported
    assert (
        interpreter.rock_soldiers_etb_semantic_coverage(
            SOURCE, "When this creature enters, destroy target artifact."
        )
        is None
    )


def test_entry_uses_priority_and_resolves_locked_target_once():
    game = Game(([SOURCE], [ART]), seed=2300)
    game.begin_turn()
    source = game.create_permanent(SOURCE, 0)
    target = game.create_permanent(ART, 0)

    game._process_creature_entered_triggers(source)

    assert target.zone == "battlefield"
    assert game.priority_state is not None
    assert game.stack
    resolve_priority(game)
    assert target.zone == "former"
    assert any(card.card.name == "Relic" for card in game.players[0].graveyard)
    assert sum(event["event"] == "rock_soldiers_destroyed" for event in game.events) == 1


def test_locked_target_that_leaves_fails_closed_without_relinking():
    game = Game(([SOURCE], [ART, ART]), seed=2301)
    game.begin_turn()
    source = game.create_permanent(SOURCE, 0)
    target = game.create_permanent(ART, 0)
    replacement = game.create_permanent(ART, 0)

    game._process_creature_entered_triggers(source)
    game.put_into_graveyard(target)
    resolve_priority(game)

    assert target.zone == "former"
    assert any(card.card.name == "Relic" for card in game.players[0].graveyard)
    assert replacement.zone == "battlefield"
    assert not any(event["event"] == "rock_soldiers_destroyed" for event in game.events)


def test_optional_target_can_decline():
    game = Game(
        ([SOURCE], [ART]),
        seed=2302,
        stun_target_chooser=lambda _controller, _source_id, options: None,
    )
    game.begin_turn()
    source = game.create_permanent(SOURCE, 0)
    target = game.create_permanent(ART, 0)

    game._process_creature_entered_triggers(source)
    assert game.priority_state is not None
    resolve_priority(game)

    assert target.zone == "battlefield"
    assert not any(event["event"] == "rock_soldiers_destroyed" for event in game.events)


def test_only_noncreature_artifact_is_offered_once():
    creature_artifact = CardFact(
        "Artifact Creature", "{2}", 2, "Artifact Creature", power=2, toughness=2
    )
    nonartifact = CardFact("Bear", "{2}", 2, "Creature", power=2, toughness=2)
    offered = []

    def choose(_controller, _source_id, options):
        offered.append(options)
        return next(option for option in options if option is not None)

    game = Game(
        ([SOURCE], [ART, creature_artifact, nonartifact]),
        seed=2303,
        stun_target_chooser=choose,
    )
    game.begin_turn()
    source = game.create_permanent(SOURCE, 0)
    target = game.create_permanent(ART, 0)
    artifact_creature = game.create_permanent(creature_artifact, 0)
    ordinary_creature = game.create_permanent(nonartifact, 0)

    game._process_creature_entered_triggers(source)
    resolve_priority(game)

    assert offered == [(target.object_id, None)]
    assert target.zone == "former"
    assert artifact_creature.zone == "battlefield"
    assert ordinary_creature.zone == "battlefield"
    assert sum(event["event"] == "rock_soldiers_destroyed" for event in game.events) == 1


def test_relinked_source_identity_fails_closed():
    game = Game(([SOURCE], [ART]), seed=2304)
    game.begin_turn()
    source = game.create_permanent(SOURCE, 0)
    target = game.create_permanent(ART, 0)

    game._process_creature_entered_triggers(source)
    source.card = CardFact(
        "Relinked Rock Soldiers", "{2}{R}", 3, "Creature - Soldier", FRAGMENT, power=3, toughness=3
    )

    with pytest.raises(ValueError, match="Rock Soldiers trigger"):
        resolve_priority(game)
    assert target.zone == "battlefield"
