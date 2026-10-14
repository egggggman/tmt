"""Mandatory self-entry creature destruction through normal target and Stack rules."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TriggerEffect, load_facts

ROOT = Path(__file__).resolve().parents[1]
SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
FRAGMENT = "When this artifact enters, destroy target creature."
SOURCE = CardFact("Unnamed Food", "{2}{B}{B}", 4, "Artifact — Food", FRAGMENT)
CREATURE = CardFact("Target", "{1}", 1, "Creature", power=2, toughness=2)
HEXPROOF = replace(CREATURE, name="Protected", oracle_text="Hexproof", keywords=("Hexproof",))
INDESTRUCTIBLE = replace(
    CREATURE, name="Durable", oracle_text="Indestructible", keywords=("Indestructible",)
)


def setup(*, chooser=None):
    current = Game(([SWAMP] * 35, [SWAMP] * 35), seed=309, counter_target_chooser=chooser)
    current.begin_turn()
    return current


def resolve(current):
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            current.execute_priority_action(
                current.legal_priority_actions(current.priority_state.player_index)[0]
            )


def entry(current, source=SOURCE):
    permanent = current.create_permanent(source, 0)
    current._process_creature_entered_triggers(permanent)
    return permanent


def test_frozen_oracle_and_renamed_artifact_and_creature_grammar():
    path = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    frozen = load_facts(
        load_card_data(path, path.with_suffix(".manifest.json")),
        {"Anchovy & Banana Pizza"},
    )["Anchovy & Banana Pizza"]
    interpreter = CardInterpreter()
    assert interpreter.etb_destroy_target_creature(frozen, frozen.oracle_text.splitlines()[0])
    assert interpreter.etb_destroy_target_creature(SOURCE, FRAGMENT)
    assert not interpreter.unsupported_fragments(frozen)
    creature = replace(
        CREATURE,
        name="Creature Source",
        oracle_text="When this creature enters, destroy target creature.",
    )
    assert interpreter.etb_destroy_target_creature(creature, creature.oracle_text)
    assert not interpreter.etb_destroy_target_creature(CREATURE, FRAGMENT)
    assert not interpreter.etb_destroy_target_creature(
        SOURCE, "When this artifact enters, destroy up to one target creature."
    )


def test_cast_payment_entry_target_priority_and_resolution_from_frozen_card():
    path = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    frozen = load_facts(
        load_card_data(path, path.with_suffix(".manifest.json")),
        {"Anchovy & Banana Pizza"},
    )["Anchovy & Banana Pizza"]
    offered = []

    def choose(_controller, _source_id, options):
        offered.append(options)
        return options[-1]

    current = setup(chooser=choose)
    own = current.create_permanent(CREATURE, 0)
    enemy = current.create_permanent(CREATURE, 1)
    shielded = current.create_permanent(HEXPROOF, 1)
    for _ in range(4):
        current.create_permanent(SWAMP, 0)
    current.set_hand_for_testing(0, [frozen])
    option = next(
        option
        for option in current.legal_main_actions(0)
        if option.object_id == current.players[0].hand[0].object_id
    )
    current.execute_main_action(option)
    resolve(current)  # Spell resolves; ETB trigger gets its own Priority window.
    assert set(offered[0]) == {own.object_id, enemy.object_id}
    assert shielded.zone == "battlefield"
    assert enemy.zone == "former" and own.zone == "battlefield"
    assert any(e["event"] == "cost_paid" and e["card"] == frozen.name for e in current.events)
    assert any(
        e["event"] == "etb_creature_destroy_resolved" and e["destroyed"] for e in current.events
    )
    current.check_invariants()


def test_source_departure_does_not_cancel_trigger_and_target_id_stays_locked():
    current = setup()
    victim = current.create_permanent(CREATURE, 1)
    source = entry(current)
    assert current.stack[-1].effect is TriggerEffect.ETB_DESTROY_TARGET_CREATURE
    current.move_object(source, "graveyard", reason="response")
    resolve(current)
    assert victim.zone == "former"
    current.check_invariants()

    current = setup()
    victim = current.create_permanent(CREATURE, 1)
    source = entry(current)
    current.move_object(victim, "graveyard", reason="response")
    replacement = current.create_permanent(CREATURE, 1)
    resolve(current)
    assert source.zone == "battlefield" and replacement.zone == "battlefield"
    assert any(
        e["event"] == "etb_creature_destroy_resolved" and not e["legal_target"]
        for e in current.events
    )
    current.check_invariants()


def test_no_legal_target_and_invalid_choice_fail_closed():
    current = setup()
    current.create_permanent(HEXPROOF, 1)
    source = entry(current)
    assert source.zone == "battlefield" and not current.stack
    assert any(e["event"] == "etb_creature_destroy_no_legal_target" for e in current.events)

    current = setup(chooser=lambda *_: "fabricated-target")
    current.create_permanent(CREATURE, 1)
    with pytest.raises(ValueError, match="listed creature"):
        entry(current)


def test_indestructible_and_target_type_change_are_rechecked_at_resolution():
    current = setup()
    durable = current.create_permanent(INDESTRUCTIBLE, 1)
    entry(current)
    resolve(current)
    assert durable.zone == "battlefield"
    assert any(e["event"] == "destruction_prevented" for e in current.events)
    assert any(
        e["event"] == "etb_creature_destroy_resolved" and e["legal_target"] and not e["destroyed"]
        for e in current.events
    )

    current = setup()
    victim = current.create_permanent(CREATURE, 1)
    entry(current)
    victim.type_line_override = "Artifact"
    resolve(current)
    assert victim.zone == "battlefield"
    assert any(
        e["event"] == "etb_creature_destroy_resolved" and not e["legal_target"]
        for e in current.events
    )


def test_replay_and_tampered_target_provenance():
    def run():
        current = setup()
        victim = current.create_permanent(CREATURE, 1)
        source = entry(current)
        resolve(current)
        current.check_invariants()
        return current.snapshot(), current.events, source.object_id, victim.object_id

    assert run() == run()
    current = setup()
    current.create_permanent(CREATURE, 1)
    entry(current)
    current.stack[-1].target_id = "fabricated-target"
    with pytest.raises(AssertionError, match="invalid target provenance"):
        current.check_invariants()
