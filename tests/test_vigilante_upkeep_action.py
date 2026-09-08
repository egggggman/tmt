import copy
import json
from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TriggerEffect, TurnStep
from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.stage002 import _begin_turn_with_priority

LAND = CardFact("Plains", "", 0, "Basic Land")
FRAGMENT = CardInterpreter.VIGILANTE_FRAGMENT
CASEY = CardFact("Casey Jones, Vigilante", "{2}{R}", 3, "Creature", FRAGMENT, 3, 3)


def setup(owner=0, at_upkeep=False):
    g = Game(([LAND] * 60, [LAND] * 60), seed=29)
    if at_upkeep:
        g.advance_step()
        g.advance_step()
    else:
        g.begin_turn()
    source = g.create_permanent(CASEY, owner)
    before = len(g.players[owner].hand)
    g._process_creature_entered_triggers(source)
    return g, source, before


def resolve(g):
    while g.priority_state is not None and g.winner is None:
        if g.priority_state.resolution_pending:
            g.process_priority_resolution()
        else:
            g.execute_priority_action(g.legal_priority_actions(g.priority_state.player_index)[0])


def due(g, owner):
    if g.step is not TurnStep.PRECOMBAT_MAIN:
        g.advance_to(TurnStep.PRECOMBAT_MAIN)
    while True:
        g.end_turn()
        g.advance_step()
        g.advance_step()
        if g.active_player == owner:
            return
        resolve(g)
        g.advance_to(TurnStep.PRECOMBAT_MAIN)


def validate(g):
    Game.validate_vigilante_snapshot_evidence(g.snapshot())
    snap = json.loads(json.dumps(g.snapshot()))
    Game.validate_vigilante_snapshot_evidence(snap)
    return snap


@pytest.mark.parametrize(
    "fragment",
    [
        FRAGMENT.replace("three", "two"),
        FRAGMENT.replace("next upkeep", "end step"),
        FRAGMENT.replace("at random", ""),
        FRAGMENT + " Draw a card.",
        FRAGMENT.replace("Casey Jones", "this creature"),
    ],
)
def test_exact_grammar_neighbors(fragment):
    assert CardInterpreter().vigilante_semantic_coverage(CASEY, fragment) is None


def test_exact_grammar_rename_and_noncreature():
    i = CardInterpreter()
    assert i.vigilante_semantic_coverage(replace(CASEY, name="Renamed"), FRAGMENT)
    assert i.vigilante_semantic_coverage(replace(CASEY, type_line="Artifact"), FRAGMENT) is None


@pytest.mark.parametrize("owner", [0, 1])
@pytest.mark.parametrize("at_upkeep", [False, True])
def test_both_priority_windows_and_first_subsequent_upkeep(owner, at_upkeep):
    g, source, before = setup(owner, at_upkeep)
    ability = g.stack[-1]
    assert len(g.players[owner].hand) == before and not g._vigilante_schedules
    g._enqueue_trigger(ability.event, source, FRAGMENT, TriggerEffect.ETB_VIGILANTE)
    assert len(g.stack) == 1 and not g.pending_triggers
    with pytest.raises(ValueError, match="all players pass"):
        g.resolve_top_of_stack()
    resolve(g)
    assert len(g.players[owner].hand) == before + 3
    snap = validate(g)
    assert snap["vigilante_evidence"]["records"][0]["state"] == "pending"
    assert not any(
        r["oracle_fragment"] == FRAGMENT for r in snap["conformance"]["executed_references"]
    )
    due(g, owner)
    hand = tuple(g.players[owner].hand)
    assert len(g.stack) == 1
    validate(g)
    with pytest.raises(ValueError, match="unresolved stack"):
        g.advance_step()
    with pytest.raises(ValueError, match="all players pass"):
        g.resolve_top_of_stack()
    assert tuple(g.players[owner].hand) == hand
    resolve(g)
    assert len(g.players[owner].hand) == len(hand) - 3
    snap = validate(g)
    assert snap["vigilante_evidence"]["records"][0]["consumed"]
    assert any(r["oracle_fragment"] == FRAGMENT for r in snap["conformance"]["executed_references"])
    g.advance_step()


@pytest.mark.parametrize("size", [0, 1, 2, 3, 4, 9])
def test_current_hand_random_sample_and_rng_policy(size):
    runs = []
    for _ in range(2):
        g, _, _ = setup()
        resolve(g)
        due(g, 0)
        for obj in tuple(g.players[0].hand):
            g.move_object(obj, "graveyard", reason="test_hand_change")
        g.draw(g.players[0], size)
        ids = [o.object_id for o in g.players[0].hand]
        records = len(g.rng.records)
        resolve(g)
        assert len(g.rng.records) == records + 1
        event = next(e for e in g.events if e["event"] == "vigilante_resolved")
        assert len(set(event["selected_ids"])) == min(3, size)
        assert set(event["selected_ids"]) <= set(ids)
        assert [o.object_id for o in g.players[0].hand] == [
            i for i in ids if i not in event["selected_ids"]
        ]
        runs.append(validate(g))
    assert runs[0] == runs[1]


@pytest.mark.parametrize("change", ["departure", "reentry", "control"])
def test_source_lifetime_and_independent_schedules(change):
    g, source, _ = setup()
    resolve(g)
    if change == "control":
        g.players[0].battlefield.remove(source)
        g.players[1].battlefield.append(source)
        source.controller = 1
    else:
        card = g.move_object(source, "graveyard", reason="test_departure")
        if change == "reentry":
            returned = g.move_object(card, "battlefield", controller=1, reason="test_reentry")
            g._process_creature_entered_triggers(returned)
            resolve(g)
    validate(g)
    due(g, 0)
    resolve(g)
    records = validate(g)["vigilante_evidence"]["records"]
    assert records[0]["controller"] == 0 and records[0]["state"] == "resolved"
    if change == "reentry":
        assert (
            len(records) == 2
            and records[1]["controller"] == 1
            and records[1]["state"] == "resolved"
        )


def test_multiple_same_controller_records_and_replay():
    g, _, _ = setup()
    other = g.create_permanent(CASEY, 0)
    g._process_creature_entered_triggers(other)
    resolve(g)
    assert len(g._vigilante_schedules) == 2
    due(g, 0)
    assert len(g.stack) == 2
    with pytest.raises(ValueError, match="replay"):
        g._vigilante_upkeep()
    abilities = tuple(g.stack)
    resolve(g)
    assert all(r["consumed"] for r in validate(g)["vigilante_evidence"]["records"])
    with pytest.raises(ValueError):
        g._resolve_vigilante(abilities[0])


@pytest.mark.parametrize("cards", [0, 1, 2])
def test_partial_draw_and_terminal_pending(cards):
    g, _, _ = setup()
    while len(g.players[0].library) > cards:
        g.move_object(g.players[0].library[-1], "graveyard", reason="test_short_library")
    hand = len(g.players[0].hand)
    resolve(g)
    assert len(g.players[0].hand) == hand + cards and g.winner is not None
    snap = validate(g)
    record = snap["vigilante_evidence"]["records"][0]
    assert record["state"] == "pending" and record["terminal_without_resolution"]
    assert not any(
        r["oracle_fragment"] == FRAGMENT for r in snap["conformance"]["executed_references"]
    )


@pytest.mark.parametrize("kind", ["schedule", "state", "source", "event", "stack", "hand"])
def test_live_identity_tampering_fails_closed(kind):
    g, source, _ = setup()
    resolve(g)
    sid = next(iter(g._vigilante_schedules))
    if kind == "schedule":
        g._vigilante_schedules[sid] = replace(g._vigilante_schedules[sid])
    elif kind == "state":
        g._vigilante_states[sid] = "resolved"
    elif kind == "source":
        g._objects[source.object_id] = copy.copy(source)
    if kind in {"schedule", "state", "source"}:
        with pytest.raises((ValueError, AssertionError)):
            due(g, 0)
        return
    due(g, 0)
    ability = g.stack[-1]
    if kind == "event":
        ability.event = replace(ability.event)
    elif kind == "stack":
        clone = copy.copy(ability)
        g.stack[-1] = clone
        g._objects[clone.object_id] = clone
    else:
        g.players[0].hand[-1] = copy.copy(g.players[0].hand[-1])
    with pytest.raises(ValueError, match="Vigilante"):
        resolve(g)


@pytest.mark.parametrize(
    "kind",
    [
        "missing_ledger",
        "state",
        "schedule",
        "rng",
        "hand",
        "sample",
        "boundary",
        "movement",
        "both_copies",
        "missing_resolution",
    ],
)
def test_serialized_delayed_chain_rejects_corruption(kind):
    g, _, _ = setup()
    resolve(g)
    due(g, 0)
    resolve(g)
    snap = validate(g)
    if kind == "missing_ledger":
        del snap["vigilante_evidence"]
    elif kind == "state":
        snap["vigilante_evidence"]["records"][0]["state"] = "pending"
    elif kind == "schedule":
        snap["vigilante_evidence"]["records"][0]["controller"] = 1
    elif kind == "rng":
        snap["rng"]["records"][-1]["result"] = []
    elif kind == "missing_resolution":
        snap["events"] = [
            e
            for e in snap["events"]
            if not (e.get("event") == "trigger_resolved" and e.get("effect") == "vigilante_discard")
        ]
    else:
        e = next(e for e in snap["events"] if e["event"] == "vigilante_resolved")
        if kind == "hand":
            e["pre_hand_ids"] = []
        if kind == "sample":
            e["selected_ids"] = ["fake"]
        if kind == "movement":
            e["movements"] = []
        if kind == "boundary":
            next(e for e in snap["events"] if e["event"] == "vigilante_delivered")["event_id"] = (
                "fake"
            )
        if kind == "both_copies":
            e["selected_ids"] = ["fake"]
        # Keep the duplicate event ledger consistent: independent reconstruction must reject.
        for segment in snap["vigilante_evidence"]["segments"]:
            start = segment["start"]
            n = len(segment["events"])
            segment["events"] = copy.deepcopy(snap["events"][start : start + n])
    with pytest.raises(ValueError, match="reconstruct"):
        Game.validate_vigilante_snapshot_evidence(snap)


def test_runner_services_upkeep_before_draw():
    g, _, _ = setup()
    resolve(g)
    g.end_turn()
    _begin_turn_with_priority(g, AcceptancePilot())
    g.end_turn()
    _begin_turn_with_priority(g, AcceptancePilot())
    assert g.step is TurnStep.PRECOMBAT_MAIN and not g.stack
    snap = validate(g)
    end = next(i for i, e in enumerate(snap["events"]) if e["event"] == "vigilante_resolved")
    draw = next(
        i
        for i, e in enumerate(snap["events"])
        if e["event"] == "step_started" and e["step"] == "draw" and e["turn"] == 3
    )
    assert end < draw


@pytest.mark.parametrize(
    "kind",
    [
        "source_before_draw",
        "etb_event",
        "etb_stack",
        "forged_schedule",
        "rng_identity",
        "rng_state",
    ],
)
def test_additional_live_provenance(kind):
    from tmnt_design_studio.engine07 import DeterministicRNG

    g, source, _ = setup()
    if kind == "source_before_draw":
        g.put_into_graveyard(source)
        resolve(g)
        due(g, 0)
        resolve(g)
        assert validate(g)["vigilante_evidence"]["records"][0]["consumed"]
        return
    if kind in {"etb_event", "etb_stack"}:
        ability = g.stack[-1]
        if kind == "etb_event":
            ability.event = replace(ability.event)
        else:
            g.stack[-1] = copy.copy(ability)
        with pytest.raises(ValueError):
            resolve(g)
        assert not g._vigilante_schedules
        return
    resolve(g)
    if kind == "forged_schedule":
        sid = next(iter(g._vigilante_schedules))
        forged = replace(g._vigilante_schedules[sid], controller=1)
        g._vigilante_schedules[sid] = g._vigilante_originals[sid] = forged
    elif kind == "rng_identity":
        g.rng = DeterministicRNG(29)
    else:
        g.rng.records[-1] = replace(g.rng.records[-1], state_after="fake")
    with pytest.raises(ValueError, match="Vigilante"):
        g.vigilante_snapshot_evidence()


@pytest.mark.parametrize(
    "kind",
    [
        "missing_due_delivery",
        "delivered_stack",
        "controller",
        "first_boundary",
        "rng_chain",
        "hand_authentication",
    ],
)
def test_independent_pending_and_resolution_authentication(kind):
    g, _, _ = setup()
    resolve(g)
    due(g, 0)
    if kind != "delivered_stack":
        resolve(g)
    snap = validate(g)
    if kind == "delivered_stack":
        snap["stack"][0]["controller"] = 1
    elif kind == "missing_due_delivery":
        next(e for e in snap["events"] if e["event"] == "vigilante_delivered")["schedule_id"] = (
            "fake"
        )
    elif kind == "controller":
        next(
            e
            for e in snap["events"]
            if e.get("event") == "trigger_pending"
            and e["event_id"] == snap["vigilante_evidence"]["segments"][-2]["events"][0]["event_id"]
        )["controller"] = "B"
    elif kind == "first_boundary":
        next(e for e in snap["events"] if e["event"] == "vigilante_upkeep")["step_cursor"] = 0
    elif kind == "rng_chain":
        snap["rng"]["records"][-2]["state_after"] = "fake"
    else:
        # Alter the independent pre-resolution hand movement without changing its claim.
        next(
            e
            for e in snap["events"]
            if e["event"] == "zone_changed" and e["destination_zone"] == "hand"
        )["destination_object_id"] = "fake"
    for segment in snap["vigilante_evidence"]["segments"]:
        start = segment["start"]
        segment["events"] = copy.deepcopy(snap["events"][start : start + len(segment["events"])])
    with pytest.raises(ValueError, match="reconstruct"):
        Game.validate_vigilante_snapshot_evidence(snap)
