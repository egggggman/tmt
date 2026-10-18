"""Oracle-derived self-damage mana triggers and per-unit turn-end retention."""

from dataclasses import replace
from pathlib import Path
from types import MethodType

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, DamageTargetKind
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    DamageTransaction,
    Game,
    TriggerEffect,
    TurnStep,
    load_facts,
)
from tmnt_design_studio.mana_ledger07 import FloatingManaLedger

FRAGMENT = (
    "Enrage — Whenever this creature is dealt damage, add that much {R}. "
    "Until end of turn, you don't lose this mana as steps and phases end."
)
REACTOR = CardFact("Anonymous Reactor", "{2}{R}", 3, "Creature — Beast", FRAGMENT, 4, 5)
SOURCE = CardFact("Damage Source", "{R}", 1, "Creature — Goblin", "", 2, 2)
LAND = CardFact("Mountain", "", 0, "Basic Land — Mountain")
SPELL = CardFact("Red Spell", "{R}", 1, "Creature — Goblin", "", 1, 1)
ABILITY = "{R}, Sacrifice this artifact: Draw one card."
TOOL = CardFact("Reusable Tool", "{1}", 1, "Artifact", ABILITY)


def setup(*, hand=()):
    game = Game(([LAND] * 60, [LAND] * 60), seed=2893)
    game.begin_turn()
    game.set_hand_for_testing(0, list(hand))
    reactor = game.create_permanent(REACTOR, 0)
    source = game.create_permanent(SOURCE, 1, summoning_sick=False)
    return game, reactor, source


def resolve(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            options = game.legal_priority_actions(game.priority_state.player_index)
            game.execute_priority_action(
                next(option for option in options if option.kind is ActionKind.PASS_PRIORITY)
            )


def damage(game, reactor, source, amount):
    return game.deal_damage(
        DamageTransaction(
            1, source, DamageTargetKind.CREATURE, amount, "Deal damage.", target=reactor
        )
    )


def test_parser_requires_full_retention_and_self_reference_from_frozen_oracle():
    interpreter = CardInterpreter()
    assert interpreter.damage_to_self_mana(REACTOR, FRAGMENT) == "R"
    assert (FRAGMENT, "oracle_ability_not_implemented") not in interpreter.unsupported_fragments(
        REACTOR
    )
    catalog = Path(__file__).resolve().parents[1] / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    frozen = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Raphael, Ninja Destroyer"},
    )["Raphael, Ninja Destroyer"]
    clause = CardInterpreter.fragments(frozen)[1]
    assert interpreter.damage_to_self_mana(frozen, clause) == "R"
    for text in (
        FRAGMENT.replace("this creature", "another creature"),
        FRAGMENT.replace("Until end of turn, ", ""),
        FRAGMENT + " Draw a card.",
    ):
        assert interpreter.damage_to_self_mana(replace(REACTOR, oracle_text=text), text) is None


def test_noncombat_damage_amount_priority_source_departure_and_turn_retention():
    game, reactor, source = setup(hand=(SPELL, SPELL))
    event = damage(game, reactor, source, 2)
    assert game.stack[-1].effect is TriggerEffect.DAMAGE_TO_SELF_MANA
    assert game.stack[-1].event is event
    assert game.floating_mana.snapshot(0) == {}
    game.move_object(reactor, "graveyard", reason="response")
    resolve(game)
    production = game.floating_mana.productions(0)[-1]
    assert (production.source_id, production.color, production.quantity) == (
        reactor.object_id,
        "R",
        2,
    )
    assert production.allowed_spending == () and production.persists_until_turn_end
    assert game.floating_mana.snapshot(0) == {"R": 2}
    game.floating_mana.add(0, source.object_id, "R", 1, "ordinary")
    game.advance_to(TurnStep.COMBAT_DAMAGE)
    game.resolve_combat_damage()
    game.advance_to(TurnStep.POSTCOMBAT_MAIN)
    assert game.floating_mana.snapshot(0) == {"R": 2}
    assert game.floating_mana.consumptions(0)[-1].payment_id == "mana_pool_emptied"
    spell = game.players[0].hand[0]
    plan = game.payment_plan(0, spell)
    assert plan is not None and plan.floating_event_ids == (production.event_id,)
    assert game.announce_spell(0, spell) is not None
    assert game.floating_mana.snapshot(0) == {"R": 1}
    game.resolve_top_of_stack()
    game.advance_to(TurnStep.CLEANUP)
    assert game.floating_mana.snapshot(0) == {"R": 1}
    game.advance_step()
    assert game.floating_mana.snapshot(0) == {}
    assert (
        sum(
            c.quantity
            for c in game.floating_mana.consumptions(0)
            if c.source_event_id == production.event_id
        )
        == 2
    )
    game.check_invariants()


def test_legal_activation_payment_and_invalid_cast_do_not_consume_retained_units():
    game, reactor, source = setup()
    damage(game, reactor, source, 1)
    resolve(game)
    unit = game.floating_mana.productions(0)[-1]
    expensive = CardFact("Too Expensive", "{R}{R}", 2, "Creature — Goblin", "", 2, 2)
    game.set_hand_for_testing(0, [expensive])
    card = game.players[0].hand[0]
    assert game.announce_spell(0, card) is None
    assert game.floating_mana.snapshot(0) == {"R": 1}
    tool = game.create_permanent(TOOL, 0)
    ability = game.announce_activated_ability(0, tool, ABILITY)
    assert ability is not None
    assert game.floating_mana.snapshot(0) == {}
    assert game.floating_mana.consumptions(0)[-1].source_event_id == unit.event_id
    resolve(game)
    game.check_invariants()


def test_ordinary_and_restricted_mana_still_expire_independently():
    ledger = FloatingManaLedger()
    ledger.add(0, "ordinary", "R", 2, "ordinary")
    ledger.add(0, "restricted", "R", 1, "restricted", ("artifact_spell", "activate_ability"))
    ledger.add(0, "retained", "R", 3, "retained", persists_until_turn_end=True)
    assert ledger.empty(0, preserve_turn_end=True) == {"R": 3}
    assert ledger.snapshot(0) == {"R": 3}
    assert ledger.eligible(0, "other_spell") == (ledger.productions(0)[2],) * 3
    assert ledger.empty(0) == {"R": 3}
    assert ledger.snapshot(0) == {}


def test_no_trigger_from_damage_to_player_or_suppressed_recipient():
    game, reactor, source = setup()
    game.deal_damage(
        DamageTransaction(1, source, DamageTargetKind.PLAYER, 1, "Deal damage.", target_player=0)
    )
    assert not game.stack
    reactor.ability_loss_timestamp = (game.turn, 1)
    damage(game, reactor, source, 1)
    assert not game.stack and not game.floating_mana.snapshot(0)
    game.check_invariants()


def test_combat_damage_to_recipient_uses_recipient_controller():
    game = Game(([LAND] * 60, [LAND] * 60), seed=2894)
    game.begin_turn()
    attacker = game.create_permanent(SOURCE, 0, summoning_sick=False)
    reactor = game.create_permanent(REACTOR, 1, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    game.execute_attack_action(
        next(
            option
            for option in game.legal_attack_options(0)
            if option.attacker_ids == (attacker.object_id,)
        )
    )
    game.execute_block_action(
        ActionOption(
            ActionKind.DECLARE_BLOCKERS, 1, blocks=((attacker.object_id, reactor.object_id),)
        )
    )
    game.resolve_combat_damage()
    assert game.stack[-1].effect is TriggerEffect.DAMAGE_TO_SELF_MANA
    assert game.stack[-1].controller == 1
    resolve(game)
    assert game.floating_mana.snapshot(1) == {"R": 2}
    assert game.floating_mana.snapshot(0) == {}
    game.check_invariants()


def test_first_and_regular_damage_steps_retain_only_permitted_units():
    game = Game(([LAND] * 60, [LAND] * 60), seed=2895)
    game.begin_turn()
    double = CardFact("Double Attacker", "{2}", 2, "Creature — Warrior", "Double strike", 1, 1)
    attacker = game.create_permanent(double, 0, summoning_sick=False)
    reactor = game.create_permanent(REACTOR, 1, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    game.execute_attack_action(
        next(
            option
            for option in game.legal_attack_options(0)
            if option.attacker_ids == (attacker.object_id,)
        )
    )
    game.execute_block_action(
        ActionOption(
            ActionKind.DECLARE_BLOCKERS, 1, blocks=((attacker.object_id, reactor.object_id),)
        )
    )
    first = game.resolve_combat_damage()
    assert first.sequence == 1 and game.priority_state is not None
    game.floating_mana.add(1, reactor.object_id, "R", 1, "ordinary_first_strike")
    resolve(game)
    assert game.floating_mana.snapshot(1) == {"R": 1}
    regular = game.resolve_combat_damage()
    assert regular.sequence == 2
    assert any(e["event"] == "floating_mana_emptied" and e["mana"] == {"R": 1} for e in game.events)
    resolve(game)
    assert game.floating_mana.snapshot(1) == {"R": 2}
    assert [e["quantity"] for e in game.events if e["event"] == "damage_to_self_mana_resolved"] == [
        1,
        1,
    ]
    game.check_invariants()


def test_lethal_damage_source_departure_forged_event_and_exact_replay():
    def scenario():
        game = Game(([LAND] * 60, [LAND] * 60), seed=2896)
        game.begin_turn()
        reactor = game.create_permanent(replace(REACTOR, toughness=1), 0)
        source = game.create_permanent(SOURCE, 1)
        event = damage(game, reactor, source, 2)
        trigger = game.stack[-1]
        with pytest.raises(ValueError, match="original evidence"):
            game._validate_damage_to_self_mana(
                replace(event, amount=9),
                reactor.object_id,
                reactor.card,
                trigger.oracle_fragment,
                0,
                trigger_id=trigger.trigger_id,
            )
        game.check_state_based_actions()
        assert reactor.zone == "former"
        resolve(game)
        assert game.floating_mana.snapshot(0) == {"R": 2}
        game.check_invariants()
        return game.events, game.floating_mana.productions(0), game.floating_mana.consumptions(0)

    assert scenario() == scenario()


def test_departed_combat_recipient_cannot_create_damage_mana_event():
    """A stale combat assignment must fail closed before event construction."""
    game = Game(([LAND] * 60, [LAND] * 60), seed=2897)
    game.begin_turn()
    attacker = game.create_permanent(SOURCE, 0, summoning_sick=False)
    reactor = game.create_permanent(REACTOR, 1, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    game.execute_attack_action(
        next(
            option
            for option in game.legal_attack_options(0)
            if option.attacker_ids == (attacker.object_id,)
        )
    )
    game.execute_block_action(
        ActionOption(
            ActionKind.DECLARE_BLOCKERS,
            1,
            blocks=((attacker.object_id, reactor.object_id),),
        )
    )
    original = game._combat_permanent
    departed = False

    def depart_before_assignment(self, object_id, role):
        nonlocal departed
        if role == "damage source" and not departed:
            departed = True
            self.move_object(reactor, "graveyard", reason="stale_combat_fixture")
        return original(object_id, role)

    game._combat_permanent = MethodType(depart_before_assignment, game)
    game.resolve_combat_damage()
    assert reactor.zone == "former"
    assert not game.stack
    assert not game.floating_mana.snapshot(1)
    game.check_invariants()
