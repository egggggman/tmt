"""Granted combat abilities and optional subtype-entry Equipment attachment."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
    TriggerEffect,
    TurnStep,
    load_facts,
)

LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
WARRIOR = CardFact("Guard", "{1}", 1, "Creature — Warrior", power=2, toughness=2)
DOUBLE = replace(
    WARRIOR, name="Double Guard", oracle_text="Double strike", keywords=("Double strike",)
)
GEAR = CardFact(
    "Generic Blade",
    "{W}",
    1,
    "Artifact — Equipment",
    'Equipped creature gets +1/+1 and has "Whenever this creature deals combat '
    'damage, untap it and you gain 2 life."\n'
    "Whenever a Warrior you control enters, you may attach this Equipment to it.\n"
    "Equip {2}",
)
BONUS = GEAR.oracle_text.splitlines()[0]
ENTRY = GEAR.oracle_text.splitlines()[1]


def setup(*, chooser=None, equipped=True, creature=WARRIOR):
    game = Game(([LAND] * 35, [LAND] * 35), seed=307, equipment_attach_chooser=chooser)
    game.begin_turn()
    recipient = game.create_permanent(creature, 0, summoning_sick=False)
    equipment = game.create_permanent(GEAR, 0)
    if equipped:
        equipment.attached_to = recipient.object_id
        equipment.attachment_timestamp = game._effect_timestamp()
        game.refresh_static_pt_modifiers()
    return game, equipment, recipient


def resolve(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def combat(game, attacker, blockers=()):
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    game.execute_attack_action(
        next(
            action
            for action in game.legal_attack_options(0)
            if action.attacker_ids == (attacker.object_id,)
        )
    )
    game.execute_block_action(
        ActionOption(
            ActionKind.DECLARE_BLOCKERS,
            1,
            blocks=tuple((attacker.object_id, blocker.object_id) for blocker in blockers),
        )
    )


def test_frozen_oracle_and_renamed_equipment_derive_both_families():
    root = Path(__file__).resolve().parents[1]
    path = root / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    frozen = load_facts(
        load_card_data(path, path.with_suffix(".manifest.json")),
        {"Quintessential Katana"},
    )["Quintessential Katana"]
    interpreter = CardInterpreter()
    assert interpreter.equipment_granted_combat_semantics(
        frozen, frozen.oracle_text.splitlines()[0]
    ) == (1, 1, 2)
    assert (
        interpreter.equipment_subtype_entry_attach(frozen, frozen.oracle_text.splitlines()[1])
        == "Ninja"
    )
    assert interpreter.equipment_static_semantics(GEAR, BONUS) == (1, 1, None)
    assert interpreter.equipment_subtype_entry_attach(GEAR, ENTRY) == "Warrior"
    assert not interpreter.unsupported_fragments(frozen)
    assert (
        interpreter.equipment_granted_combat_semantics(replace(GEAR, type_line="Artifact"), BONUS)
        is None
    )


def test_optional_entry_attaches_at_resolution_and_can_decline():
    for choice in (True, False):
        game, equipment, old = setup(chooser=lambda *_, selected=choice: selected)
        entrant = game.create_permanent(WARRIOR, 0)
        game._process_creature_entered_triggers(entrant)
        assert game.stack[-1].effect is TriggerEffect.EQUIPMENT_SUBTYPE_ENTRY_ATTACH
        assert equipment.attached_to == old.object_id
        resolve(game)
        assert equipment.attached_to == (entrant.object_id if choice else old.object_id)
        assert entrant.power == (3 if choice else 2)
        game.check_invariants()


def test_entry_is_untargeted_but_requires_live_equipment_and_same_recipient():
    game, equipment, old = setup()
    entrant = game.create_permanent(WARRIOR, 0)
    game._process_creature_entered_triggers(entrant)
    game.move_object(entrant, "graveyard", reason="test_response")
    resolve(game)
    assert equipment.attached_to == old.object_id
    other = game.create_permanent(WARRIOR, 0)
    game._process_creature_entered_triggers(other)
    game.move_object(equipment, "graveyard", reason="test_response")
    resolve(game)
    assert other.power == 2 and old.power == 2
    game.check_invariants()


def test_combat_hit_waits_for_priority_untaps_recipient_and_gains_life():
    game, equipment, attacker = setup()
    assert attacker.power == 3 and attacker.toughness == 3
    combat(game, attacker)
    game.resolve_combat_damage()
    assert attacker.tapped and game.players[0].life == 20
    assert game.players[1].life == 17
    ability = game.stack[-1]
    assert ability.effect is TriggerEffect.GRANTED_COMBAT_UNTAP_GAIN
    assert ability.source_id == attacker.object_id
    assert game._triggers[ability.trigger_id].grant_source_id == equipment.object_id
    resolve(game)
    assert not attacker.tapped and game.players[0].life == 22
    assert len([e for e in game.events if e["event"] == "equipment_granted_combat_resolved"]) == 1
    game.check_invariants()


def test_blocking_creature_damage_triggers_and_double_strike_gives_two_player_triggers():
    game, _equipment, attacker = setup()
    blocker = game.create_permanent(WARRIOR, 1)
    combat(game, attacker, (blocker,))
    game.resolve_combat_damage()
    assert game.players[1].life == 20 and game.players[0].life == 20
    assert len(game.stack) == 1
    resolve(game)
    assert game.players[0].life == 22
    assert (
        next(e for e in game.events if e["event"] == "equipment_granted_combat_resolved")[
            "damage_recipient_id"
        ]
        == blocker.object_id
    )
    game.check_invariants()

    game, _equipment, attacker = setup(creature=DOUBLE)
    combat(game, attacker)
    game.resolve_combat_damage()
    resolve(game)
    assert game.players[0].life == 22 and game.step is TurnStep.COMBAT_DAMAGE
    game.resolve_combat_damage()
    resolve(game)
    assert game.players[0].life == 24 and game.players[1].life == 14
    assert len([e for e in game.events if e["event"] == "equipment_granted_combat_resolved"]) == 2
    game.check_invariants()


def test_trigger_persists_after_attachment_or_recipient_departure_and_replays():
    def run():
        game, equipment, attacker = setup()
        combat(game, attacker)
        game.resolve_combat_damage()
        game.move_object(equipment, "graveyard", reason="test_response")
        game.move_object(attacker, "graveyard", reason="test_response")
        resolve(game)
        assert game.players[0].life == 22
        assert (
            next(e for e in game.events if e["event"] == "equipment_granted_combat_resolved")[
                "untapped"
            ]
            is False
        )
        game.check_invariants()
        return game.snapshot(), game.events

    assert run() == run()
