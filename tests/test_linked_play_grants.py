"""A linked, single-use play grant follows normal card timing and payment."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
    LinkedPlayGrant,
    TurnStep,
    load_facts,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
FACTS = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")),
    {"Mouser Attack!", "Raphael's Technique"},
)
MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land — Mountain")
BEAR = CardFact("Ordinary Bear", "{1}{R}", 2, "Creature — Bear", power=2, toughness=2)
FREE = replace(BEAR, name="Free Visitor", mana_cost="", mana_value=0)


def game(seed=319, *, lands=3):
    current = Game(([MOUNTAIN] * 25, [MOUNTAIN] * 25), seed=seed)
    current.begin_turn()
    for _ in range(lands):
        current.create_permanent(MOUNTAIN, 0)
    return current


def link(current, source, card, owner=0):
    exiled = current._create_card_object(card, owner, "exile")
    current.players[owner].exile.append(exiled)
    current._raphael_linked_exile.setdefault(source.object_id, []).append(
        (exiled.object_id, exiled.card, source.object_id)
    )
    return exiled


def grant(current, source, controller=0, grant_id="fixture-grant"):
    item = LinkedPlayGrant(grant_id, source.object_id, controller, current.turn)
    current._linked_play_grants.setdefault(source.object_id, []).append(item)
    return item


def drain(current):
    while current.priority_state is not None:
        state = current.priority_state
        if state.resolution_pending:
            current.process_priority_resolution()
        else:
            current.execute_priority_action(
                next(
                    action
                    for action in current.legal_priority_actions(state.player_index)
                    if action.kind is ActionKind.PASS_PRIORITY
                )
            )


def test_permission_selects_on_play_including_cards_exiled_after_grant():
    current = game(lands=0)
    source = current.create_permanent(BEAR, 0)
    prior = link(current, source, FREE)
    unrelated = current._create_card_object(FREE, 0, "exile")
    current.players[0].exile.append(unrelated)
    permission = grant(current, source)
    later = link(current, source, FREE)
    assert current._raphael_permission_for(0, later) == source.object_id
    assert current._raphael_permission_for(0, unrelated) is None
    assert {option.object_id for option in current.legal_main_actions(0)}.issuperset(
        {prior.object_id, later.object_id}
    )
    current.execute_main_action(
        next(o for o in current.legal_main_actions(0) if o.object_id == later.object_id)
    )
    assert permission.remaining_plays == 0
    assert current._raphael_permission_for(0, prior) is None
    assert not any(o.object_id == prior.object_id for o in current.legal_main_actions(0))
    drain(current)
    current.check_invariants()


@pytest.mark.parametrize("pump", (False, True))
def test_linked_modal_instant_announces_exact_mode_with_priority_and_replay(pump):
    def run():
        current = game(seed=321)
        source = current.create_permanent(BEAR, 0)
        target = current.create_permanent(BEAR, 0)
        card = link(current, source, FACTS["Mouser Attack!"])
        permission = grant(current, source)
        current.destroy(source)
        current.advance_to(TurnStep.DECLARE_ATTACKERS)
        current._begin_priority_window(allow_empty=True, priority_player=0)
        options = [o for o in current.legal_priority_actions(0) if o.object_id == card.object_id]
        assert len(options) >= 2
        chosen = next(o for o in options if (o.target_id == target.object_id) == pump)
        assert chosen.oracle_fragment is not None
        current.execute_priority_action(chosen)
        assert current.stack[-1].mode_fragment == chosen.oracle_fragment
        assert permission.remaining_plays == 0
        drain(current)
        assert any(
            e["event"] == "modal_mode_chosen" and e["mode_fragment"] == chosen.oracle_fragment
            for e in current.events
        )
        assert any(e["event"] == "linked_play_grant_used" for e in current.events)
        current.check_invariants()
        return current.snapshot()

    assert run() == run()


def test_controlled_permission_can_play_card_owned_by_another_player():
    current = game(lands=0)
    source = current.create_permanent(BEAR, 0)
    exiled = link(current, source, FREE, owner=1)
    grant(current, source, controller=0)
    action = next(o for o in current.legal_main_actions(0) if o.object_id == exiled.object_id)
    current.execute_main_action(action)
    drain(current)
    entered = next(p for p in current.players[0].battlefield if p.card.name == FREE.name)
    assert entered.owner == 1 and entered.controller == 0
    current.check_invariants()


def test_linked_sneak_uses_alt_cost_and_consumes_exact_grant():
    def run():
        current = game(seed=322)
        source = current.create_permanent(BEAR, 0)
        card = link(current, source, FACTS["Raphael's Technique"])
        permission = grant(current, source)
        attacker = current.create_permanent(BEAR, 0, summoning_sick=False)
        current.advance_to(TurnStep.DECLARE_ATTACKERS)
        current.execute_attack_action(
            ActionOption(ActionKind.DECLARE_ATTACKERS, 0, attacker_ids=(attacker.object_id,))
        )
        current.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))
        action = next(o for o in current.legal_sneak_actions(0) if o.object_id == card.object_id)
        current.execute_sneak_action(action)
        assert current.stack[-1].cast_from_raphael and permission.remaining_plays == 0
        assert any(
            e["event"] == "zone_changed"
            and e.get("source_object_id") == card.object_id
            and e["source_zone"] == "exile"
            for e in current.events
        )
        drain(current)
        current.check_invariants()
        return current.snapshot()

    assert run() == run()


def test_invalid_or_expired_linked_grant_cannot_pay_or_move_card():
    current = game(lands=0)
    source = current.create_permanent(BEAR, 0)
    exiled = link(current, source, FREE)
    permission = grant(current, source)
    current._turn += 1
    assert current.payment_plan(0, exiled, allow_exile=True) is None
    assert current.announce_spell(0, exiled, cast_from_exile=True) is None
    assert permission.remaining_plays == 1 and exiled.zone == "exile"
    current.check_invariants()
