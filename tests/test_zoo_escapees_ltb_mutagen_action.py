import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, RulesEventKind, TriggerEffect

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Forest", "", 0, "Basic Land")
FRAGMENT = (
    "When this creature leaves the battlefield, create a Mutagen token. "
    "(It's an artifact with \"{1}, {T}, Sacrifice this token: Put a +1/+1 counter "
    'on target creature. Activate only as a sorcery.")'
)
ZOO = CardFact("Zoo Escapees", "{3}{G}", 4, "Creature", FRAGMENT, 4, 4)


def setup(controller=0):
    g = Game(([LAND] * 30, [LAND] * 30), seed=27)
    g.begin_turn()
    source = g.create_permanent(ZOO, 0, controller=controller)
    return g, source


def tokens(g):
    return [x for p in g.players for x in p.battlefield if x.is_token]


def leave(g, source, destination="graveyard"):
    replacement = g.move_object(source, destination, reason="test_departure")
    assert len(g.pending_triggers) == 1
    assert not g.stack and not tokens(g)
    g.check_state_based_actions()
    return replacement, g.stack[-1]


def resolve(g):
    while g.priority_state is not None:
        if g.priority_state.resolution_pending:
            g.process_priority_resolution()
        else:
            g.execute_priority_action(g.legal_priority_actions(g.priority_state.player_index)[0])


def test_exact_authoritative_grammar_without_name_dispatch():
    catalog = json.loads((ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json").read_bytes())
    actual = next(c for c in catalog if c["name"] == "Zoo Escapees")
    assert actual["oracle_text"] == FRAGMENT == CardInterpreter.LTB_MUTAGEN_FRAGMENT
    i = CardInterpreter()
    for card in (ZOO, replace(ZOO, name="Renamed")):
        c = i.ltb_mutagen_semantic_coverage(card, FRAGMENT)
        assert c.payload_executable and c.parent_executable
        assert not c.followup_executable and not c.fully_supported
        assert c.program.quantity == 1
        assert c.program.definition is i.PREDEFINED_TOKENS["mutagen"]
        assert c.limitations == ("token_activated_ability_not_implemented",)


@pytest.mark.parametrize(
    "fragment",
    [
        FRAGMENT.replace("leaves the battlefield", "dies"),
        FRAGMENT.replace("leaves the battlefield", "enters"),
        FRAGMENT.replace("this creature", "another creature"),
        FRAGMENT.replace("a Mutagen", "two Mutagen"),
        FRAGMENT.replace("Mutagen", "Food"),
        FRAGMENT.replace("create", "you may create"),
        FRAGMENT.replace("+1/+1", "+2/+2"),
        FRAGMENT.split(" (", 1)[0],
        FRAGMENT + " Draw a card.",
    ],
)
def test_near_neighbors_rejected(fragment):
    assert CardInterpreter().ltb_mutagen_semantic_coverage(ZOO, fragment) is None


@pytest.mark.parametrize("destination", ["hand", "library", "graveyard"])
@pytest.mark.parametrize("controller", [0, 1])
def test_qualifying_leave_creates_one_token_only_after_priority(destination, controller):
    g, source = setup(controller)
    _replacement, ability = leave(g, source, destination)
    assert source.zone == "former"
    assert ability.effect is TriggerEffect.LTB_MUTAGEN
    assert ability.event.source_id == source.object_id
    assert ability.controller == controller
    with pytest.raises(ValueError, match="before all players pass"):
        g.resolve_top_of_stack()
    with pytest.raises(ValueError, match="Priority resolution"):
        g._resolve_triggered_ability(ability)
    assert not tokens(g) and g.stack == [ability]
    resolve(g)
    assert len(tokens(g)) == 1
    token = tokens(g)[0]
    assert token.card is CardInterpreter.PREDEFINED_TOKENS["mutagen"]
    assert token.owner == token.controller == controller
    assert g.is_authoritative(token, "battlefield")
    assert token.object_id not in {source.object_id, ability.object_id}
    Game.validate_ltb_mutagen_snapshot_evidence(g.snapshot())


def test_duplicate_enqueue_and_delivery_rejected():
    g, source = setup()
    _replacement, ability = leave(g, source)
    g._enqueue_trigger(ability.event, source, FRAGMENT, TriggerEffect.LTB_MUTAGEN)
    assert not g.pending_triggers
    resolve(g)
    before = g.snapshot()
    with pytest.raises(ValueError):
        g._resolve_ltb_mutagen(ability)
    assert g.snapshot() == before
    assert len(tokens(g)) == 1


def test_new_incarnation_and_new_controller_do_not_relink_old_trigger():
    g, source = setup(1)
    replacement, old_ability = leave(g, source, "hand")
    returned = g.move_object(replacement, "battlefield", controller=0, reason="return")
    assert returned.object_id != source.object_id
    resolve(g)
    assert tokens(g)[0].controller == 1
    assert old_ability.source_id == source.object_id
    g.move_object(returned, "graveyard", reason="second_leave")
    g.check_state_based_actions()
    new_ability = g.stack[-1]
    assert new_ability.source_id == returned.object_id
    assert new_ability.event is not old_ability.event
    resolve(g)
    assert sorted(x.controller for x in tokens(g)) == [0, 1]
    Game.validate_ltb_mutagen_snapshot_evidence(g.snapshot())


@pytest.mark.parametrize(
    "tamper",
    [
        "source",
        "source_card",
        "replacement",
        "event",
        "event_registry",
        "trigger",
        "stack",
        "controller",
        "effect",
    ],
)
def test_fabricated_or_relinked_provenance_fails_before_token_creation(tamper):
    g, source = setup()
    replacement, ability = leave(g, source)
    if tamper == "source":
        g._objects[source.object_id] = copy.copy(source)
    elif tamper == "source_card":
        source.card = replace(source.card)
    elif tamper == "replacement":
        g._objects[replacement.object_id] = copy.copy(replacement)
    elif tamper == "event":
        ability.event = replace(ability.event, source_id="fake", subject_ids=("fake",))
    elif tamper == "event_registry":
        g._rules_events[ability.event.event_id] = replace(ability.event)
    elif tamper == "trigger":
        g._triggers[ability.trigger_id] = replace(g._triggers[ability.trigger_id])
    elif tamper == "stack":
        clone = copy.copy(ability)
        g.stack[-1] = clone
        g._objects[ability.object_id] = clone
    elif tamper == "controller":
        ability.controller = 1
    else:
        ability.effect = TriggerEffect.CREATE_TOKEN
    with pytest.raises(ValueError):
        resolve(g)
    assert not tokens(g)


def test_fabricated_leave_while_source_remains_on_battlefield_is_rejected():
    g, source = setup()
    event = g._new_rules_event(
        RulesEventKind.PERMANENT_LEFT, 0, (source.object_id,), source_id=source.object_id
    )
    with pytest.raises(ValueError, match="original departure"):
        g._enqueue_trigger(event, source, FRAGMENT, TriggerEffect.LTB_MUTAGEN)
    assert not g.pending_triggers and not tokens(g)


def test_nonbattlefield_zone_movement_and_etb_do_not_trigger():
    g, source = setup()
    g._process_creature_entered_triggers(source)
    assert not g.stack and not g.pending_triggers
    hand = g.set_hand_for_testing(0, [ZOO])[0]
    g.move_object(hand, "graveyard", reason="discard")
    assert not g.pending_triggers and not tokens(g)


def test_mutagen_activation_remains_unsupported():
    g, source = setup()
    leave(g, source)
    resolve(g)
    token = tokens(g)[0]
    c = g.interpreter.activated_ability_semantics(token.card, token.card.oracle_text)
    assert c is not None and not c.coverage.fully_supported
    assert g.interpreter.unsupported_fragments(token.card)
    snap = g.snapshot()
    assert not any(
        x["source_id"] == token.object_id for x in snap["conformance"]["executed_references"]
    )
    assert not any(x["source_id"] == token.object_id for x in snap["activated_abilities"])


@pytest.mark.parametrize(
    "field,value",
    [
        ("token_id", "fake"),
        ("source_id", "fake"),
        ("event_id", "fake"),
        ("token_owner", 1),
        ("token_oracle_text", ""),
        ("activation_supported", True),
    ],
)
def test_serialized_evidence_rejects_tampering(field, value):
    g, source = setup()
    leave(g, source)
    resolve(g)
    snap = json.loads(json.dumps(g.snapshot()))
    Game.validate_ltb_mutagen_snapshot_evidence(snap)
    row = next(e for e in snap["events"] if e["event"] == "ltb_mutagen_resolved")
    row[field] = value
    with pytest.raises(ValueError, match="does not reconstruct"):
        Game.validate_ltb_mutagen_snapshot_evidence(snap)


def test_evidence_survives_token_departure_and_rejects_missing_original_event():
    g, source = setup()
    leave(g, source)
    resolve(g)
    g.put_into_graveyard(tokens(g)[0])
    g.check_state_based_actions()
    snap = g.snapshot()
    Game.validate_ltb_mutagen_snapshot_evidence(snap)
    row = next(e for e in snap["events"] if e["event"] == "ltb_mutagen_resolved")
    snap["rules_event_evidence"] = [
        e for e in snap["rules_event_evidence"] if e["event_id"] != row["creation_event_id"]
    ]
    with pytest.raises(ValueError, match="does not reconstruct"):
        Game.validate_ltb_mutagen_snapshot_evidence(snap)
