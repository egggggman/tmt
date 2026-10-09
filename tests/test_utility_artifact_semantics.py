"""Frozen artifacts exercise generic entry, departure, activated, and pilot semantics."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TurnStep, load_facts
from tmnt_design_studio.pilot07 import AcceptancePilot

ROOT = Path(__file__).resolve().parents[1]
CATALOG = load_card_data(
    ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
    ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
)
FACTS = load_facts(CATALOG, {"Sewer-veillance Cam", "Bespoke Bō", "Skateboard", "Island"})
BEAR = CardFact("Unrelated Bear", "{1}{U}", 2, "Creature", power=3, toughness=3)


def game():
    g = Game(([FACTS["Island"]] * 40, [FACTS["Island"]] * 40), seed=289)
    g.begin_turn()
    for _ in range(4):
        g.create_permanent(FACTS["Island"], 0, summoning_sick=False)
    return g


def resolve(g):
    while g.priority_state is not None:
        if g.priority_state.resolution_pending:
            g.process_priority_resolution()
        else:
            g.execute_priority_action(g.legal_priority_actions(g.priority_state.player_index)[0])


def cast(g, card):
    g.set_hand_for_testing(0, [card])
    choice = next(
        option
        for option in g.legal_main_actions(0)
        if option.kind is ActionKind.CAST and option.object_id == g.players[0].hand[0].object_id
    )
    g.execute_main_action(choice)
    resolve(g)
    return next(p for p in g.players[0].battlefield if p.card is card)


def test_utility_patterns_are_oracle_derived_and_reject_neighbors():
    interpreter = CardInterpreter()
    for name in ("Sewer-veillance Cam", "Bespoke Bō", "Skateboard"):
        assert not interpreter.unsupported_fragments(FACTS[name])
    cam = FACTS["Sewer-veillance Cam"]
    fragment = cam.oracle_text.splitlines()[1]
    renamed = replace(cam, name="Observation Lens")
    assert interpreter.utility_trigger_semantics(renamed, fragment) == (
        "entry_or_leave",
        "tap_or_untap_creature",
        False,
    )
    assert (
        interpreter.utility_trigger_semantics(
            renamed, fragment.replace("target creature", "target permanent")
        )
        is None
    )
    activation = interpreter.activated_ability_semantics(cam, cam.oracle_text.splitlines()[-1])
    assert activation and activation.coverage.fully_supported
    assert activation.program.effect_kind is ActivatedEffectKind.DRAW_CARDS


def test_pilot_can_select_generic_utility_or_prioritize_creature():
    for name in ("Sewer-veillance Cam", "Bespoke Bō", "Skateboard"):
        g = game()
        g.set_hand_for_testing(0, [FACTS[name]])
        cast_options = [o for o in g.legal_main_actions(0) if o.kind is ActionKind.CAST]
        assert len(cast_options) == 1
        assert (
            AcceptancePilot().choose_main_action(
                g.pilot_view(0), tuple(g.legal_main_actions(0)), "creature"
            )
            == cast_options[0]
        )
    g = game()
    g.set_hand_for_testing(0, [FACTS["Sewer-veillance Cam"], BEAR])
    chosen = AcceptancePilot().choose_main_action(
        g.pilot_view(0), tuple(g.legal_main_actions(0)), "creature"
    )
    assert chosen.object_id == g.players[0].hand[1].object_id


def test_skateboard_entry_taps_target_permanent_at_priority_resolution():
    g = game()
    target = g.create_permanent(BEAR, 1)
    g.set_hand_for_testing(0, [FACTS["Skateboard"]])
    option = next(o for o in g.legal_main_actions(0) if o.kind is ActionKind.CAST)
    g.execute_main_action(option)
    assert not target.tapped
    assert g.stack[-1].target_id == target.object_id
    resolve(g)
    assert target.tapped
    assert any(
        e["event"] == "utility_trigger_resolved" and e["effect"] == "tap_permanent"
        for e in g.events
    )


def test_bespoke_bo_bounces_other_nonland_or_declines_when_none():
    g = game()
    target = g.create_permanent(BEAR, 1)
    cast(g, FACTS["Bespoke Bō"])
    assert target.zone == "former"
    assert any(card.card is BEAR for card in g.players[1].hand)
    g.check_invariants()
    empty = game()
    cast(empty, FACTS["Bespoke Bō"])
    assert any(
        e["event"] == "utility_trigger_resolved" and e["result"] == "no_legal_target"
        for e in empty.events
    )


def test_cam_entry_and_leave_are_distinct_triggers_with_source_zone_transition():
    g = game()
    first = g.create_permanent(BEAR, 1)
    cam = cast(g, FACTS["Sewer-veillance Cam"])
    assert first.tapped
    second = g.create_permanent(BEAR, 1)
    g.put_into_graveyard(cam)
    g.check_state_based_actions()
    assert cam.zone == "former" and g.stack[-1].target_id == second.object_id
    resolve(g)
    assert second.tapped
    records = [e for e in g.events if e["event"] == "utility_trigger_resolved"]
    assert len(records) == 2 and len({e["event_id"] for e in records}) == 2


def test_cam_sacrifice_cost_triggers_leave_before_draw_two_resolves():
    g = game()
    target = g.create_permanent(BEAR, 1)
    source = g.create_permanent(FACTS["Sewer-veillance Cam"], 0)
    choice = next(
        o
        for o in g.legal_main_actions(0)
        if o.kind is ActionKind.ACTIVATE_ABILITY and o.object_id == source.object_id
    )
    original_hand = len(g.players[0].hand)
    g.execute_main_action(choice)
    assert source.zone == "former" and not target.tapped
    assert len(g.stack) == 2
    resolve(g)
    assert target.tapped and len(g.players[0].hand) == original_hand + 2
    result = [e for e in g.events if e["event"] == "activated_draw_resolved"]
    assert len(result) == 1 and result[0]["cards_drawn"] == 2
    assert (
        next(e for e in g.events if e["event"] == "utility_trigger_resolved")["target_id"]
        == target.object_id
    )
    g.check_invariants()


def test_target_leaving_before_trigger_resolves_does_not_affect_new_incarnation():
    g = game()
    target = g.create_permanent(BEAR, 1)
    g.set_hand_for_testing(0, [FACTS["Skateboard"]])
    g.execute_main_action(next(o for o in g.legal_main_actions(0) if o.kind is ActionKind.CAST))
    moved = g.move_object(target, "hand", reason="test_removal")
    returned = g.move_object(moved, "battlefield", reason="test_return")
    resolve(g)
    assert not returned.tapped
    assert any(
        e["event"] == "utility_trigger_resolved" and e["result"] == "no_legal_target"
        for e in g.events
    )


def test_flash_artifact_has_priority_cast_option_during_opponents_turn():
    g = game()
    g.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = g.legal_attack_options(0)[0]
    g.execute_attack_action(attack)
    g.execute_block_action(g.legal_block_options(attack, 1)[0])
    g.resolve_combat_damage()
    g.advance_to(TurnStep.CLEANUP)
    g.begin_turn()
    assert g.active_player == 1
    g.set_hand_for_testing(0, [FACTS["Sewer-veillance Cam"]])
    g._begin_priority_window(allow_empty=True)
    g.execute_priority_action(g.legal_priority_actions(1)[0])
    option = next(
        o
        for o in g.legal_priority_actions(0)
        if o.kind is ActionKind.CAST and o.object_id == g.players[0].hand[0].object_id
    )
    g.execute_priority_action(option)
    resolve(g)
    assert any(p.card is FACTS["Sewer-veillance Cam"] for p in g.players[0].battlefield)


def test_utility_sequence_is_deterministic():
    def execute():
        g = game()
        g.create_permanent(BEAR, 1)
        cast(g, FACTS["Sewer-veillance Cam"])
        g.check_invariants()
        return g.snapshot()

    assert execute() == execute()
