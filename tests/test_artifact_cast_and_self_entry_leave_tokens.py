"""Oracle-derived cast and self-zone token triggers share the normal stack."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, RulesEventKind, TriggeredAbilityObject

ROOT = Path(__file__).resolve().parents[1]
FOUNDRY_TEXT = (
    "When this artifact enters or leaves the battlefield, "
    "create a 1/1 colorless Robot artifact creature token."
)
ROBOTS_TEXT = (
    "Whenever you cast an artifact spell, create a 1/1 colorless Robot artifact creature token."
)
FOUNDRY = CardFact("Workshop", "{1}{R}", 2, "Artifact", FOUNDRY_TEXT)
ROBOTS = CardFact("Automaton", "{1}{R}", 2, "Artifact Creature — Robot", ROBOTS_TEXT, 1, 1)
ARTIFACT = CardFact("Cog", "{0}", 0, "Artifact")
NONARTIFACT = CardFact("Mouse", "{0}", 0, "Creature — Mouse", power=1, toughness=1)
LAND = CardFact("Mountain", "", 0, "Basic Land — Mountain")


def game(seed=11):
    g = Game(([LAND] * 30, [LAND] * 30), seed=seed)
    g.begin_turn()
    return g


def robots(g):
    return [
        item
        for player in g.players
        for item in player.battlefield
        if item.is_token and item.card.name == "Robot"
    ]


def pass_to_resolution(g):
    if g.priority_state is None:
        g._put_pending_triggers_on_stack()
        g._begin_priority_window()
    while g.priority_state is not None and not g.priority_state.resolution_pending:
        state = g.priority_state
        g.execute_priority_action(g.legal_priority_actions(state.player_index)[0])
    g.process_priority_resolution()


def test_catalog_clauses_and_renamed_generic_recognition():
    catalog = json.loads((ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json").read_text())
    for name, fragment, card, context in (
        ("Mouser Foundry", FOUNDRY_TEXT, FOUNDRY, "entry_or_leave"),
        ("Ravenous Robots", ROBOTS_TEXT, ROBOTS, "artifact_cast"),
    ):
        actual = next(item for item in catalog if item["name"] == name)
        assert fragment in actual["oracle_text"]
        for fixture in (card, replace(card, name=f"Another {name}")):
            semantics = CardInterpreter().token_semantic_coverage(fixture, fragment)
            assert semantics is not None and semantics.fully_supported
            assert semantics.program.quantity == 1
            assert semantics.program.definition.name == "Robot"
            assert (
                CardInterpreter().entry_leave_or_artifact_cast_token_context(fixture, fragment)
                == context
            )
    assert (
        CardInterpreter().entry_leave_or_artifact_cast_token_context(
            FOUNDRY, FOUNDRY_TEXT + " Draw a card."
        )
        is None
    )


def test_self_entry_leave_uses_departure_controller_and_stack_even_after_reentry():
    g = game()
    source = g.create_permanent(FOUNDRY, 0, controller=1)
    g._process_creature_entered_triggers(source, defer_triggers=True)
    entry = g.stack[-1]
    assert isinstance(entry, TriggeredAbilityObject)
    assert entry.event.kind is RulesEventKind.PERMANENT_ENTERED
    assert entry.controller == 1 and not robots(g)
    with pytest.raises(ValueError, match="before all players pass"):
        g.resolve_top_of_stack()
    pass_to_resolution(g)
    assert len(robots(g)) == 1 and robots(g)[0].controller == 1
    old_id = source.object_id
    hand = g.move_object(source, "hand", reason="bounce")
    assert len(g.pending_triggers) == 1 and not g.stack
    g._put_pending_triggers_on_stack()
    leave = g.stack[-1]
    assert leave.event.kind is RulesEventKind.PERMANENT_LEFT
    assert leave.source_id == old_id and leave.controller == 1
    returned = g.move_object(hand, "battlefield", controller=0, reason="reentry")
    assert returned.object_id != old_id
    pass_to_resolution(g)
    assert [item.controller for item in robots(g)] == [1, 1]
    assert any(
        event["event"] == "tokens_created" and event.get("source_id") == old_id
        for event in g.events
    )


def test_artifact_cast_not_entry_and_multiple_watchers_stack_before_spell():
    g = game()
    first = g.create_permanent(ROBOTS, 0)
    second = g.create_permanent(ROBOTS, 0)
    g.create_permanent(ARTIFACT, 0)
    assert not robots(g)  # Battlefield entry is not casting.
    card = g.set_hand_for_testing(0, [ARTIFACT])[0]
    spell = g.announce_spell(0, card)
    assert spell is not None
    assert [item.source_id for item in g.stack[1:]] == [second.object_id, first.object_id]
    assert all(item.event.kind is RulesEventKind.SPELL_CAST for item in g.stack[1:])
    assert not robots(g)
    g.move_object(first, "graveyard", reason="response")
    pass_to_resolution(g)
    pass_to_resolution(g)
    assert len(robots(g)) == 2
    assert all(item.controller == 0 for item in robots(g))
    assert g.stack[0] is spell


def test_opponent_cast_and_nonartifact_spell_do_not_trigger():
    g = game()
    g.create_permanent(ROBOTS, 0)
    other = g.set_hand_for_testing(1, [ARTIFACT])[0]
    assert g.announce_spell(1, other) is None  # Opponent lacks sorcery timing.
    card = g.set_hand_for_testing(0, [NONARTIFACT])[0]
    assert g.announce_spell(0, card) is not None
    assert len(g.stack) == 1 and not robots(g)


def test_deterministic_token_trace_and_source_identity():
    def trace():
        g = game(203)
        source = g.create_permanent(FOUNDRY, 0)
        g._process_creature_entered_triggers(source)
        pass_to_resolution(g)
        g.move_object(source, "graveyard", reason="destroy")
        pass_to_resolution(g)
        return g.snapshot()

    assert trace() == trace()
