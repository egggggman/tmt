"""Complete temporary keyword and granted self-death trigger from an instant."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
    TriggerEffect,
    TurnStep,
    load_facts,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
PAIN = load_facts(load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")), {"Pain 101"})[
    "Pain 101"
]
SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
BEAR = CardFact("Quiet Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
BRUTE = CardFact("Quiet Brute", "{2}{G}", 3, "Creature — Beast", power=3, toughness=3)


def game(seed=1):
    current = Game(([SWAMP] * 40, [SWAMP] * 40), seed=seed)
    current.begin_turn()
    for _ in range(2):
        current.create_permanent(SWAMP, 0)
    card = current.set_hand_for_testing(0, [PAIN])[0]
    return current, card


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


def grant(current, card, target):
    action = next(
        option
        for option in current.legal_main_actions(0)
        if option.object_id == card.object_id and option.target_id == target.object_id
    )
    current.execute_main_action(action)
    drain(current)
    assert current._has_keyword(target, "Deathtouch")
    assert len(target.temporary_death_return_effects) == 1


def test_complete_parser_and_fail_closed_companions():
    interpreter = CardInterpreter()
    for card in (PAIN, replace(PAIN, name="Unnamed Rescue")):
        program = interpreter.temporary_death_return_grant_program(card)
        assert program is not None and program.keyword == "deathtouch"
        assert interpreter.cast_program(card).kind is CastKind.TEMPORARY_DEATH_RETURN_GRANT
        assert interpreter.unsupported_fragments(card) == ()
    for text in (
        PAIN.oracle_text + "\nDraw a card.",
        PAIN.oracle_text.replace("tapped", "untapped"),
        PAIN.oracle_text.replace("owner's", "controller's"),
        PAIN.oracle_text.replace("deathtouch", "lifelink"),
    ):
        assert (
            interpreter.temporary_death_return_grant_program(replace(PAIN, oracle_text=text))
            is None
        )


def test_payment_target_and_return_under_owner_with_new_incarnation():
    current, card = game()
    enemy = current.create_permanent(BEAR, 1)
    protected = current.create_permanent(
        replace(BEAR, name="Protected Bear", keywords=("Hexproof",)), 1
    )
    actions = [a for a in current.legal_main_actions(0) if a.object_id == card.object_id]
    assert {a.target_id for a in actions} == {enemy.object_id}
    assert current.announce_spell(0, card, protected) is None
    assert current.announce_spell(0, card, None) is None
    grant(current, card, enemy)
    paid = next(e for e in current.events if e["event"] == "cost_paid")
    assert paid["generic"] == 1 and paid["colored"] == ["B"]
    # Change controller after the grant: the trigger belongs to the dying creature's
    # controller, while its returned incarnation belongs to the card's owner.
    current.players[1].battlefield.remove(enemy)
    enemy.controller = 0
    current.players[0].battlefield.append(enemy)
    current.put_into_graveyard(enemy)
    current._put_pending_triggers_on_stack()
    trigger = current.stack[-1]
    assert trigger.effect is TriggerEffect.GRANTED_DIES_RETURN
    assert trigger.controller == 0
    current._resolve_triggered_ability(trigger)
    returned = next(p for p in current.players[1].battlefield if p.card is BEAR)
    assert returned.object_id != enemy.object_id and returned.tapped
    assert not current._has_keyword(returned, "Deathtouch")
    assert any(e["event"] == "granted_death_return_resolved" for e in current.events)
    current.check_invariants()


def test_graveyard_object_moved_before_resolution_cannot_return():
    current, card = game(seed=17)
    target = current.create_permanent(BEAR, 0)
    grant(current, card, target)
    current.put_into_graveyard(target)
    current._put_pending_triggers_on_stack()
    trigger = current.stack[-1]
    grave = next(obj for obj in current.players[0].graveyard if obj.card is BEAR)
    current.move_object(grave, "exile", reason="response_exile")
    current._resolve_triggered_ability(trigger)
    assert not any(p.card is BEAR for p in current.players[0].battlefield)
    assert any(e["event"] == "granted_death_return_no_effect" for e in current.events)


def test_sacrifice_death_and_cleanup_expiry_are_distinct():
    current, card = game(seed=29)
    target = current.create_permanent(BEAR, 0)
    grant(current, card, target)
    current.move_object(target, "graveyard", reason="sacrifice_cost")
    assert [t.effect for t in current.pending_triggers] == [TriggerEffect.GRANTED_DIES_RETURN]
    current._put_pending_triggers_on_stack()
    current._resolve_triggered_ability(current.stack[-1])
    returned = next(p for p in current.players[0].battlefield if p.card is BEAR)
    assert returned.tapped
    assert returned.temporary_death_return_effects == []
    current._perform_cleanup()
    assert not current._has_keyword(returned, "Deathtouch")


def test_grant_expires_and_ability_loss_suppresses_its_death_trigger():
    current, card = game(seed=31)
    creature = current.create_permanent(BEAR, 0)
    grant(current, card, creature)
    creature.ability_loss_timestamp = current._effect_timestamp()
    assert not current._has_keyword(creature, "Deathtouch")
    current.put_into_graveyard(creature)
    assert not any(t.effect is TriggerEffect.GRANTED_DIES_RETURN for t in current.pending_triggers)

    next_game, next_card = game(seed=32)
    next_creature = next_game.create_permanent(BEAR, 0)
    grant(next_game, next_card, next_creature)
    next_game._perform_cleanup()
    assert not next_creature.temporary_death_return_effects
    next_game.put_into_graveyard(next_creature)
    assert not any(
        t.effect is TriggerEffect.GRANTED_DIES_RETURN for t in next_game.pending_triggers
    )


def test_target_departure_before_spell_resolution_fizzles_entire_grant():
    current, card = game(seed=33)
    creature = current.create_permanent(BEAR, 1)
    action = next(
        a
        for a in current.legal_main_actions(0)
        if a.object_id == card.object_id and a.target_id == creature.object_id
    )
    current.execute_main_action(action)
    current.put_into_graveyard(creature)
    drain(current)
    assert not creature.temporary_keyword_effects
    assert not creature.temporary_death_return_effects
    assert any(e["event"] == "spell_resolved_no_effect" for e in current.events)


def test_deterministic_replay_and_blocking_damage():
    snapshots = []
    for _ in range(2):
        current, card = game(seed=41)
        attacker = current.create_permanent(BRUTE, 0, summoning_sick=False)
        blocker = current.create_permanent(BEAR, 1, summoning_sick=False)
        grant(current, card, blocker)
        current.advance_to(TurnStep.DECLARE_ATTACKERS)
        # The granted deathtouch is used in actual combat, then death recursion.
        attack = next(
            action
            for action in current.legal_attack_options(0)
            if action.attacker_ids == (attacker.object_id,)
        )
        current.execute_attack_action(attack)
        current.execute_block_action(
            ActionOption(
                ActionKind.DECLARE_BLOCKERS,
                1,
                blocks=((attacker.object_id, blocker.object_id),),
            )
        )
        current.resolve_combat_damage()
        drain(current)
        assert attacker.zone == "former"  # two damage is lethal only with deathtouch
        assert any(p.card is BEAR and p.tapped for p in current.players[1].battlefield)
        snapshots.append(current.snapshot())
    assert snapshots[0] == snapshots[1]
