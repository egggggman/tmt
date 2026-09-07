import copy
import json
from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    CardFact,
    DiscardDrawOption,
    Game,
    RulesEventKind,
    TriggerEffect,
)

LAND = CardFact("Plains", "", 0, "Basic Land")
FRAGMENT = "When Stockman enters, draw a card, then discard a card."
STOCKMAN = CardFact("Stockman, Mad Fly-entist", "{2}{U}", 3, "Creature", FRAGMENT, 2, 2)


def setup(chooser=None, hand=(LAND, LAND)):
    g = Game(([LAND] * 30, [LAND] * 30), seed=26, draw_discard_chooser=chooser)
    g.begin_turn()
    g.set_hand_for_testing(0, list(hand))
    source = g.create_permanent(STOCKMAN, 0)
    g._process_creature_entered_triggers(source)
    return g, source, g.stack[-1]


def resolve(g):
    while g.priority_state is not None:
        if g.priority_state.resolution_pending:
            g.process_priority_resolution()
        else:
            g.execute_priority_action(g.legal_priority_actions(g.priority_state.player_index)[0])


def evidence(g):
    return next(e for e in g.events if e["event"] == "etb_draw_discard_committed")


def empty_library(g):
    while g.players[0].library:
        g.move_object(g.players[0].library[-1], "graveyard", reason="test_empty")


def test_exact_grammar_is_oracle_derived():
    i = CardInterpreter()
    result = i.etb_draw_discard_semantic_coverage(STOCKMAN, FRAGMENT)
    assert result and result.coverage.fully_supported and result.program.draw_first
    renamed = replace(STOCKMAN, name="Renamed", oracle_text=FRAGMENT.replace("Stockman", "Renamed"))
    assert i.etb_draw_discard_semantic_coverage(renamed, renamed.oracle_text)
    assert i.etb_draw_discard_semantic_coverage(renamed, FRAGMENT) is None


@pytest.mark.parametrize(
    "fragment",
    [
        FRAGMENT.replace("When", "Whenever"),
        FRAGMENT.replace("enters", "attacks"),
        FRAGMENT.replace("draw a card", "draw two cards"),
        FRAGMENT.replace("discard a card", "you may discard a card"),
        FRAGMENT.replace("discard a card", "discard a card at random"),
        FRAGMENT + " Gain 1 life.",
        "When Stockman enters, discard a card, then draw a card.",
    ],
)
def test_neighbors_rejected(fragment):
    assert CardInterpreter().etb_draw_discard_semantic_coverage(STOCKMAN, fragment) is None


def test_etb_is_once_and_no_mutation_before_priority():
    g, source, ability = setup()
    before = tuple(g.players[0].hand), tuple(g.players[0].library)
    g._enqueue_trigger(ability.event, source, FRAGMENT, TriggerEffect.ETB_DRAW_DISCARD)
    g._put_pending_triggers_on_stack()
    assert g.stack == [ability]
    assert ability.effect is TriggerEffect.ETB_DRAW_DISCARD
    with pytest.raises(ValueError, match="before all players pass"):
        g.resolve_top_of_stack()
    assert before == (tuple(g.players[0].hand), tuple(g.players[0].library))
    resolve(g)
    after = g.snapshot()
    with pytest.raises(ValueError):
        g._resolve_etb_draw_discard(ability)
    assert g.snapshot() == after
    with pytest.raises(ValueError, match="semantic applicability"):
        g._process_creature_entered_triggers(source)
    assert not g.stack


def test_post_draw_choice_can_discard_the_drawn_equal_valued_card():
    observations = []

    def choose(view, options):
        observations.append((view, options))
        assert all(option.card_id is not None for option in options)
        return options[-1]

    g, _source, _ability = setup(choose)
    originals = tuple(g.players[0].hand)
    resolve(g)
    e = evidence(g)
    assert len(observations[0][0].cards) == 3
    assert len({x.card_id for x in observations[0][1]}) == 3
    assert e["selected_hand_id"] == e["drawn_hand_id"]
    assert e["drawn_hand_id"] != e["drawn_library_id"]
    assert tuple(g.players[0].hand) == originals
    assert len(g.players[0].graveyard) == 1
    snapshot = g.snapshot()
    Game.validate_draw_discard_snapshot_evidence(snapshot)
    assert any(
        o["oracle_fragment"] == FRAGMENT for o in snapshot["conformance"]["semantic_occurrences"]
    )


@pytest.mark.parametrize(
    "kind", ["fabricated", "decline", "stale", "relinked", "mutated", "zone_mutation", "movement"]
)
def test_invalid_post_draw_choice_fails_closed(kind):
    def choose(_view, options):
        player = g.players[0]
        chosen = player.hand[0]
        if kind == "fabricated":
            return DiscardDrawOption("fabricated")
        if kind == "decline":
            return DiscardDrawOption(None)
        if kind == "stale":
            return DiscardDrawOption(stale_id)
        if kind == "relinked":
            g._objects[chosen.object_id] = copy.copy(chosen)
        if kind == "mutated":
            chosen.card = replace(chosen.card)
        if kind == "movement":
            g.move_object(chosen, "graveyard", reason="forbidden_chooser_movement")
        if kind == "zone_mutation":
            player.hand.pop()
        return options[0]

    g, _source, _ability = setup(choose)
    stale = g.players[0].hand[-1]
    stale_id = stale.object_id
    g.move_object(stale, "graveyard", reason="test_stale")
    hand_before = tuple(g.players[0].hand)
    library_before = tuple(g.players[0].library)
    graveyard_before = tuple(g.players[0].graveyard)
    with pytest.raises(ValueError, match="discard/Draw"):
        resolve(g)
    # The preceding mandatory Draw is intentional; no invalid discard or chooser mutation commits.
    assert tuple(g.players[0].hand[:-1]) == hand_before
    assert len(g.players[0].hand) == len(hand_before) + 1
    assert tuple(g.players[0].library) == library_before[:-1]
    assert tuple(g.players[0].graveyard) == graveyard_before
    assert all(g.is_authoritative(obj, "hand") for obj in g.players[0].hand)
    assert all(obj.card is LAND for obj in g.players[0].hand)
    assert not any(e["event"] == "etb_draw_discard_committed" for e in g.events)


def test_source_departure_does_not_erase_trigger():
    g, source, _ability = setup()
    g.put_into_graveyard(source)
    resolve(g)
    assert evidence(g)["source_id"] == source.object_id
    assert source.zone == "former"
    Game.validate_draw_discard_snapshot_evidence(g.snapshot())


@pytest.mark.parametrize("tamper", ["source", "event", "controller", "stack", "fragment"])
def test_trigger_provenance_rejects_tampering_before_draw(tamper):
    g, source, ability = setup()
    before = tuple(g.players[0].hand), tuple(g.players[0].library)
    if tamper == "source":
        g._objects[source.object_id] = copy.copy(source)
    elif tamper == "event":
        ability.event = replace(ability.event, subject_ids=("fake",))
    elif tamper == "controller":
        ability.controller = 1
    elif tamper == "stack":
        clone = copy.copy(ability)
        g.stack[-1] = clone
        g._objects[ability.object_id] = clone
    else:
        ability.oracle_fragment = FRAGMENT + " Draw a card."
    with pytest.raises(ValueError):
        resolve(g)
    assert before == (tuple(g.players[0].hand), tuple(g.players[0].library))


def test_wrong_entry_event_rejected():
    g, source, _ability = setup()
    event = g._new_rules_event(RulesEventKind.ATTACKERS_DECLARED, 0, (source.object_id,))
    with pytest.raises(ValueError, match="entry provenance"):
        g._enqueue_trigger(event, source, FRAGMENT, TriggerEffect.ETB_DRAW_DISCARD)


@pytest.mark.parametrize("hand", [(), (LAND,)])
def test_empty_library_still_discards_if_possible_then_loses_at_sba(hand):
    g, _source, _ability = setup(hand=hand)
    empty_library(g)
    resolve(g)
    e = evidence(g)
    assert not e["draw_succeeded"] and e["drawn_hand_id"] is None
    assert bool(e["discarded_graveyard_id"]) == bool(hand)
    assert e["failed_draw_pending"]
    assert g.players[0].lost and g.players[0].loss_reason == "draw_from_empty_library"
    names = [e["event"] for e in g.events]
    assert names.index("draw_failed") < names.index("etb_draw_discard_committed")
    assert (
        names.index("etb_draw_discard_committed")
        < names.index("trigger_resolved")
        < names.index("player_lost")
    )
    Game.validate_draw_discard_snapshot_evidence(g.snapshot())


@pytest.mark.parametrize(
    "field,value",
    [
        ("drawn_hand_id", "fake"),
        ("selected_hand_id", "fake"),
        ("draw_succeeded", False),
        ("start_event_cursor", 0),
        ("post_hand_ids", []),
        ("controller", 1),
    ],
)
def test_serialized_evidence_rejects_fabricated_claims(field, value):
    g, _source, _ability = setup()
    resolve(g)
    snapshot = json.loads(json.dumps(g.snapshot()))
    Game.validate_draw_discard_snapshot_evidence(snapshot)
    e = next(e for e in snapshot["events"] if e["event"] == "etb_draw_discard_committed")
    e[field] = value
    with pytest.raises(ValueError, match="does not reconstruct"):
        Game.validate_draw_discard_snapshot_evidence(snapshot)


def test_reconstruction_survives_later_zone_changes_and_rejects_reordering():
    g, _source, _ability = setup()
    resolve(g)
    g.move_object(g.players[0].hand[-1], "graveyard", reason="later")
    snap = g.snapshot()
    Game.validate_draw_discard_snapshot_evidence(snap)
    e = next(e for e in snap["events"] if e["event"] == "etb_draw_discard_committed")
    start = e["start_event_cursor"]
    snap["events"][start], snap["events"][start + 2] = (
        snap["events"][start + 2],
        snap["events"][start],
    )
    with pytest.raises(ValueError, match="does not reconstruct"):
        Game.validate_draw_discard_snapshot_evidence(snap)


def test_internal_resolution_cannot_pop_before_priority_and_public_all_pass_is_valid():
    g, _source, ability = setup()
    with pytest.raises(ValueError, match="Priority resolution"):
        g._resolve_triggered_ability(ability)
    assert g.stack == [ability]
    while not g.priority_state.resolution_pending:
        g.execute_priority_action(g.legal_priority_actions(g.priority_state.player_index)[0])
    g.resolve_top_of_stack()
    assert evidence(g)["draw_succeeded"]
    assert not g.stack
