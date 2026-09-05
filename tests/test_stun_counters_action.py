import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TriggerEffect

ROOT = Path(__file__).resolve().parents[1]
PLAINS = CardFact("Plains", "", 0, "Basic Land ? Plains")
BEAR = CardFact("Bear", "{1}{W}", 2, "Creature ? Bear", power=2, toughness=2)
FRAGMENT = CardInterpreter.ETB_TAP_STUN
SOURCE = CardFact(
    "Generic Scientist",
    "{2}{U}",
    3,
    "Creature ? Scientist",
    FRAGMENT,
    power=1,
    toughness=4,
    oracle_id="generic-scientist",
)


def setup(*, tapped=False, decline=False):
    game = Game(([PLAINS] * 30, [PLAINS] * 30), seed=1919)
    target = game.create_permanent(BEAR, 0, tapped=tapped)
    source = game.create_permanent(SOURCE, 1)
    game.stun_target_chooser = lambda *_args: None if decline else target.object_id
    game._process_creature_entered_triggers(source)
    return game, source, target, game.stack[-1]


def resolve(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def test_frozen_corpus_is_recognized_without_card_name_dispatch():
    corpus = json.loads((ROOT / "cardcade/card-model-0.6.json").read_text(encoding="utf-8"))
    assert "89793c8c-98a3-4621-ad3d-cfc5949c65da" in json.dumps(corpus)
    interpreter = CardInterpreter()
    assert interpreter.etb_tap_stun_semantic_coverage(SOURCE, FRAGMENT).fully_supported
    assert interpreter.unsupported_fragments(SOURCE) == ()
    assert FRAGMENT in json.dumps(corpus)


@pytest.mark.parametrize(
    "fragment",
    [
        FRAGMENT.replace("up to one", "two"),
        FRAGMENT.replace("a stun counter", "two stun counters", 1),
        FRAGMENT.replace("enters", "attacks", 1),
        FRAGMENT.replace("target creature", "target permanent", 1),
        FRAGMENT.replace("When this creature", "Whenever another creature", 1),
    ],
)
def test_near_neighbors_remain_unsupported(fragment):
    card = replace(SOURCE, oracle_text=fragment)
    assert CardInterpreter().etb_tap_stun_semantic_coverage(card, fragment) is None
    assert CardInterpreter().unsupported_fragments(card)


def test_noncreature_source_remains_unsupported():
    card = replace(SOURCE, type_line="Artifact")
    assert not CardInterpreter().etb_tap_stun_semantic_coverage(card, FRAGMENT).fully_supported


@pytest.mark.parametrize("tapped", [False, True])
def test_stack_priority_target_tap_counter_and_authoritative_history(tapped):
    game, source, target, ability = setup(tapped=tapped)
    assert ability.effect is TriggerEffect.ETB_TAP_STUN
    assert ability.target_id == target.object_id
    assert target.counters == {}
    assert game.priority_state is not None
    with pytest.raises(ValueError, match="all players pass"):
        game.resolve_top_of_stack()
    resolve(game)
    assert target.tapped and target.counters == {"stun": 1}
    event = next(e for e in game.events if e["event"] == "stun_etb_resolved")
    assert event["source_id"] == source.object_id
    assert event["target_id"] == target.object_id
    assert event["trigger_id"] == ability.trigger_id
    assert event["event_id"] == ability.event.event_id
    assert event["tapped_before"] is tapped
    assert event["counters_before"] == 0 and event["counters_after"] == 1
    assert game.events[event["placement_cursor"]]["event"] == "counters_placed"
    game.check_invariants()
    assert any(r["oracle_fragment"] == FRAGMENT for r in game._executed_conformance_references())


def test_optional_zero_target_resolves_without_effect():
    game, _, target, ability = setup(decline=True)
    assert ability.target_id is None
    resolve(game)
    assert not target.tapped and target.counters == {}
    assert next(e for e in game.events if e["event"] == "stun_etb_resolved")["applied"] is False


def test_next_turn_untap_is_replaced_then_later_untap_succeeds():
    game, _, target, _ = setup()
    resolve(game)
    game.begin_turn()
    assert target.tapped and target.counters.get("stun", 0) == 0
    game.untap_permanent(target)
    assert not target.tapped
    assert len([e for e in game.events if e["event"] == "stun_untap_replaced"]) == 1
    game.check_invariants()


def test_two_real_etb_triggers_accumulate_and_each_untap_removes_only_one():
    game, _, target, _ = setup()
    resolve(game)
    second = game.create_permanent(SOURCE, 1)
    game._process_creature_entered_triggers(second)
    resolve(game)
    assert target.counters["stun"] == 2
    for remaining in (1, 0):
        game.untap_permanent(target)
        assert target.tapped and target.counters.get("stun", 0) == remaining
    game.untap_permanent(target)
    assert not target.tapped
    game.check_invariants()


def test_already_untapped_permanent_does_not_consume_counter():
    game, _, target, _ = setup(decline=True)
    resolve(game)
    game.place_counters(target, "stun", 1, source_card=SOURCE.name, oracle_fragment=FRAGMENT)
    game.untap_permanent(target)
    assert target.counters["stun"] == 1 and not target.tapped


def test_source_departure_does_not_cancel_stacked_trigger():
    game, source, target, _ = setup()
    game.destroy(source)
    resolve(game)
    assert target.tapped and target.counters["stun"] == 1
    game.check_invariants()


def test_target_departure_does_not_retarget_replacement_incarnation():
    game, _, target, _ = setup()
    game.destroy(target)
    replacement = game.create_permanent(BEAR, 0)
    resolve(game)
    assert replacement.counters == {} and not replacement.tapped
    assert next(e for e in game.events if e["event"] == "stun_etb_resolved")["applied"] is False


def test_stun_state_does_not_transfer_through_zone_change():
    game, _, target, _ = setup()
    resolve(game)
    hand = game.move_object(target, "hand", reason="test_return")
    replacement = game.move_object(hand, "battlefield", reason="test_reenter")
    assert replacement.object_id != target.object_id
    assert replacement.counters == {}
    game.check_invariants()


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_id", "fabricated"),
        ("target_id", "fabricated"),
        ("trigger_id", "fabricated"),
        ("controller", 0),
        ("oracle_fragment", "wrong"),
    ],
)
def test_mutated_trigger_fails_closed(field, value):
    game, _, target, ability = setup()
    setattr(ability, field, value)
    with pytest.raises((ValueError, AssertionError), match="stun"):
        resolve(game)
    assert target.counters == {} and not target.tapped


@pytest.mark.parametrize("which", ["source", "target", "ability"])
def test_fabricated_same_id_object_cannot_relink(which):
    game, source, target, ability = setup()
    original = {"source": source, "target": target, "ability": ability}[which]
    forged = copy.copy(original)
    game._objects[original.object_id] = forged
    if which == "ability":
        game.stack[-1] = forged
    else:
        field = game.players[original.controller].battlefield
        field[field.index(original)] = forged
    with pytest.raises((ValueError, AssertionError), match="stun"):
        resolve(game)
    assert target.counters == {}


def test_fabricated_target_choice_rejected():
    game = Game(([PLAINS] * 30, [PLAINS] * 30), stun_target_chooser=lambda *_: "fabricated")
    source = game.create_permanent(SOURCE, 0)
    with pytest.raises(ValueError, match="listed creature"):
        game._process_creature_entered_triggers(source)
    assert source.counters == {} and not source.tapped


def test_wrong_zone_and_fabricated_untap_objects_fail_closed():
    game, _, target, _ = setup()
    resolve(game)
    with pytest.raises(ValueError, match="authoritative"):
        game.untap_permanent(copy.copy(target))
    game.destroy(target)
    with pytest.raises(ValueError, match="authoritative"):
        game.untap_permanent(target)


@pytest.mark.parametrize(
    "kind", ["stun_target_selected", "stun_etb_resolved", "counters_placed", "stun_untap_replaced"]
)
def test_modified_history_cannot_claim_authenticated_execution(kind):
    game, _, target, _ = setup()
    resolve(game)
    game.untap_permanent(target)
    event = next(e for e in game.events if e["event"] == kind)
    event["quantity" if kind == "counters_placed" else "target_id"] = "fabricated"
    with pytest.raises(ValueError, match="history"):
        game._executed_conformance_references()


def test_deterministic_replay():
    snapshots = []
    for _ in range(2):
        game, _, target, _ = setup()
        resolve(game)
        game.begin_turn()
        game.untap_permanent(target)
        game.check_invariants()
        snapshots.append(json.dumps(game.snapshot(), sort_keys=True))
    assert snapshots[0] == snapshots[1]


def test_target_becoming_noncreature_before_resolution_gets_no_effect():
    game, _, target, _ = setup()
    target.type_line_override = "Artifact"
    resolve(game)
    assert not target.tapped and target.counters == {}
    game.check_invariants()


def test_target_controller_change_does_not_invalidate_unrestricted_creature_target():
    game, _, target, _ = setup()
    game.players[0].battlefield.remove(target)
    target.controller = 1
    game.players[1].battlefield.append(target)
    resolve(game)
    assert target.tapped and target.counters["stun"] == 1
    game.check_invariants()


def test_trigger_effect_relabeling_cannot_bypass_stun_provenance():
    game, _, target, ability = setup()
    ability.effect = TriggerEffect.ALLIANCE_PT
    with pytest.raises((ValueError, AssertionError), match="stun"):
        resolve(game)
    assert target.counters == {}


def test_trigger_event_replacement_is_rejected():
    game, _, target, ability = setup()
    ability.event = replace(ability.event, subject_ids=(target.object_id,))
    with pytest.raises((ValueError, AssertionError), match="stun"):
        resolve(game)
    assert target.counters == {}


def test_relinking_to_another_real_target_fails_closed():
    game, source, target, ability = setup()
    ability.target_id = source.object_id
    with pytest.raises((ValueError, AssertionError), match="stun"):
        resolve(game)
    assert target.counters == {} and source.counters == {}


def test_counter_state_tampering_is_detected():
    game, _, target, _ = setup()
    resolve(game)
    target.counters["stun"] = 5
    with pytest.raises(AssertionError, match="stun counter state"):
        game.check_invariants()


@pytest.mark.parametrize("tamper", ["remove_history", "tap", "placement", "source", "removal"])
def test_serialized_stage_evidence_requires_matching_stun_history(tamper):
    from tmnt_design_studio.stage002 import _authoritative_execution_index

    game, _, target, _ = setup()
    resolve(game)
    game.untap_permanent(target)
    snapshot = json.loads(json.dumps(game.snapshot()))
    _authoritative_execution_index(snapshot)
    if tamper == "remove_history":
        snapshot.pop("stun_history")
    else:
        kind = {
            "tap": "stun_target_tapped",
            "placement": "counters_placed",
            "source": "trigger_resolved",
            "removal": "stun_untap_replaced",
        }[tamper]
        event = next(e for e in snapshot["events"] if e["event"] == kind)
        event["source_id"] = "fabricated"
    with pytest.raises(ValueError, match="stun"):
        _authoritative_execution_index(snapshot)


def test_real_frozen_card_creates_supported_trigger():
    from tmnt_design_studio.engine07 import load_facts
    from tmnt_design_studio.stage002 import load_catalog

    fact = load_facts(load_catalog(ROOT), {"Utrom Scientists"})["Utrom Scientists"]
    game = Game(([PLAINS] * 30, [PLAINS] * 30), seed=19)
    source = game.create_permanent(fact, 0)
    game._process_creature_entered_triggers(source)
    assert game.stack[-1].oracle_fragment == FRAGMENT
    resolve(game)
    assert source.counters["stun"] == 1
    game.check_invariants()


@pytest.mark.parametrize("keyword", ["Hexproof", "Shroud", "Ward {2}", "Protection from blue"])
def test_absent_targeting_subsystems_fail_closed(keyword):
    game = Game(([PLAINS] * 30, [PLAINS] * 30), seed=19)
    target = game.create_permanent(replace(BEAR, oracle_text=keyword), 0)
    source = game.create_permanent(SOURCE, 1)
    game.stun_target_chooser = lambda *_: target.object_id
    with pytest.raises(ValueError, match="targeting dependency"):
        game._process_creature_entered_triggers(source)
    assert target.counters == {} and not target.tapped


def test_live_trigger_resolution_log_is_also_authenticated():
    game, _, _, _ = setup()
    resolve(game)
    event = next(e for e in game.events if e["event"] == "trigger_resolved")
    event["source_id"] = "fabricated"
    with pytest.raises(ValueError, match="history"):
        game._executed_conformance_references()
