import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    CardFact,
    Game,
    RulesEventKind,
    TriggeredAbilityObject,
    TriggerEffect,
)
from tmnt_design_studio.semantic_coverage import SemanticCoverage

ROOT = Path(__file__).resolve().parents[1]
PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
FRAGMENT = "When this creature dies, draw a card."
BUZZ = CardFact(
    "Renamed Self-Death Fixture",
    "{2}",
    2,
    "Artifact Creature — Robot",
    FRAGMENT,
    power=2,
    toughness=2,
)
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)


def game(*, library_size=12):
    current = Game(([PLAINS] * library_size, [PLAINS] * 20), seed=131)
    current.begin_turn()
    source = current.create_permanent(BUZZ, 0, summoning_sick=False)
    return current, source


def pass_priority(current):
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            option = current.legal_priority_actions(current.priority_state.player_index)[0]
            current.execute_priority_action(option)


def catalog():
    return load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )


def test_exact_oracle_grammar_is_generic_and_fully_supported():
    coverage = CardInterpreter().dies_draw_semantic_coverage(BUZZ, FRAGMENT)
    assert coverage == SemanticCoverage(True, True, True, ())
    renamed = replace(BUZZ, name="No Source-Name Dependency")
    assert CardInterpreter().dies_draw_semantic_coverage(renamed, FRAGMENT) == coverage


@pytest.mark.parametrize(
    "fragment",
    [
        "When another creature dies, draw a card.",
        "When this creature dies, draw two cards.",
        "When this creature dies, you may draw a card.",
        "When this creature dies, target player draws a card.",
        "When this creature dies, draw a card, then discard a card.",
        "Whenever this creature dies, draw a card.",
    ],
)
def test_near_neighbor_death_triggers_remain_unrecognized(fragment):
    assert CardInterpreter().dies_draw_semantic_coverage(BUZZ, fragment) is None


def test_noncreature_exact_text_is_recognized_but_not_executable():
    noncreature = CardFact("Relic", "{2}", 2, "Artifact", FRAGMENT)
    coverage = CardInterpreter().dies_draw_semantic_coverage(noncreature, FRAGMENT)
    assert coverage == SemanticCoverage(
        False, False, False, ("dies_draw_source_is_not_a_creature",)
    )


def test_death_enqueues_authoritative_trigger_then_priority_delivers_draw():
    current, source = game()
    hand_before = len(current.players[0].hand)

    graveyard = current.put_into_graveyard(source, state_based_action="lethal_damage")
    assert graveyard.object_id != source.object_id
    assert len(current.pending_triggers) == 1
    current.check_state_based_actions()

    ability = current.stack[-1]
    assert isinstance(ability, TriggeredAbilityObject)
    assert ability.effect is TriggerEffect.DIES_DRAW
    assert ability.source_id == source.object_id
    assert ability.event.kind is RulesEventKind.CREATURE_DIED
    assert ability.event.last_known_battlefield == ((source.object_id, 0, BUZZ.type_line, True),)
    assert current.priority_state is not None
    assert len(current.players[0].hand) == hand_before

    pass_priority(current)

    assert len(current.players[0].hand) == hand_before + 1
    names = [item["event"] for item in current.events]
    assert names.index("permanent_to_graveyard") < names.index("trigger_stacked")
    assert names.index("trigger_stacked") < names.index("priority_granted")
    action_draw = max(index for index, name in enumerate(names) if name == "card_drawn")
    assert names.index("priority_passed") < action_draw
    assert action_draw < names.index("trigger_resolved")


def test_trigger_uses_last_known_controller_and_survives_source_departure():
    current, source = game()
    current.change_controller(source, 1)
    hand_before = len(current.players[1].hand)
    current.put_into_graveyard(source)
    current.check_state_based_actions()
    ability = current.stack[-1]
    assert isinstance(ability, TriggeredAbilityObject)
    assert ability.controller == 1
    assert source.zone == "former"
    pass_priority(current)
    assert len(current.players[1].hand) == hand_before + 1


def test_non_graveyard_departure_does_not_trigger_dies():
    current, source = game()
    current.move_object(source, "hand", reason="return")
    current.check_state_based_actions()
    assert current.stack == []
    assert current.pending_triggers == []
    assert not any(item["event"] == "trigger_pending" for item in current.events)


def test_printed_creature_that_is_authoritatively_noncreature_does_not_die():
    current, source = game()
    source.type_line_override = "Artifact — Robot"
    current.put_into_graveyard(source, state_based_action="destroyed_noncreature")
    current.check_state_based_actions()

    assert current.stack == []
    assert current.pending_triggers == []
    assert not any(
        item.get("rules_event") == RulesEventKind.CREATURE_DIED.value for item in current.events
    )
    assert not any(item["event"] == "trigger_pending" for item in current.events)


def test_fabricated_last_known_creature_characteristics_fail_closed():
    current, source = game()
    hand_before = len(current.players[0].hand)
    current.put_into_graveyard(source)
    current.check_state_based_actions()
    ability = current.stack[-1]
    assert isinstance(ability, TriggeredAbilityObject)
    malformed = replace(
        ability.event,
        last_known_battlefield=((source.object_id, 0, "Artifact — Robot", False),),
    )
    current._rules_events[malformed.event_id] = malformed
    ability.event = malformed

    with pytest.raises(AssertionError, match="death provenance"):
        current.check_invariants()
    with pytest.raises(ValueError, match="death provenance"):
        current._resolve_triggered_ability(ability)
    assert len(current.players[0].hand) == hand_before


def test_fabricated_or_relinked_death_provenance_fails_invariant_and_resolution():
    current, source = game()
    current.put_into_graveyard(source)
    current.check_state_based_actions()
    ability = current.stack[-1]
    assert isinstance(ability, TriggeredAbilityObject)
    original = ability.event
    ability.event = replace(original, source_id="fabricated", subject_ids=("fabricated",))

    with pytest.raises(AssertionError, match="death provenance"):
        current.check_invariants()
    with pytest.raises(ValueError, match="death provenance"):
        current._resolve_triggered_ability(ability)


def test_borrowed_death_event_from_another_source_cannot_authenticate():
    current, first = game()
    second = current.create_permanent(BUZZ, 0, summoning_sick=False)
    current.put_into_graveyard(first)
    current.put_into_graveyard(second)
    current.check_state_based_actions()
    first_ability, second_ability = current.stack
    assert isinstance(first_ability, TriggeredAbilityObject)
    assert isinstance(second_ability, TriggeredAbilityObject)
    second_ability.event = first_ability.event
    with pytest.raises(AssertionError, match="death provenance"):
        current.check_invariants()


def test_draw_failure_finishes_trigger_then_loses_at_sba_boundary():
    current, source = game(library_size=7)
    assert current.players[0].library == []
    current.put_into_graveyard(source)
    current.check_state_based_actions()
    pass_priority(current)

    names = [item["event"] for item in current.events]
    assert names.index("draw_failed") < names.index("trigger_resolved")
    assert names.index("trigger_resolved") < names.index("player_lost")
    assert current.players[0].lost
    assert current.players[0].loss_reason == "draw_from_empty_library"


def test_simultaneous_deaths_create_distinct_events_stack_objects_and_draws():
    current, first = game()
    second = current.create_permanent(BUZZ, 0, summoning_sick=False)
    hand_before = len(current.players[0].hand)
    current.put_into_graveyard(first)
    current.put_into_graveyard(second)
    current.check_state_based_actions()

    abilities = tuple(current.stack)
    assert len(abilities) == 2
    assert len({item.object_id for item in abilities}) == 2
    assert len({item.event.event_id for item in abilities}) == 2
    pass_priority(current)
    assert len(current.players[0].hand) == hand_before + 2


def test_exact_supported_fragment_is_not_registered_as_unsupported():
    interpreter = CardInterpreter()
    assert interpreter.unsupported_fragments(BUZZ) == ()
    compound = replace(
        BUZZ, oracle_text="When this creature dies, draw a card, then discard a card."
    )
    assert interpreter.unsupported_fragments(compound) == (
        (compound.oracle_text, "oracle_ability_not_implemented"),
    )


def test_authoritative_corpus_membership_and_digest_are_locked():
    interpreter = CardInterpreter()
    seen = set()
    members = []
    for card in sorted(catalog().cards, key=lambda item: (item.name, item.oracle_id)):
        if card.oracle_id in seen:
            continue
        seen.add(card.oracle_id)
        for fragment in interpreter.fragments(card):
            if interpreter.dies_draw_semantic_coverage(card, fragment) is not None:
                members.append((card.oracle_id, card.name, fragment))
    assert members == [
        (
            "434e720f-2bfa-49b6-a5ac-fe0c0b24764d",
            "Buzz Bots",
            FRAGMENT,
        )
    ]
    encoded = json.dumps(members, ensure_ascii=False, separators=(",", ":")).encode()
    assert hashlib.sha256(encoded).hexdigest() == (
        "f3b318c396eb9d7e49486baba973807e2d7f0554fd384be65620f4af815685fa"
    )


def test_frozen_roster_membership_and_digest_are_locked():
    roster = json.loads((ROOT / "cardcade/roster-0.2.json").read_text(encoding="utf-8"))
    decklists = {deck["id"]: deck["decklist"] for deck in roster["decks"]}
    members = []
    for deck_id in ("april_oneil", "donatello", "krang"):
        lines = (ROOT / decklists[deck_id]).read_text(encoding="utf-8").splitlines()
        buzz_line = next(line for line in lines if line.endswith(" Buzz Bots"))
        members.append((deck_id, "Buzz Bots", int(buzz_line.split()[0])))
    assert members == [
        ("april_oneil", "Buzz Bots", 4),
        ("donatello", "Buzz Bots", 4),
        ("krang", "Buzz Bots", 4),
    ]
    encoded = json.dumps(members, separators=(",", ":")).encode()
    assert hashlib.sha256(encoded).hexdigest() == (
        "c1e9f438d3c27a3c72ca6f4ce6b4ddd7f440cbb9292147c01de7afb755e101b5"
    )


def test_duplicate_execution_evidence_is_deterministic():
    snapshots = []
    for _ in range(2):
        current, source = game()
        current.put_into_graveyard(source)
        current.check_state_based_actions()
        pass_priority(current)
        snapshots.append(current.snapshot())
    assert snapshots[0] == snapshots[1]
