"""Complete Oracle-derived temporary artifact creature animation and draw."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
    TurnStep,
    load_facts,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
FACTS = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")),
    {"Mind Transfer Protocol", "Retro-Mutation"},
)
PROTOCOL = FACTS["Mind Transfer Protocol"]
AURA = FACTS["Retro-Mutation"]
ISLAND = CardFact("Island", "", 0, "Basic Land — Island")
BEAR = CardFact("Quiet Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
RELIC = CardFact("Quiet Relic", "{2}", 2, "Artifact — Clue")
EQUIPMENT = CardFact("Quiet Equipment", "{2}", 2, "Artifact — Equipment")
LAND = CardFact("Quiet Shore", "", 0, "Land")


def game(*, lands=3, seed=312):
    current = Game(([ISLAND] * 40, [ISLAND] * 40), seed=seed)
    current.begin_turn()
    for _ in range(lands):
        current.create_permanent(ISLAND, 0)
    card = current.set_hand_for_testing(0, [PROTOCOL])[0]
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


def test_complete_oracle_parser_and_fail_closed_near_neighbors():
    interpreter = CardInterpreter()
    for card in (PROTOCOL, replace(PROTOCOL, name="Unnamed Transfer")):
        program = interpreter.temporary_type_base_pt_draw_program(card)
        assert program is not None
        assert program.target_types == {"artifact", "creature"}
        assert (program.added_types, program.power, program.toughness, program.draw_quantity) == (
            ("Artifact", "Creature"),
            4,
            5,
            1,
        )
        assert interpreter.cast_program(card).kind is CastKind.TEMPORARY_TYPE_BASE_PT_DRAW
        assert interpreter.unsupported_fragments(card) == ()
    for text in (
        PROTOCOL.oracle_text + "\nGain 2 life.",
        PROTOCOL.oracle_text.replace("Draw a card.", "Scry 1."),
        PROTOCOL.oracle_text.replace("4/5", "X/5"),
        PROTOCOL.oracle_text.replace("target artifact or creature", "target permanent"),
        PROTOCOL.oracle_text.replace("Until end of turn", "Until your next turn"),
        PROTOCOL.oracle_text.replace("Draw a card.", "Draw two cards.\nScry 1."),
    ):
        partial = replace(PROTOCOL, oracle_text=text)
        assert interpreter.temporary_type_base_pt_draw_program(partial) is None
        assert interpreter.cast_program(partial).kind is CastKind.UNSUPPORTED


def test_paid_cast_legal_artifact_and_creature_targets_and_no_land_or_hexproof():
    current, card = game()
    artifact = current.create_permanent(RELIC, 0)
    creature = current.create_permanent(BEAR, 1)
    land = current.create_permanent(LAND, 1)
    protected = current.create_permanent(
        replace(BEAR, name="Protected Bear", keywords=("Hexproof",)), 1
    )
    actions = [
        action for action in current.legal_main_actions(0) if action.object_id == card.object_id
    ]
    assert {action.target_id for action in actions} == {artifact.object_id, creature.object_id}
    assert land.object_id not in {action.target_id for action in actions}
    assert protected.object_id not in {action.target_id for action in actions}
    assert current.announce_spell(0, card, land) is None
    assert current.announce_spell(0, card, protected) is None
    assert current.announce_spell(0, card, None) is None
    assert card.zone == "hand" and not any(e["event"] == "cost_paid" for e in current.events)
    before = len(current.players[0].hand)
    assert current.execute_main_action(
        next(a for a in actions if a.target_id == artifact.object_id)
    )
    spell = current.stack[-1]
    assert spell.target_id == artifact.object_id and artifact.type_line == "Artifact — Clue"
    paid = next(e for e in current.events if e["event"] == "cost_paid")
    assert paid["generic"] == 2 and paid["colored"] == ["U"]
    drain(current)
    assert len(current.players[0].hand) == before
    assert artifact.type_line == "Artifact Creature — Clue"
    assert (artifact.power, artifact.toughness) == (4, 5)
    assert (
        next(e for e in current.events if e["event"] == "temporary_animation_draw_resolved")[
            "source_id"
        ]
        == spell.object_id
    )
    current.check_invariants()


def test_payment_staleness_and_priority_response_are_transactional():
    current, card = game(lands=2)
    target = current.create_permanent(RELIC, 0)
    assert not any(a.object_id == card.object_id for a in current.legal_main_actions(0))
    assert current.announce_spell(0, card, target) is None
    assert target.type_line == "Artifact — Clue" and card.zone == "hand"
    current.create_permanent(ISLAND, 0)
    current._begin_priority_window(allow_empty=True, priority_player=0)
    response = next(a for a in current.legal_priority_actions(0) if a.object_id == card.object_id)
    current.execute_priority_action(response)
    assert target.type_line == "Artifact — Clue" and current.stack[-1].target_id == target.object_id
    drain(current)
    assert target.type_line == "Artifact Creature — Clue"
    current.check_invariants()


def test_changed_or_departed_target_fizzles_without_followup_draw():
    for leave in (False, True):
        current, card = game()
        target = current.create_permanent(RELIC, 0)
        before = len(current.players[0].hand)
        spell = current.announce_spell(0, card, target)
        assert spell is not None
        if leave:
            current.move_object(target, "graveyard", reason="target_departed")
        else:
            target.type_line_override = "Land"
        current.resolve_top_of_stack()
        assert len(current.players[0].hand) == before - 1
        assert not any(e["event"] == "temporary_animation_draw_resolved" for e in current.events)
        assert any(e["event"] == "spell_resolved_no_effect" for e in current.events)
        current.check_invariants()


def test_base_pt_layer_counters_and_cleanup_preserve_intrinsic_creature():
    current, card = game()
    target = current.create_permanent(
        replace(BEAR, name="Legendary Bear", type_line="Legendary Creature — Bear"), 0
    )
    target.counters["+1/+1"] = 1
    current.apply_pt_modifier(
        target,
        2,
        -1,
        duration="until_end_of_turn",
        source_card="Generic Modifier",
        oracle_fragment="Target creature gets +2/-1 until end of turn.",
    )
    current.announce_spell(0, card, target)
    current.resolve_top_of_stack()
    assert target.type_line == "Legendary Artifact Creature — Bear"
    assert (target.power, target.toughness) == (7, 5)
    current.end_turn()
    assert target.type_line == "Legendary Creature — Bear"
    assert (target.power, target.toughness) == (3, 3)
    assert not target.temporary_type_effects
    assert not any(
        effect.duration == "until_end_of_turn" for effect in target.characteristic_effects
    )
    current.check_invariants()


def test_later_base_pt_set_overwrites_aura_then_aura_reasserts_on_cleanup():
    current, card = game()
    target = current.create_permanent(BEAR, 0)
    aura = current.create_permanent(AURA, 1)
    aura.attached_to = target.object_id
    aura.attachment_timestamp = current._effect_timestamp()
    current.refresh_static_pt_modifiers()
    assert (target.power, target.toughness) == (0, 1)
    current.announce_spell(0, card, target)
    current.resolve_top_of_stack()
    assert target.type_line.startswith("Artifact Creature")
    assert (target.power, target.toughness) == (4, 5)
    current.end_turn()
    assert (target.power, target.toughness) == (0, 1)
    current.check_invariants()


def test_zone_change_drops_temporary_type_and_base_pt_effects():
    current, card = game()
    artifact = current.create_permanent(RELIC, 0)
    current.announce_spell(0, card, artifact)
    current.resolve_top_of_stack()
    grave = current.move_object(artifact, "graveyard", reason="test_departure")
    returned = current.move_object(grave, "battlefield", reason="test_return")
    assert returned.object_id != artifact.object_id
    assert not returned.is_creature and returned.type_line == "Artifact — Clue"
    assert not returned.temporary_type_effects and not returned.characteristic_effects
    current.check_invariants()


def test_animated_artifact_can_block_and_attack_when_controlled_since_turn_start():
    current, card = game()
    artifact = current.create_permanent(RELIC, 0, summoning_sick=False)
    opposing = current.create_permanent(BEAR, 1, summoning_sick=False)
    current.announce_spell(0, card, artifact)
    current.resolve_top_of_stack()
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    assert artifact in current.legal_attackers(0)
    assert any(
        option.attacker_ids == (artifact.object_id,) for option in current.legal_attack_options(0)
    )
    current.execute_attack_action(ActionOption(ActionKind.DECLARE_ATTACKERS, 0, attacker_ids=()))
    assert current.can_block(opposing, artifact, 0)
    current.end_turn()
    assert not artifact.is_creature and artifact.type_line == "Artifact — Clue"
    current.check_invariants()


def test_equipment_that_becomes_a_creature_detaches_without_reentering():
    current, card = game()
    equipment = current.create_permanent(EQUIPMENT, 0)
    recipient = current.create_permanent(BEAR, 0)
    equipment.attached_to = recipient.object_id
    current.announce_spell(0, card, equipment)
    current.resolve_top_of_stack()
    assert equipment.is_creature and equipment.attached_to is None
    assert any(
        event["event"] == "equipment_detached" and event["source_id"] == equipment.object_id
        for event in current.events
    )
    assert not any(
        event["event"] == "creature_entered" and event.get("object_id") == equipment.object_id
        for event in current.events
    )
    current.end_turn()
    assert equipment.type_line == "Artifact — Equipment" and equipment.attached_to is None
    current.check_invariants()


def test_animated_artifact_zero_toughness_dies_by_state_based_actions():
    current, card = game()
    artifact = current.create_permanent(RELIC, 0)
    artifact.counters["-1/-1"] = 5
    current.announce_spell(0, card, artifact)
    current.resolve_top_of_stack()
    assert artifact.zone == "former"
    assert any(obj.card is RELIC for obj in current.players[0].graveyard)
    current.check_invariants()


def test_failed_draw_is_checked_after_full_spell_resolution():
    current, card = game()
    artifact = current.create_permanent(RELIC, 0)
    for card_in_library in tuple(current.players[0].library):
        current.move_object(card_in_library, "graveyard", reason="test_exhaustion")
    current.announce_spell(0, card, artifact)
    current.resolve_top_of_stack()
    assert artifact.is_creature and (artifact.power, artifact.toughness) == (4, 5)
    assert current.players[0].lost and current.players[0].loss_reason == "draw_from_empty_library"
    assert (
        next(e for e in current.events if e["event"] == "temporary_animation_draw_resolved")[
            "draw_succeeded"
        ]
        is False
    )


def test_countered_spell_does_not_leak_effects_and_replay():
    def run():
        current, card = game(seed=417)
        artifact = current.create_permanent(RELIC, 0)
        spell = current.announce_spell(0, card, artifact)
        current.move_object(spell, "graveyard", reason="countered")
        current.priority_state = None
        assert not artifact.is_creature and not artifact.temporary_type_effects
        assert not any(e["event"] == "temporary_animation_draw_resolved" for e in current.events)
        current.check_invariants()
        return current.snapshot()

    assert run() == run()
