import json
from pathlib import Path

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    CardFact,
    Game,
    TemporaryKeyword,
    TriggeredAbilityObject,
    TriggerEffect,
    TurnStep,
)

ROOT = Path(__file__).resolve().parents[1]
PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Bear", "{1}{W}", 2, "Creature — Bear", power=2, toughness=2)
FRAGMENT = (
    "Alliance — Whenever another creature you control enters, Generic Bat gains your choice "
    "of flying, menace, or haste until end of turn."
)
SOURCE = CardFact(
    "Generic Bat",
    "{1}{R}",
    2,
    "Creature — Bat Mutant",
    FRAGMENT,
    power=1,
    toughness=2,
    oracle_id="generic-bat",
)


def game(*, choice="flying"):
    return Game(
        ([PLAINS] * 30, [PLAINS] * 30),
        seed=1818,
        temporary_keyword_chooser=lambda _controller, _source_id, _choices: choice,
    )


def create_trigger(current, source):
    entering = current.create_permanent(BEAR, source.controller, summoning_sick=False)
    current._process_creature_entered_triggers(entering, defer_triggers=True)
    ability = current.stack[-1]
    assert isinstance(ability, TriggeredAbilityObject)
    assert ability.effect is TriggerEffect.ALLIANCE_TEMPORARY_KEYWORD_CHOICE
    return ability


def pass_priority(current):
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            option = current.legal_priority_actions(current.priority_state.player_index)[0]
            current.execute_priority_action(option)


@pytest.mark.parametrize("choice", ["flying", "menace", "haste"])
def test_each_exact_choice_is_selected_granted_and_recorded(choice):
    current = game(choice=choice)
    source = current.create_permanent(SOURCE, 0, summoning_sick=True)
    ability = create_trigger(current, source)

    current.resolve_top_of_stack()

    assert [effect.keyword.value for effect in source.temporary_keyword_effects] == [choice]
    assert current.has_temporary_keyword(source, TemporaryKeyword(choice))
    event = next(
        item for item in current.events if item["event"] == "temporary_keyword_choice_resolved"
    )
    assert event == {
        "turn": 0,
        "phase": "setup",
        "step": "setup",
        "event": "temporary_keyword_choice_resolved",
        "stack_object_id": ability.object_id,
        "trigger_id": ability.trigger_id,
        "event_id": ability.event.event_id,
        "source_id": source.object_id,
        "target_id": source.object_id,
        "controller": 0,
        "choices": ["flying", "menace", "haste"],
        "selected_keyword": choice,
        "duration": "until_end_of_turn",
        "oracle_fragment": FRAGMENT,
        "applied": True,
    }
    current.check_invariants()


def test_exactly_one_keyword_is_granted_and_haste_is_observed_by_attack_eligibility():
    current = game(choice="haste")
    current.begin_turn()
    source = current.create_permanent(SOURCE, 0, summoning_sick=True)
    create_trigger(current, source)

    current.resolve_top_of_stack()

    assert len(source.temporary_keyword_effects) == 1
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    assert source in current.legal_attackers(0)


def test_trigger_uses_normal_stack_priority_and_pass_resolution_lifecycle():
    current = game(choice="menace")
    source = current.create_permanent(SOURCE, 0)
    entering = current.create_permanent(BEAR, 0)

    current._process_creature_entered_triggers(entering)

    assert isinstance(current.stack[-1], TriggeredAbilityObject)
    assert current.priority_state is not None
    assert source.temporary_keyword_effects == []
    pass_priority(current)
    assert current.stack == []
    assert current.priority_state is None
    assert current.has_temporary_keyword(source, TemporaryKeyword.MENACE)


def test_unsupported_choice_is_rejected_before_grant():
    current = game(choice="vigilance")
    source = current.create_permanent(SOURCE, 0)
    create_trigger(current, source)

    with pytest.raises(ValueError, match="available keyword"):
        current.resolve_top_of_stack()

    assert source.temporary_keyword_effects == []


def test_temporary_grant_expires_during_cleanup():
    current = game(choice="flying")
    current.begin_turn()
    source = current.create_permanent(SOURCE, 0)
    create_trigger(current, source)
    current.resolve_top_of_stack()
    assert current.has_temporary_keyword(source, TemporaryKeyword.FLYING)

    current.advance_to(TurnStep.COMBAT_DAMAGE)
    current.resolve_combat_damage()
    current.advance_to(TurnStep.CLEANUP)

    assert not current.has_temporary_keyword(source, TemporaryKeyword.FLYING)
    assert source.temporary_keyword_effects == []


def test_source_departure_and_replacement_incarnation_cannot_inherit_grant():
    current = game(choice="menace")
    source = current.create_permanent(SOURCE, 0)
    create_trigger(current, source)
    current.destroy(source)
    replacement = current.create_permanent(SOURCE, 0)

    current.resolve_top_of_stack()

    assert source.temporary_keyword_effects == []
    assert replacement.temporary_keyword_effects == []
    event = next(
        item for item in current.events if item["event"] == "temporary_keyword_choice_resolved"
    )
    assert event["source_id"] == source.object_id
    assert event["applied"] is False


def test_fabricated_and_wrong_zone_source_cannot_receive_or_relink_effect():
    current = game(choice="flying")
    source = current.create_permanent(SOURCE, 0)
    ability = create_trigger(current, source)
    ability.source_id = "object-fabricated"

    with pytest.raises(ValueError, match="Alliance provenance"):
        current.resolve_top_of_stack()

    assert source.temporary_keyword_effects == []


def test_identical_state_and_choice_produce_identical_authoritative_history():
    histories = []
    for _ in range(2):
        current = game(choice="flying")
        source = current.create_permanent(SOURCE, 0)
        create_trigger(current, source)
        current.resolve_top_of_stack()
        histories.append(
            [
                item
                for item in current.events
                if item["event"]
                in {
                    "rules_event",
                    "trigger_pending",
                    "trigger_stacked",
                    "temporary_keyword_choice_resolved",
                    "trigger_resolved",
                }
            ]
        )

    assert histories[0] == histories[1]


@pytest.mark.parametrize(
    "fragment",
    [
        "Alliance — Whenever another creature you control enters, Generic Bat gains flying, "
        "menace, or haste until end of turn.",
        "Alliance — Whenever another creature you control enters, Generic Bat gains your choice "
        "of flying, menace, or vigilance until end of turn.",
        "Alliance — Whenever another creature you control enters, Generic Bat gains your choice "
        "of flying, menace, or haste.",
        "Whenever another creature you control enters, Generic Bat gains your choice of flying, "
        "menace, or haste until end of turn.",
    ],
)
def test_near_neighbor_grammar_remains_unsupported(fragment):
    card = CardFact("Generic Bat", "{1}{R}", 2, "Creature — Bat", fragment, 1, 2)
    interpreter = CardInterpreter()

    assert interpreter.temporary_keyword_choice_semantic_coverage(card, fragment) is None
    assert interpreter.unsupported_fragments(card)


def test_wrong_self_reference_is_recognized_but_not_executable():
    fragment = FRAGMENT.replace("Generic Bat gains", "Unrelated Bat gains")
    card = CardFact("Generic Bat", "{1}{R}", 2, "Creature — Bat", fragment, 1, 2)

    semantics = CardInterpreter().temporary_keyword_choice_semantic_coverage(card, fragment)

    assert semantics is not None
    assert not semantics.coverage.fully_supported
    assert semantics.limitations == ("temporary_keyword_choice_source_mismatch",)


def test_frozen_corpus_member_and_exact_oracle_fragment_are_authoritative():
    cards = json.loads((ROOT / "cardcade/card-model-0.6.json").read_text(encoding="utf-8"))["cards"]
    wingnut = cards["Wingnut, Bat on the Belfry"]
    exact_fragment = wingnut["oracle_text"].splitlines()[0]

    semantics = CardInterpreter().temporary_keyword_choice_semantic_coverage(
        CardFact(
            "Wingnut, Bat on the Belfry",
            wingnut["mana_cost"],
            wingnut["mana_value"],
            wingnut["type_line"],
            wingnut["oracle_text"],
            keywords=tuple(wingnut["keywords"]),
            oracle_id=wingnut["oracle_id"],
        ),
        exact_fragment,
    )

    assert exact_fragment == (
        "Alliance — Whenever another creature you control enters, Wingnut gains your choice of "
        "flying, menace, or haste until end of turn."
    )
    assert semantics is not None
    assert semantics.program.choices == ("flying", "menace", "haste")
    assert semantics.coverage.fully_supported
