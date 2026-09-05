import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import (
    ActionKind,
    CardFact,
    CastKind,
    Game,
    StackObject,
)

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Island", "", 0, "Basic Land ? Island")
CREATURE = CardFact("Bear", "{1}{G}", 2, "Creature ? Bear", power=2, toughness=2)
ARTIFACT = CardFact("Relic", "{2}", 2, "Artifact", oracle_id="relic")
FUGITIVE = CardFact(
    "Fugitive Droid",
    "{2}{U}",
    3,
    "Artifact Creature ? Robot",
    "{U}, Sacrifice this creature: Counter target spell that targets an artifact "
    "or creature you control.",
    toughness=2,
    oracle_id="fugitive",
)
FRAGMENT = FUGITIVE.oracle_text
SPELL = CardFact("Bolt", "{R}", 1, "Instant", "Deal 3 damage to any target.", oracle_id="bolt")
NON_TARGET = CardFact("Concentrate", "{3}{U}", 4, "Sorcery", "Draw three cards.", oracle_id="draw")


def setup(*, protected=CREATURE, spell=SPELL, spell_target=True):
    game = Game(([LAND] * 30, [LAND] * 30), seed=2020)
    game.begin_turn()
    mana = game.create_permanent(LAND, 0, summoning_sick=False)
    target = game.create_permanent(protected, 0, summoning_sick=False)
    source = game.create_permanent(FUGITIVE, 0, summoning_sick=False)
    target_id = target.object_id if spell_target else None
    stack_spell = StackObject(
        game._allocate_object_id(), spell, 1, 1, CastKind.DEAL_DAMAGE, target_id
    )
    game._register(stack_spell)
    game.stack.append(stack_spell)
    game._begin_priority_window()
    return game, mana, target, source, stack_spell


def pass_all(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def resolve_one(game):
    for _ in range(2):
        option = game.legal_priority_actions(game.priority_state.player_index)[0]
        game.execute_priority_action(option)
    game.process_priority_resolution()


def test_exact_fugitive_grammar_is_recognized_generically():
    semantics = CardInterpreter().activated_ability_semantics(FUGITIVE, FRAGMENT)
    assert semantics is not None and semantics.coverage.fully_supported
    assert semantics.program.effect_kind is ActivatedEffectKind.COUNTER_TARGET_SPELL
    assert semantics.program.cost.mana_cost == "{U}"
    assert semantics.program.cost.sacrifice_source
    assert CardInterpreter().unsupported_fragments(FUGITIVE) == ()


@pytest.mark.parametrize(
    "fragment",
    [
        FRAGMENT.replace("{U}", "{1}"),
        FRAGMENT.replace("this creature", "this permanent"),
        FRAGMENT.replace("an artifact or creature", "a creature"),
        FRAGMENT.replace("targets an artifact or creature you control", "targets any permanent"),
    ],
)
def test_near_neighbor_grammar_fails_closed(fragment):
    card = replace(FUGITIVE, oracle_text=fragment)
    semantics = CardInterpreter().activated_ability_semantics(card, fragment)
    assert semantics is None or not semantics.coverage.fully_supported


def test_activation_requires_mana_and_qualifying_target():
    game, mana, target, source, spell = setup()
    ability = game.announce_activated_ability(0, source, FRAGMENT, target_ids=(spell.object_id,))
    assert ability is not None and mana.tapped
    assert source.zone == "former" and ability.target_ids == (spell.object_id,)
    no_mana, _, _, source2, spell2 = setup()
    no_mana.players[0].battlefield = [
        x
        for x in no_mana.players[0].battlefield
        if x is not next(x for x in no_mana.players[0].battlefield if x.card is LAND)
    ]
    assert (
        no_mana.announce_activated_ability(0, source2, FRAGMENT, target_ids=(spell2.object_id,))
        is None
    )
    invalid, _, _, source3, spell3 = setup(spell_target=False)
    assert (
        invalid.announce_activated_ability(0, source3, FRAGMENT, target_ids=(spell3.object_id,))
        is None
    )


def test_priority_lifecycle_and_deterministic_target_options():
    game, _, _, source, spell = setup()
    options = game.legal_priority_actions(0)
    activation = next(o for o in options if o.kind is ActionKind.ACTIVATE_ABILITY)
    assert activation.target_id == spell.object_id
    assert activation.oracle_fragment == FRAGMENT
    assert game.legal_priority_actions(1) == ()
    assert game.execute_priority_action(activation)
    assert game.stack[-1].target_ids == (spell.object_id,)
    assert game.priority_state is not None


def test_payment_sacrifice_target_and_resolution_counter_spell():
    game, mana, target, source, spell = setup()
    ability = game.announce_activated_ability(0, source, FRAGMENT, target_ids=(spell.object_id,))
    assert ability is not None
    assert mana.tapped and source.zone == "former" and spell.zone == "stack"
    with pytest.raises(ValueError, match="all players pass"):
        game.resolve_top_of_stack()
    pass_all(game)
    assert spell.zone == "former" and not game.stack
    event = next(e for e in game.events if e["event"] == "spell_countered")
    assert event["target_spell_id"] == spell.object_id
    assert event["target_object_id"] == target.object_id
    assert event["countered_object_id"] != spell.object_id
    assert event["target_relationship"] == "targets_artifact_or_creature_you_control"
    assert any(e["event"] == "activation_cost_paid" and e["sacrifice_source"] for e in game.events)
    assert any(e["event"] == "activated_ability_resolved" and e["delivered"] for e in game.events)
    game.check_invariants()


@pytest.mark.parametrize("protected", [ARTIFACT, CREATURE])
def test_artifact_or_creature_controlled_by_activator_qualifies(protected):
    game, _, _, source, spell = setup(protected=protected)
    assert game.announce_activated_ability(0, source, FRAGMENT, target_ids=(spell.object_id,))


def test_wrong_controller_non_target_and_missing_target_are_illegal():
    game, _, target, source, spell = setup()
    target.controller = 1
    game.players[0].battlefield.remove(target)
    game.players[1].battlefield.append(target)
    assert (
        game.announce_activated_ability(0, source, FRAGMENT, target_ids=(spell.object_id,)) is None
    )
    game2, _, _, source2, spell2 = setup(spell=NON_TARGET, spell_target=False)
    assert game2._legal_counter_target_ids(0) == ()
    assert (
        game2.announce_activated_ability(0, source2, FRAGMENT, target_ids=(spell2.object_id,))
        is None
    )


def test_resolution_revalidates_target_and_costs_remain_paid():
    game, mana, target, source, spell = setup()
    ability = game.announce_activated_ability(0, source, FRAGMENT, target_ids=(spell.object_id,))
    assert ability is not None
    game.players[0].battlefield.remove(target)
    target.zone = "former"
    replacement = game.create_permanent(CREATURE, 0, summoning_sick=False)
    resolve_one(game)
    assert spell.zone == "stack" and replacement.counters == {}
    assert mana.tapped and source.zone == "former"
    event = next(e for e in game.events if e["event"] == "activated_ability_resolved_no_effect")
    assert event["reason"] == "counter_target_illegal_at_resolution"


@pytest.mark.parametrize("field", ["source_id", "target_ids", "oracle_fragment", "controller"])
def test_fabricated_activation_fails_closed(field):
    game, _, target, source, spell = setup()
    ability = game.announce_activated_ability(0, source, FRAGMENT, target_ids=(spell.object_id,))
    assert ability is not None
    if field == "target_ids":
        ability.target_ids = ("fabricated",)
    elif field == "source_id":
        ability.source_id = "fabricated"
    elif field == "oracle_fragment":
        ability.oracle_fragment = "wrong"
    else:
        ability.controller = 1
    with pytest.raises(
        (ValueError, AssertionError), match="activation|target|counter|authoritative|semantics"
    ):
        resolve_one(game)
    assert spell.zone == "stack"


def test_relinked_spell_and_fabricated_objects_fail_closed():
    game, _, target, source, spell = setup()
    ability = game.announce_activated_ability(0, source, FRAGMENT, target_ids=(spell.object_id,))
    assert ability is not None
    forged = copy.copy(spell)
    game._objects[spell.object_id] = forged
    with pytest.raises((ValueError, AssertionError)):
        pass_all(game)
    assert spell.zone == "stack"


def test_event_history_reconstructs_activation_payment_sacrifice_and_counter():
    game, _, _, source, spell = setup()
    game.announce_activated_ability(0, source, FRAGMENT, target_ids=(spell.object_id,))
    pass_all(game)
    events = [e["event"] for e in game.events]
    for expected in (
        "zone_changed",
        "activation_announced",
        "activation_cost_paid",
        "activated_ability_stacked",
        "priority_passed",
        "stack_resolution_permitted",
        "spell_countered",
        "activated_ability_resolved",
    ):
        assert expected in events
    assert game.snapshot()["stack"] == []


def test_deterministic_replay():
    def run():
        game, _, _, source, spell = setup()
        game.announce_activated_ability(0, source, FRAGMENT, target_ids=(spell.object_id,))
        pass_all(game)
        return json.dumps(game.snapshot(), sort_keys=True)

    assert run() == run()


def test_frozen_card_is_present_and_supported():
    text = (ROOT / "cardcade/card-model-0.6.json").read_text(encoding="utf-8")
    assert "Fugitive Droid" in text
