"""Generic sacrifice-for-targeted-damage activation, with a frozen Oracle fixture."""

from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, RulesEventKind

ROOT = Path(__file__).resolve().parents[1]
MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land — Mountain", "({T}: Add {R}.)")
REACTOR = CardFact(
    "Experimental Reactor",
    "{1}{R}",
    2,
    "Artifact",
    "{4}{R}, Sacrifice this artifact: It deals 3 damage to target creature.",
)
TARGET = CardFact("Test Creature", "{2}{G}", 3, "Creature — Bear", power=2, toughness=3)
PROTECTED = CardFact("Protected Creature", "{2}{G}", 3, "Creature — Bear", "Hexproof", 2, 3)


def setup(seed=71, *, mana=5):
    game = Game(([MOUNTAIN] * 60, [MOUNTAIN] * 60), seed=seed)
    game.begin_turn()
    for _ in range(mana):
        game.create_permanent(MOUNTAIN, 0, summoning_sick=False)
    source = game.create_permanent(REACTOR, 0)
    target = game.create_permanent(TARGET, 1)
    return game, source, target


def resolve(game):
    for _ in range(2):
        action = game.legal_priority_actions(game.priority_state.player_index)[0]
        assert action.kind is ActionKind.PASS_PRIORITY
        game.execute_priority_action(action)
    game.process_priority_resolution()


def test_frozen_oracle_fixture_and_generic_shape():
    catalog = load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    card = catalog.resolve_name("Mouser Foundry")
    fragment = next(line for line in CardInterpreter().fragments(card) if "deals 3 damage" in line)
    semantics = CardInterpreter().activated_ability_semantics(card, fragment)
    assert semantics is not None and semantics.coverage.fully_supported
    assert semantics.program.effect_kind is ActivatedEffectKind.DEAL_FIXED_DAMAGE_TO_TARGET_CREATURE
    assert (
        fragment,
        "damage_activation_context_not_implemented",
    ) not in CardInterpreter().unsupported_fragments(card)
    generic = CardInterpreter().activated_ability_semantics(REACTOR, REACTOR.oracle_text)
    assert generic is not None and generic.coverage.fully_supported


def test_mana_sacrifice_target_damage_lethal_sba_and_event_provenance():
    game, source, target = setup()
    option = next(
        action
        for action in game.legal_activated_ability_actions(0)
        if action.object_id == source.object_id and action.target_id == target.object_id
    )
    ability = game.announce_activated_ability(
        0, source, option.oracle_fragment, target_ids=(option.target_id,)
    )
    assert ability is not None and source.zone == "former"
    assert all(land.tapped for land in game.players[0].battlefield if land.card.is_land)
    assert ability.sacrificed_destination_id in {
        card.object_id for card in game.players[0].graveyard
    }
    departure = game._rules_events[ability.departure_event_id]
    assert departure.kind is RulesEventKind.PERMANENT_LEFT
    assert departure.subject_ids == (source.object_id,)
    resolve(game)
    assert target.zone == "former"
    assert any(card.card is TARGET for card in game.players[1].graveyard)
    damage = [event for event in game.events if event["event"] == "activated_damage_resolved"]
    assert len(damage) == 1 and damage[0]["amount"] == 3
    assert game.activation_evidence[-1].resolved
    game.check_invariants()


def test_illegal_payments_and_targets_are_nonmutating():
    game, source, target = setup(mana=4)
    before = game.authoritative_state_fingerprint()
    assert (
        game.announce_activated_ability(
            0, source, REACTOR.oracle_text, target_ids=(target.object_id,)
        )
        is None
    )
    assert game.authoritative_state_fingerprint() == before

    game, source, target = setup()
    protected = game.create_permanent(PROTECTED, 1)
    before = game.authoritative_state_fingerprint()
    assert (
        game.announce_activated_ability(
            0, source, REACTOR.oracle_text, target_ids=(protected.object_id,)
        )
        is None
    )
    assert game.announce_activated_ability(0, source, REACTOR.oracle_text, target_ids=()) is None
    assert game.authoritative_state_fingerprint() == before


def test_source_departure_does_not_cancel_ability_but_target_departure_does():
    game, source, target = setup()
    ability = game.announce_activated_ability(
        0, source, REACTOR.oracle_text, target_ids=(target.object_id,)
    )
    assert ability is not None and source.zone == "former"
    game.move_object(target, "hand", reason="response")
    resolve(game)
    assert not [event for event in game.events if event["event"] == "damage_dealt"]
    assert any(
        event["event"] == "activated_ability_resolved_no_effect"
        and event["reason"] == "target_illegal_at_resolution"
        for event in game.events
    )
    game.check_invariants()


def test_priority_window_offers_generic_instant_speed_activation():
    game, source, target = setup()
    game._begin_priority_window(allow_empty=True)
    assert any(
        option.object_id == source.object_id and option.target_id == target.object_id
        for option in game.legal_priority_actions(0)
    )


@pytest.mark.parametrize("seed", [71, 72])
def test_deterministic_replay(seed):
    def run():
        game, source, target = setup(seed)
        assert game.activate_ability(0, source, REACTOR.oracle_text, target_ids=(target.object_id,))
        resolve(game)
        return game.authoritative_state_fingerprint(), game.events

    assert run() == run()
