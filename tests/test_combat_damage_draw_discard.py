"""Combat damage triggers use the ordinary damage, stack, and zone model."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
    RulesEventKind,
    TriggerEffect,
    TurnStep,
    load_facts,
)

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
FRAGMENT = (
    "Whenever Courier deals combat damage to a player, draw that many cards, then discard a card."
)
COURIER = CardFact("Courier, Archive Diver", "{2}{U}", 3, "Creature", FRAGMENT, 2, 4)
NORMAL = CardFact("Normal", "{1}{W}", 2, "Creature", power=2, toughness=2)


def game(source=COURIER, *, second=None, chooser=None, library_size=30):
    g = Game(
        ([LAND] * library_size, [LAND] * 30),
        seed=289,
        draw_discard_chooser=chooser,
    )
    g.begin_turn()
    g.set_hand_for_testing(0, [LAND, LAND])
    attacker = g.create_permanent(source, 0, summoning_sick=False)
    additional = g.create_permanent(second, 0, summoning_sick=False) if second else None
    return g, attacker, additional


def combat(g, attackers, blockers=()):
    g.advance_to(TurnStep.DECLARE_ATTACKERS)
    chosen = tuple(attacker.object_id for attacker in attackers)
    g.execute_attack_action(
        next(option for option in g.legal_attack_options(0) if option.attacker_ids == chosen)
    )
    g.execute_block_action(
        ActionOption(
            ActionKind.DECLARE_BLOCKERS,
            1,
            blocks=tuple((attacker.object_id, blocker.object_id) for attacker, blocker in blockers),
        )
    )


def resolve(g):
    while g.priority_state is not None:
        if g.priority_state.resolution_pending:
            g.process_priority_resolution()
        else:
            g.execute_priority_action(g.legal_priority_actions(g.priority_state.player_index)[0])


def commits(g):
    return [e for e in g.events if e["event"] == "combat_draw_discard_committed"]


def test_oracle_frozen_and_generic_self_reference():
    catalog = load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    april = load_facts(catalog, {"April, Reporter of the Weird"})["April, Reporter of the Weird"]
    exact = (
        "Whenever April deals combat damage to a player, draw that many cards, then discard a card."
    )
    assert april.oracle_id == "1c371003-e4f0-4d7c-b021-273176772f97"
    assert exact in CardInterpreter.fragments(april)
    assert CardInterpreter().combat_damage_draw_discard_semantic_coverage(april, exact)
    renamed = replace(
        COURIER, name="Messenger", oracle_text=FRAGMENT.replace("Courier", "Messenger")
    )
    assert CardInterpreter().combat_damage_draw_discard_semantic_coverage(
        renamed, renamed.oracle_text
    )
    assert CardInterpreter().combat_damage_draw_discard_semantic_coverage(renamed, FRAGMENT) is None
    assert not any(
        fragment == exact for fragment, _ in CardInterpreter().unsupported_fragments(april)
    )

    g, source, _ = game(april)
    combat(g, (source,))
    g.resolve_combat_damage()
    resolve(g)
    assert len(commits(g)) == 1
    assert commits(g)[0]["damage"] == april.power
    assert commits(g)[0]["drawn_count"] == april.power


@pytest.mark.parametrize(
    "fragment",
    [
        FRAGMENT.replace("combat damage", "damage"),
        FRAGMENT.replace("to a player", "to a creature"),
        FRAGMENT.replace("draw that many cards", "draw a card"),
        FRAGMENT.replace("then discard", "and discard"),
        FRAGMENT + " Gain 2 life.",
    ],
)
def test_unrepresented_neighbors_are_not_claimed(fragment):
    assert CardInterpreter().combat_damage_draw_discard_semantic_coverage(COURIER, fragment) is None


def test_unblocked_damage_waits_for_priority_and_uses_post_draw_choice():
    observations = []

    def choose(view, options):
        observations.append((view, options))
        return options[-1]

    g, source, _ = game(chooser=choose)
    combat(g, (source,))
    before_hand, before_library = tuple(g.players[0].hand), tuple(g.players[0].library)
    g.resolve_combat_damage()
    assert g.players[1].life == 18
    assert g.step is TurnStep.COMBAT_DAMAGE
    assert len(g.stack) == 1
    assert g.stack[-1].effect is TriggerEffect.COMBAT_DAMAGE_DRAW_DISCARD
    assert (tuple(g.players[0].hand), tuple(g.players[0].library)) == (
        before_hand,
        before_library,
    )
    with pytest.raises(ValueError, match="before all players pass"):
        g.resolve_top_of_stack()
    resolve(g)
    assert g.step is TurnStep.END_OF_COMBAT
    assert len(observations) == 1 and len(observations[0][1]) == 4
    assert len(g.players[0].hand) == len(before_hand) + 1
    evidence = commits(g)[0]
    assert evidence["damage"] == 2 and evidence["drawn_count"] == 2
    assert evidence["selected_hand_id"] != evidence["discarded_graveyard_id"]
    assert evidence["selected_hand_id"] in evidence["offered_choice_ids"]
    assert evidence["discarded_graveyard_id"] in evidence["post_graveyard_ids"]
    event = g._rules_events[evidence["event_id"]]
    assert event.kind is RulesEventKind.COMBAT_DAMAGE_TO_PLAYER
    assert event.source_id == source.object_id and event.amount == 2
    g.check_invariants()


def test_blocked_attack_creates_no_player_damage_trigger():
    g, source, _ = game()
    blocker = g.create_permanent(NORMAL, 1)
    combat(g, (source,), ((source, blocker),))
    g.resolve_combat_damage()
    assert not commits(g) and not g.stack
    assert g.players[1].life == 20


@pytest.mark.parametrize("keyword,damage_steps", [("First strike", 1), ("Double strike", 2)])
def test_strike_steps_trigger_only_on_damage_to_player(keyword, damage_steps):
    source = replace(COURIER, oracle_text=keyword + "\n" + FRAGMENT, keywords=(keyword,))
    g, attacker, _ = game(source)
    combat(g, (attacker,))
    g.resolve_combat_damage()
    assert g.step is TurnStep.COMBAT_DAMAGE
    assert len(g.stack) == 1
    resolve(g)
    assert g.step is TurnStep.COMBAT_DAMAGE
    g.resolve_combat_damage()
    resolve(g)
    assert g.step is TurnStep.END_OF_COMBAT
    assert len(commits(g)) == damage_steps
    assert sum(e["drawn_count"] for e in commits(g)) == 2 * damage_steps
    assert g.players[1].life == 20 - 2 * damage_steps


def test_multiple_sources_have_distinct_events_triggers_and_resolutions():
    g, first, second = game(second=COURIER)
    combat(g, (first, second))
    g.resolve_combat_damage()
    assert len(g.stack) == 2
    resolve(g)
    entries = commits(g)
    assert len(entries) == 2
    assert {e["source_id"] for e in entries} == {first.object_id, second.object_id}
    assert len({e["event_id"] for e in entries}) == 2
    assert len({e["trigger_id"] for e in entries}) == 2
    assert g.players[1].life == 16


def test_trample_damage_triggers_even_when_source_dies_in_same_damage_step():
    trampler = replace(
        COURIER,
        oracle_text="Trample\n" + FRAGMENT,
        keywords=("Trample",),
        power=4,
        toughness=2,
    )
    g, source, _ = game(trampler)
    blocker = g.create_permanent(NORMAL, 1)
    combat(g, (source,), ((source, blocker),))
    g.resolve_combat_damage()
    assert source.zone == "former"
    assert g.players[1].life == 18
    assert len(g.stack) == 1
    resolve(g)
    assert commits(g)[0]["damage"] == 2


def test_source_removal_and_zone_transition_preserve_trigger_then_new_identity():
    g, source, _ = game()
    combat(g, (source,))
    g.resolve_combat_damage()
    ability = g.stack[-1]
    g.put_into_graveyard(source)
    assert source.zone == "former"
    resolve(g)
    assert commits(g)[0]["source_id"] == source.object_id
    assert ability.zone == "former"
    with pytest.raises(ValueError):
        g._resolve_combat_draw_discard(ability)
    returned = g.move_object(g.players[0].graveyard[-1], "battlefield", reason="test_return")
    assert returned.object_id != source.object_id
    g.check_invariants()


def test_empty_library_mandatory_discard_then_loss_at_state_based_actions():
    g, source, _ = game()
    combat(g, (source,))
    g.resolve_combat_damage()
    while g.players[0].library:
        g.move_object(g.players[0].library[-1], "graveyard", reason="test_empty")
    resolve(g)
    evidence = commits(g)[0]
    assert evidence["drawn_count"] == 0
    assert evidence["failed_draw_pending"]
    assert evidence["discarded_graveyard_id"] is not None
    assert g.winner == 1


def test_partial_library_draws_available_card_then_fails_and_discards():
    g, source, _ = game()
    combat(g, (source,))
    g.resolve_combat_damage()
    while len(g.players[0].library) > 1:
        g.move_object(g.players[0].library[-1], "graveyard", reason="test_empty")
    resolve(g)
    evidence = commits(g)[0]
    assert not evidence["draw_succeeded"]
    assert evidence["drawn_count"] == 1
    assert evidence["discarded_graveyard_id"] is not None
    assert g.winner == 1


def test_lethal_combat_ends_game_before_trigger_reaches_stack():
    g, source, _ = game()
    g.players[1].life = 2
    combat(g, (source,))
    g.resolve_combat_damage()
    assert g.winner == 0
    assert g.step is TurnStep.END_OF_COMBAT
    assert not g.stack and g.priority_state is None
    assert not commits(g)


def test_provenance_tamper_fails_before_draw():
    g, source, _ = game()
    combat(g, (source,))
    g.resolve_combat_damage()
    ability = g.stack[-1]
    before = tuple(g.players[0].hand), tuple(g.players[0].library)
    ability.event = replace(ability.event, amount=8)
    with pytest.raises(ValueError):
        resolve(g)
    assert before == (tuple(g.players[0].hand), tuple(g.players[0].library))


def test_deterministic_snapshot_and_replay_of_damage_trigger():
    def execute():
        g, source, _ = game()
        combat(g, (source,))
        g.resolve_combat_damage()
        resolve(g)
        g.check_invariants()
        return g.snapshot()

    assert execute() == execute()
