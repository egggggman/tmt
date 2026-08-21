import hashlib
import inspect
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import (
    ActivatedEffectKind,
    CardInterpreter,
    StrikeKeyword,
)
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    ActivatedAbilityObject,
    CardFact,
    Game,
    TurnStep,
)
from tmnt_design_studio.pilot07 import AcceptancePilot

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Plains", "", 0, "Basic Land — Plains", "({T}: Add {W}.)")
LEONARDO = CardFact(
    "Leonardo, Leader in Blue",
    "{2}{W}{W}",
    4,
    "Legendary Creature — Mutant Ninja Turtle",
    "{1}{W}: Leonardo gains first strike until end of turn.",
    3,
    4,
)
UNKNOWN_NAMES = {
    "Arcane Signet",
    "Chromatic Lantern",
    "Command Tower",
    "Double Jump // Flying Kick",
    "Exotic Orchard",
    "Fast Forward",
    "Plague of Vermin",
}
RECOGNIZED_DIGEST = "35ccf2712e06f6cd0b93d03dbb867e909a6c8350e3e84616d0cee9b14f067190"
EXECUTABLE_DIGEST = "c75e8cff62f3f9cc3e74243970f76fb80267d40422f9e748be5ba9bae5d886b1"


def game(seed=51):
    current = Game(([LAND] * 60, [LAND] * 60), seed=seed)
    current.begin_turn()
    return current


def add_mana(current, count=2):
    return [current.create_permanent(LAND, 0, summoning_sick=False) for _ in range(count)]


def add_leonardo(current, *, sick=False, fact=LEONARDO):
    return current.create_permanent(fact, 0, summoning_sick=sick)


def pass_priority_and_resolve(current):
    first = current.legal_priority_actions(current.priority_state.player_index)[0]
    current.execute_priority_action(first)
    second = current.legal_priority_actions(current.priority_state.player_index)[0]
    current.execute_priority_action(second)
    assert current.priority_state.resolution_pending
    current.process_priority_resolution()


def catalog():
    return load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )


def coverage_sets():
    interpreter = CardInterpreter()
    recognized, executable, full = [], [], []
    seen = set()
    for card in sorted(catalog().cards, key=lambda value: (value.name, value.oracle_id)):
        if card.oracle_id in seen:
            continue
        seen.add(card.oracle_id)
        for fragment in interpreter.fragments(card):
            semantics = interpreter.activated_ability_semantics(card, fragment)
            if semantics is None:
                continue
            member = (card.oracle_id, card.name, fragment)
            recognized.append(member)
            if semantics.coverage.payload_executable:
                executable.append(member)
            if semantics.coverage.fully_supported:
                full.append(member)
    return recognized, executable, full


def digest(members):
    encoded = json.dumps(members, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_interpreter_derives_bounded_self_strike_activation_without_card_dispatch():
    renamed = CardFact(
        "Renamed Hero",
        "",
        0,
        "Creature",
        "{1}{W}: Renamed Hero gains first strike until end of turn.",
        2,
        2,
    )
    semantics = CardInterpreter().activated_ability_semantics(renamed, renamed.oracle_text)
    assert semantics is not None
    assert semantics.activation_recognized
    assert semantics.activation_parent_executable
    assert semantics.costs_executable
    assert semantics.targets_choices_executable
    assert semantics.child_payload_executable
    assert semantics.followup_executable
    assert semantics.coverage.fully_supported
    assert semantics.program.effect_kind is ActivatedEffectKind.GRANT_SELF_FIRST_STRIKE_UNTIL_EOT


def test_engine_generates_immutable_activation_option_and_pilot_only_selects_it():
    current = game()
    add_mana(current)
    source = add_leonardo(current)
    options = current.legal_main_actions(0)
    activation = next(option for option in options if option.kind is ActionKind.ACTIVATE_ABILITY)
    assert activation.object_id == source.object_id
    assert activation.oracle_fragment == LEONARDO.oracle_text
    assert (
        AcceptancePilot().choose_main_action(current.public_view(), options, "activate")
        == activation
    )
    with pytest.raises(FrozenInstanceError):
        activation.object_id = "fabricated"


def test_announcement_pays_costs_and_uses_authoritative_stack_identity():
    current = game()
    lands = add_mana(current)
    source = add_leonardo(current)
    ability = current.announce_activated_ability(0, source, LEONARDO.oracle_text)
    assert isinstance(ability, ActivatedAbilityObject)
    assert current.stack == [ability]
    assert current.is_authoritative(ability, "stack")
    assert ability.source_id == source.object_id and ability.controller == source.controller == 0
    assert all(land.tapped for land in lands)
    assert not current.evaluated_strike_keywords(source)
    assert current.activation_evidence[-1].resolved is False

    pass_priority_and_resolve(current)
    assert not current.stack and ability.zone == "former"
    assert current.evaluated_strike_keywords(source) == {StrikeKeyword.FIRST_STRIKE}
    assert current.activation_evidence[-1].resolved is True


def test_failed_payment_is_atomic_and_does_not_create_stack_state():
    current = game()
    land = add_mana(current, 1)[0]
    source = add_leonardo(current)
    before = (land.tapped, source.tapped, tuple(current.stack), len(current.activation_evidence))
    assert current.announce_activated_ability(0, source, LEONARDO.oracle_text) is None
    assert (
        land.tapped,
        source.tapped,
        tuple(current.stack),
        len(current.activation_evidence),
    ) == before


def test_commit_failure_rolls_back_all_cost_and_identity_mutation(monkeypatch):
    current = game()
    lands = add_mana(current)
    source = add_leonardo(current)
    before_number = current._next_object_number

    def reject(_ability):
        raise ValueError("forced registration failure")

    monkeypatch.setattr(current, "_register", reject)
    with pytest.raises(ValueError, match="forced"):
        current.announce_activated_ability(0, source, LEONARDO.oracle_text)
    assert not any(land.tapped for land in lands)
    assert not source.tapped and not current.stack and not current.activation_evidence
    assert current._next_object_number == before_number


def test_fabricated_stale_wrong_controller_and_pilot_options_are_rejected():
    current = game()
    add_mana(current)
    source = add_leonardo(current)
    fabricated = type(source)(source.object_id, source.card, source.owner, source.controller)
    assert current.announce_activated_ability(0, fabricated, LEONARDO.oracle_text) is None
    current.change_controller(source, 1)
    assert current.announce_activated_ability(0, source, LEONARDO.oracle_text) is None
    current.change_controller(source, 0)
    stale = current.put_into_graveyard(source)
    assert stale.object_id != source.object_id
    assert current.announce_activated_ability(0, source, LEONARDO.oracle_text) is None

    fake_option = ActionOption(
        ActionKind.ACTIVATE_ABILITY,
        0,
        object_id="object-fabricated",
        oracle_fragment=LEONARDO.oracle_text,
    )
    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_main_action(fake_option)


def test_fabricated_targets_and_choices_cannot_broaden_bounded_activation():
    current = game()
    add_mana(current)
    source = add_leonardo(current)
    before = tuple(permanent.tapped for permanent in current.players[0].battlefield)
    assert (
        current.announce_activated_ability(
            0, source, LEONARDO.oracle_text, target_ids=("object-fabricated",)
        )
        is None
    )
    assert (
        current.announce_activated_ability(
            0, source, LEONARDO.oracle_text, choice_ids=("choice-fabricated",)
        )
        is None
    )
    assert tuple(permanent.tapped for permanent in current.players[0].battlefield) == before
    assert not current.stack


def test_tap_cost_respects_tapped_and_summoning_sick_source():
    tapper = CardFact(
        "Renamed Tapper",
        "",
        0,
        "Creature",
        "{T}: This creature gains first strike until end of turn.",
        2,
        2,
    )
    current = game()
    source = add_leonardo(current, sick=True, fact=tapper)
    assert current.activation_payment_plan(0, source, tapper.oracle_text) is None
    source.summoning_sick = False
    assert current.activation_payment_plan(0, source, tapper.oracle_text) is not None
    source.tapped = True
    assert current.activation_payment_plan(0, source, tapper.oracle_text) is None


def test_resolution_requires_authoritative_top_stack_object():
    current = game()
    add_mana(current)
    source = add_leonardo(current)
    ability = current.announce_activated_ability(0, source, LEONARDO.oracle_text)
    assert ability is not None
    fabricated = ActivatedAbilityObject(
        ability.object_id,
        ability.controller,
        ability.source_id,
        ability.source_card,
        ability.oracle_fragment,
        ability.program,
        ability.mana_source_ids,
        ability.tap_source,
    )
    with pytest.raises(ValueError, match="authoritative top"):
        current._resolve_activated_ability(fabricated)
    assert current.stack == [ability] and not current.evaluated_strike_keywords(source)


def test_source_leaving_before_resolution_does_not_bind_replacement_object():
    current = game()
    add_mana(current)
    source = add_leonardo(current)
    ability = current.announce_activated_ability(0, source, LEONARDO.oracle_text)
    assert ability is not None
    replacement_card = current.put_into_graveyard(source)
    replacement = current.move_object(replacement_card, "battlefield", controller=0)
    pass_priority_and_resolve(current)
    assert replacement.object_id != source.object_id
    assert not current.evaluated_strike_keywords(replacement)
    assert any(event["event"] == "activated_ability_resolved_no_effect" for event in current.events)


def test_temporary_first_strike_affects_combat_then_expires_at_cleanup():
    current = game()
    add_mana(current)
    source = add_leonardo(current)
    assert current.activate_ability(0, source, LEONARDO.oracle_text)
    pass_priority_and_resolve(current)
    assert current.evaluated_strike_keywords(source) == {StrikeKeyword.FIRST_STRIKE}
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        option
        for option in current.legal_attack_options(0)
        if option.attacker_ids == (source.object_id,)
    )
    current.execute_attack_action(attack)
    current.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))
    first = current.resolve_combat_damage()
    regular = current.resolve_combat_damage()
    assert [assignment.role for assignment in first.assignments] == ["first_strike"]
    assert not regular.assignments
    current.advance_to(TurnStep.CLEANUP)
    assert not current.evaluated_strike_keywords(source)


def test_activation_priority_states_are_observably_distinct_and_engine_owned():
    current = game()
    lands = add_mana(current)
    source = add_leonardo(current)
    activation = next(
        option
        for option in current.legal_main_actions(0)
        if option.kind is ActionKind.ACTIVATE_ABILITY
    )

    assert not current.stack and current.priority_state is None
    current.execute_main_action(activation)
    ability = current.stack[-1]
    assert isinstance(ability, ActivatedAbilityObject)
    assert all(land.tapped for land in lands)
    assert not current.evaluated_strike_keywords(source)
    assert current.priority_state.player_index == current.active_player

    first = current.legal_priority_actions(0)[0]
    current.execute_priority_action(first)
    assert current.stack == [ability]
    assert current.priority_state.consecutive_passes == (0,)
    assert current.priority_state.player_index == 1
    assert not current.evaluated_strike_keywords(source)

    second = current.legal_priority_actions(1)[0]
    current.execute_priority_action(second)
    assert current.stack == [ability]
    assert current.priority_state.consecutive_passes == (0, 1)
    assert current.priority_state.resolution_pending
    assert not current.evaluated_strike_keywords(source)

    current.process_priority_resolution()
    assert not current.stack and current.priority_state is None
    assert ability.zone == "former"
    assert current.evaluated_strike_keywords(source) == {StrikeKeyword.FIRST_STRIKE}


def test_priority_rejects_wrong_fabricated_stale_and_duplicate_passes_atomically():
    current = game()
    add_mana(current)
    source = add_leonardo(current)
    assert current.activate_ability(0, source, LEONARDO.oracle_text)
    before = current.snapshot()
    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_priority_action(ActionOption(ActionKind.PASS_PRIORITY, 1))
    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_priority_action(
            ActionOption(ActionKind.PASS_PRIORITY, 0, priority_epoch=999)
        )
    assert current.snapshot() == before

    stale = current.legal_priority_actions(0)[0]
    current.execute_priority_action(stale)
    after_first = current.snapshot()
    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_priority_action(stale)
    assert current.snapshot() == after_first


def test_resolution_requires_two_passes_and_cannot_repeat_or_refund_costs():
    current = game()
    lands = add_mana(current)
    source = add_leonardo(current)
    assert current.activate_ability(0, source, LEONARDO.oracle_text)
    ability = current.stack[-1]
    with pytest.raises(ValueError, match="not permitted"):
        current.process_priority_resolution()
    with pytest.raises(ValueError, match="before all players pass"):
        current.resolve_top_of_stack()
    current.execute_priority_action(current.legal_priority_actions(0)[0])
    with pytest.raises(ValueError, match="not permitted"):
        current.process_priority_resolution()
    assert current.stack == [ability] and all(land.tapped for land in lands)
    current.execute_priority_action(current.legal_priority_actions(1)[0])
    current.process_priority_resolution()
    assert all(land.tapped for land in lands)
    with pytest.raises(ValueError, match="not permitted"):
        current.process_priority_resolution()
    with pytest.raises(ValueError, match="empty stack"):
        current.resolve_top_of_stack()


def test_represented_action_between_passes_resets_consecutive_passes():
    current = game()
    add_mana(current)
    source = add_leonardo(current)
    assert current.activate_ability(0, source, LEONARDO.oracle_text)
    current.execute_priority_action(current.legal_priority_actions(0)[0])
    assert current.priority_state.consecutive_passes == (0,)
    current._record_represented_priority_action(1)
    assert current.priority_state.consecutive_passes == ()
    assert current.priority_state.player_index == 1
    current.execute_priority_action(current.legal_priority_actions(1)[0])
    assert current.priority_state.consecutive_passes == (1,)
    assert not current.priority_state.resolution_pending


def test_new_priority_window_does_not_reuse_prior_pass_bookkeeping():
    current = game()
    add_mana(current, 4)
    source = add_leonardo(current)
    assert current.activate_ability(0, source, LEONARDO.oracle_text)
    first_epoch = current.priority_state.epoch
    pass_priority_and_resolve(current)
    assert current.activate_ability(0, source, LEONARDO.oracle_text)
    assert current.priority_state.epoch != first_epoch
    assert current.priority_state.consecutive_passes == ()
    assert not current.priority_state.resolution_pending


def test_priority_resolves_authoritative_lifo_and_restarts_for_remaining_stack():
    current = game()
    add_mana(current)
    source = add_leonardo(current)
    assert current.activate_ability(0, source, LEONARDO.oracle_text)
    first = current.stack[-1]
    second = ActivatedAbilityObject(
        current._allocate_object_id(),
        first.controller,
        first.source_id,
        first.source_card,
        first.oracle_fragment,
        first.program,
        (),
        False,
    )
    current._register(second)
    current.stack.append(second)
    current._record_represented_priority_action(0)

    pass_priority_and_resolve(current)
    assert second.zone == "former" and current.stack == [first]
    assert current.priority_state is not None
    assert current.priority_state.consecutive_passes == ()
    pass_priority_and_resolve(current)
    assert first.zone == "former" and not current.stack


def test_priority_state_clears_if_resolution_ends_game(monkeypatch):
    current = game()
    add_mana(current)
    source = add_leonardo(current)
    assert current.activate_ability(0, source, LEONARDO.oracle_text)
    original = current._resolve_activated_ability

    def resolve_and_end(ability):
        original(ability)
        current.winner = 0

    monkeypatch.setattr(current, "_resolve_activated_ability", resolve_and_end)
    pass_priority_and_resolve(current)
    assert current.winner == 0
    assert current.priority_state is None


def test_priority_option_is_immutable_and_pilot_cannot_name_stack_resolution():
    current = game()
    add_mana(current)
    source = add_leonardo(current)
    assert current.activate_ability(0, source, LEONARDO.oracle_text)
    option = current.legal_priority_actions(0)[0]
    assert AcceptancePilot().choose_priority(current.public_view(), (option,)) == option
    assert option.object_id is None and option.target_id is None
    with pytest.raises(FrozenInstanceError):
        option.priority_epoch = 10


@pytest.mark.parametrize(
    "text, reason",
    [
        (
            "{2}, {T}, Sacrifice this token: You gain 3 life.",
            "activation_nonmana_cost_not_implemented",
        ),
        (
            "{1}, {T}: Return target creature to its owner's hand.",
            "activation_targets_choices_not_implemented",
        ),
        (
            "{X}: This creature gains first strike until end of turn.",
            "activation_complex_mana_cost_not_implemented",
        ),
        ("{1}: Draw a card.", "activation_child_semantics_not_implemented"),
        (
            "Equip {2} ({2}: Attach to target creature you control.)",
            "activation_nested_context_not_implemented",
        ),
    ],
)
def test_unsupported_cost_target_child_and_nested_forms_remain_explicit(text, reason):
    card = CardFact("Renamed", "", 0, "Artifact", text)
    semantics = CardInterpreter().activated_ability_semantics(card, text)
    assert semantics is not None and reason in semantics.limitations
    assert not semantics.coverage.fully_supported


def test_generic_coverage_keeps_executable_parent_costs_and_choices_separate_from_child():
    card = CardFact("Renamed", "", 0, "Artifact", "{1}: Draw a card.")
    semantics = CardInterpreter().activated_ability_semantics(card, card.oracle_text)
    assert semantics is not None
    assert semantics.activation_parent_executable
    assert semantics.costs_executable
    assert semantics.targets_choices_executable
    assert not semantics.child_payload_executable
    assert not semantics.coverage.payload_executable
    assert semantics.coverage.parent_executable
    assert not semantics.coverage.fully_supported


def test_supported_child_does_not_upgrade_an_unsupported_activation_followup():
    card = CardFact(
        "Renamed Hero",
        "",
        0,
        "Creature",
        "{1}: Renamed Hero gains first strike until end of turn. Draw a card.",
        2,
        2,
    )
    semantics = CardInterpreter().activated_ability_semantics(card, card.oracle_text)
    assert semantics is not None and semantics.child_payload_executable
    assert semantics.activation_parent_executable and semantics.costs_executable
    assert not semantics.followup_executable
    assert "activation_followup_semantics_not_implemented" in semantics.limitations
    assert not semantics.coverage.fully_supported


def test_food_mutagen_treasure_clue_and_equipment_are_not_enabled():
    interpreter = CardInterpreter()
    texts = (
        "{2}, {T}, Sacrifice this token: You gain 3 life.",
        (
            "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. "
            "Activate only as a sorcery."
        ),
        "{T}, Sacrifice this token: Add one mana of any color.",
        "{2}, Sacrifice this token: Draw a card.",
        "Equip {2} ({2}: Attach to target creature you control.)",
    )
    for text in texts:
        card = CardFact("Renamed", "", 0, "Artifact", text)
        semantics = interpreter.activated_ability_semantics(card, text)
        assert semantics is not None and not semantics.coverage.fully_supported


def test_authoritative_activation_memberships_and_digests_are_locked():
    recognized, executable, full = coverage_sets()
    assert len({item[0] for item in recognized}) == 131 and len(recognized) == 156
    assert len({item[0] for item in executable}) == 2 and len(executable) == 2
    assert full == executable
    assert {item[1] for item in executable} == {
        "Leonardo, Leader in Blue",
        "Prehistoric Pet",
    }
    assert digest(recognized) == RECOGNIZED_DIGEST
    assert digest(executable) == EXECUTABLE_DIGEST
    assert digest(full) == EXECUTABLE_DIGEST


def test_frozen_activation_memberships_and_unknown_universe_are_locked():
    recognized, executable, full = coverage_sets()
    decks = {
        directory.name: {
            line.split(" ", 1)[1]
            for line in (
                directory
                / (
                    "PROTOTYPE_0.2.txt"
                    if directory.name in {"donatello", "krang"}
                    else "PROTOTYPE_0.1.txt"
                )
            )
            .read_text(encoding="utf-8")
            .splitlines()
            if line and line != "Deck"
        }
        for directory in ROOT.glob("decks/*")
        if directory.is_dir()
    }
    roster = set().union(*decks.values())
    assert len(roster) == 102 and len(decks) == 10
    recognized_names = {item[1] for item in recognized} & roster
    executable_names = {item[1] for item in executable} & roster
    assert len(recognized_names) == 45
    assert {name for name, cards in decks.items() if cards & recognized_names} == set(decks)
    assert executable_names == {"Leonardo, Leader in Blue", "Prehistoric Pet"}
    assert {name for name, cards in decks.items() if cards & executable_names} == {"leonardo"}
    assert full == executable
    assert {
        "Arcane Signet",
        "Chromatic Lantern",
        "Command Tower",
        "Double Jump // Flying Kick",
        "Exotic Orchard",
        "Fast Forward",
        "Plague of Vermin",
    } == UNKNOWN_NAMES


def test_no_card_name_acceptance_seed_or_special_case_dispatch():
    sources = (
        inspect.getsource(CardInterpreter.activated_ability_semantics),
        inspect.getsource(Game.legal_activated_ability_actions),
        inspect.getsource(Game.announce_activated_ability),
        inspect.getsource(Game._resolve_activated_ability),
    )
    prohibited = {
        "Leonardo, Leader in Blue",
        "Lita, Little Orphan Amphibian",
        "Mutagen",
        "Treasure",
        "Clue",
        "7001",
    }
    assert all(name not in source for name in prohibited for source in sources)
