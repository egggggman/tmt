from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import Game, load_facts
from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec

ROOT = Path(__file__).resolve().parents[1]
LEVEL_TWO = "{1}{U}: Level 2"
RECOVERY = CardInterpreter.CLASS_LEVEL_TWO_RECOVERY


def _facts():
    catalog = load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    return load_facts(
        catalog,
        {"Does Machines", "Sewer-veillance Cam", "Fugitive Droid", "Island"},
    )


def _game():
    facts = _facts()
    deck = [facts["Island"], facts["Does Machines"]] * 20
    current = Game((deck, deck), seed=7)
    for _ in range(2):
        current.create_permanent(facts["Island"], 0, summoning_sick=False)
    source = current.create_permanent(facts["Does Machines"], 0)
    current.begin_turn()
    return current, source, facts


def _put_in_graveyard(current, cards):
    for card in list(current.set_hand_for_testing(0, cards)):
        current.move_object(card, "graveyard", reason="test_setup")


def _resolve_top(current):
    for _ in range(2):
        current.execute_priority_action(
            current.legal_priority_actions(current.priority_state.player_index)[0]
        )
    current.process_priority_resolution()


def test_does_machines_level_two_and_recovery_text_are_interpreted():
    card = _facts()["Does Machines"]
    interpreter = CardInterpreter()
    level = interpreter.activated_ability_semantics(card, LEVEL_TWO)

    assert level is not None
    assert level.coverage.fully_supported
    assert level.program.effect_kind is ActivatedEffectKind.ADVANCE_CLASS_LEVEL
    assert level.program.cost.mana_cost == "{1}{U}"
    assert interpreter.class_level_recovery_semantic_coverage(card, RECOVERY).fully_supported


def test_class_starts_at_level_one_and_pilot_gets_one_legal_level_action():
    current, source, _facts_by_name = _game()
    assert source.class_level == 1
    options = current.legal_main_actions(0)
    level_options = [option for option in options if option.oracle_fragment == LEVEL_TWO]

    assert len(level_options) == 1
    assert (
        AcceptancePilot().choose_main_action(current.public_view(), options, "activate")
        == (level_options[0])
    )


def test_insufficient_mana_prevents_level_advancement():
    current, source, _facts_by_name = _game()
    current.players[0].battlefield[0].tapped = True

    assert current.activation_payment_plan(0, source, LEVEL_TWO) is None
    assert not any(option.oracle_fragment == LEVEL_TWO for option in current.legal_main_actions(0))


def test_level_two_recovery_returns_only_up_to_two_artifacts_in_order():
    current, source, facts = _game()
    _put_in_graveyard(
        current,
        [facts["Sewer-veillance Cam"], facts["Fugitive Droid"], facts["Island"]],
    )
    current.activate_ability(0, source, LEVEL_TWO)
    _resolve_top(current)

    assert source.class_level == 2
    assert current.stack
    recovery = current.stack[-1]
    assert recovery.oracle_fragment == RECOVERY
    assert recovery.target_ids == tuple(sorted(recovery.target_ids))
    assert len(recovery.target_ids) == 2
    _resolve_top(current)

    assert [card.name for card in current.players[0].hand] == [
        "Sewer-veillance Cam",
        "Fugitive Droid",
    ]
    assert [card.name for card in current.players[0].graveyard] == ["Island"]
    assert any(
        event["event"] == "class_level_artifact_recovery_resolved" for event in current.events
    )


def test_recovery_is_unavailable_before_level_two_and_zero_targets_are_safe():
    current, source, facts = _game()
    assert not any(
        option.oracle_fragment == RECOVERY for option in current.legal_activated_ability_actions(0)
    )
    _put_in_graveyard(current, [facts["Island"]])
    current.activate_ability(0, source, LEVEL_TWO)
    _resolve_top(current)
    assert current.stack[-1].target_ids == ()
    _resolve_top(current)
    assert [card.name for card in current.players[0].graveyard] == ["Island"]
    assert any(
        event["event"] == "class_level_recovery_targets_selected" and event["selected_ids"] == []
        for event in current.events
    )


def test_level_state_and_recovery_event_replay_deterministically():
    def run_once():
        current, source, facts = _game()
        _put_in_graveyard(current, [facts["Sewer-veillance Cam"], facts["Fugitive Droid"]])
        current.activate_ability(0, source, LEVEL_TWO)
        _resolve_top(current)
        _resolve_top(current)
        return current

    first, second = run_once(), run_once()
    assert first.snapshot()["players"] == second.snapshot()["players"]
    assert [event for event in first.events if "class_level" in event["event"]] == [
        event for event in second.events if "class_level" in event["event"]
    ]


def test_real_donatello_seed_casts_does_machines_without_regression():
    result = run_smoke_game(
        ROOT,
        GameSpec(
            "donatello-shredder-does-machines-3002",
            "donatello/shredder",
            3002,
            "donatello-first",
            (
                DeckSpec("donatello-p0.3a", "decks/donatello/PROTOTYPE_0.3a.txt"),
                DeckSpec("shredder-p0.3", "decks/shredder/PROTOTYPE_0.3.txt"),
            ),
        ),
    )
    events = result["events"]

    assert result.get("error") is None
    assert any(
        event["event"] == "spell_cast" and event["card"] == "Does Machines" for event in events
    )
    assert any(event["event"] == "etb_mill_draw_discard_committed" for event in events)
