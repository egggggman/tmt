import hashlib
import inspect
import json
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    CharacteristicEffect,
    CharacteristicLayer,
    CharacteristicOperation,
    CombatDamageStepKind,
    Game,
    PowerToughnessSubLayer,
    TurnStep,
)
from tmnt_design_studio.semantic_coverage import SemanticCoverage

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
TRAMPLER = CardFact(
    "Generic Tramper", "{3}{G}", 4, "Creature — Beast", "Trample", 5, 5, ("Trample",)
)
FIRST_TRAMPLER = CardFact(
    "Generic First Tramper",
    "{3}{G}",
    4,
    "Creature — Beast",
    "First strike\nTrample",
    5,
    5,
    ("First strike", "Trample"),
)
DOUBLE_TRAMPLER = CardFact(
    "Generic Double Tramper",
    "{3}{G}",
    4,
    "Creature — Beast",
    "Double strike\nTrample",
    5,
    5,
    ("Double strike", "Trample"),
)
FIRST_BLOCKER = CardFact(
    "First Blocker", "{1}{W}", 2, "Creature — Soldier", "First strike", 5, 2, ("First strike",)
)
RECOGNIZED_NAMES = {
    "General Traag, Heart of Stone",
    "Genghis Frog",
    "Groundchuck & Dirtbag",
    "Heroes in a Half Shell",
    "Krang, Utrom Warlord",
    "Leatherhead, Iron Gator",
    "Leatherhead, Swamp Stalker",
    "Leonardo, the Balance",
    "Michelangelo, On the Scene",
    "Michelangelo, the Heart",
    "Mutagen Man, Living Ooze",
    "Mutant Town Musicians",
    "Novel Nunchaku",
    "Primordial Pachyderm",
    "Raph & Mikey, Troublemakers",
    "Rocksteady, Mutant Marauder",
    "Savanti Romero, Time's Exile",
    "Saved by the Shell",
    "Shadowspear",
    "Technodrome",
    "The Last Ronin",
    "Vigor",
    "Voracious Hydra",
    "West Wind Avatar",
    "Zog, Triceraton Castaway",
}
EXECUTABLE_NAMES = {
    "General Traag, Heart of Stone",
    "Genghis Frog",
    "Groundchuck & Dirtbag",
    "Heroes in a Half Shell",
    "Krang, Utrom Warlord",
    "Leatherhead, Iron Gator",
    "Leatherhead, Swamp Stalker",
    "Michelangelo, On the Scene",
    "Michelangelo, the Heart",
    "Mutagen Man, Living Ooze",
    "Mutant Town Musicians",
    "Primordial Pachyderm",
    "Raph & Mikey, Troublemakers",
    "Rocksteady, Mutant Marauder",
    "Savanti Romero, Time's Exile",
    "Technodrome",
    "Vigor",
    "Voracious Hydra",
    "West Wind Avatar",
    "Zog, Triceraton Castaway",
}
FULL_NAMES = {
    "General Traag, Heart of Stone",
    "Genghis Frog",
    "Groundchuck & Dirtbag",
    "Leatherhead, Iron Gator",
    "Leatherhead, Swamp Stalker",
    "Michelangelo, On the Scene",
    "Michelangelo, the Heart",
    "Mutagen Man, Living Ooze",
    "Mutant Town Musicians",
    "Raph & Mikey, Troublemakers",
    "Rocksteady, Mutant Marauder",
    "Savanti Romero, Time's Exile",
    "Vigor",
    "Voracious Hydra",
    "West Wind Avatar",
}


def game(seed=701):
    current = Game(([LAND] * 60, [LAND] * 60), seed=seed)
    current.begin_turn()
    return current


def permanent(current, fact, controller):
    return current.create_permanent(fact, controller, summoning_sick=False)


def declare(current, attacker, blocker=None):
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        option
        for option in current.legal_attack_options(0)
        if option.attacker_ids == (attacker.object_id,)
    )
    current.execute_attack_action(attack)
    current.execute_block_action(
        ActionOption(
            ActionKind.DECLARE_BLOCKERS,
            1,
            blocks=() if blocker is None else ((attacker.object_id, blocker.object_id),),
        )
    )


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
            semantics = interpreter.trample_semantic_coverage(card, fragment)
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
    return hashlib.sha256(
        json.dumps(members, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def test_generic_trample_recognition_and_semantic_coverage():
    semantics = CardInterpreter().trample_semantic_coverage(TRAMPLER, "Trample")
    assert semantics is not None
    assert semantics.coverage == SemanticCoverage(True, True, True)
    assert semantics.program.executable
    granted = CardInterpreter().trample_semantic_coverage(
        BEAR, "Target creature gains trample until end of turn."
    )
    assert granted is not None and not granted.coverage.fully_supported
    assert "trample_choice_or_grant_context_not_implemented" in granted.limitations


def test_supported_payload_does_not_hide_other_keywords_or_unsupported_parent():
    interpreter = CardInterpreter()
    compound = interpreter.trample_semantic_coverage(BEAR, "Vigilance, menace, trample, haste")
    assert compound is not None
    assert compound.coverage.payload_executable and compound.coverage.parent_executable
    assert not compound.coverage.followup_executable
    assert not compound.coverage.fully_supported
    assert compound.limitations == ("trample_followup_semantics_not_implemented",)
    attached = interpreter.trample_semantic_coverage(
        BEAR, "Equipped creature gets +1/+1 and has trample."
    )
    assert attached is not None
    assert not attached.coverage.payload_executable
    assert not attached.coverage.parent_executable
    assert "trample_attachment_context_not_implemented" in attached.limitations
    deathtouch = interpreter.trample_semantic_coverage(BEAR, "Deathtouch, trample")
    assert deathtouch is not None and not deathtouch.coverage.payload_executable
    assert "trample_deathtouch_lethal_not_implemented" in deathtouch.limitations


def test_unblocked_trample_is_ordinary_player_combat_damage():
    current = game()
    attacker = permanent(current, TRAMPLER, 0)
    declare(current, attacker)
    evidence = current.resolve_combat_damage()
    assert current.players[1].life == 15
    assert [(item.target_player, item.amount) for item in evidence.assignments] == [(1, 5)]


def test_trample_has_no_effect_while_blocking():
    current = game()
    attacker = permanent(current, BEAR, 0)
    blocker = permanent(current, TRAMPLER, 1)
    declare(current, attacker, blocker)
    evidence = current.resolve_combat_damage()
    blocker_assignment = next(
        item for item in evidence.assignments if item.source_id == blocker.object_id
    )
    assert blocker_assignment.target_id == attacker.object_id
    assert not blocker_assignment.trample
    assert current.players[0].life == 20


@pytest.mark.parametrize(
    ("power", "toughness", "marked", "blocker_damage", "player_damage"),
    [
        (5, 2, 0, 2, 3),
        (5, 5, 0, 5, 0),
        (5, 5, 2, 3, 2),
        (2, 2, 0, 2, 0),
    ],
)
def test_one_blocker_lethal_and_excess_use_effective_characteristics_and_marked_damage(
    power, toughness, marked, blocker_damage, player_damage
):
    current = game()
    fact = CardFact("Renamed Tramper", "", 0, "Creature — Beast", "Trample", power, 5, ("Trample",))
    blocker_fact = CardFact(
        "Renamed Blocker", "", 0, "Creature — Bear", power=1, toughness=toughness
    )
    attacker = permanent(current, fact, 0)
    blocker = permanent(current, blocker_fact, 1)
    blocker.damage = marked
    declare(current, attacker, blocker)
    evidence = current.resolve_combat_damage()
    attacker_assignments = [
        item for item in evidence.assignments if item.source_id == attacker.object_id
    ]
    assert attacker_assignments[0].target_id == blocker.object_id
    assert attacker_assignments[0].amount == blocker_damage
    assert attacker_assignments[0].trample
    assert attacker_assignments[0].lethal_required == max(0, toughness - marked)
    assert (
        sum(item.amount for item in attacker_assignments if item.target_player == 1)
        == player_damage
    )
    assert current.players[1].life == 20 - player_damage
    result = evidence.trample_results[0]
    assert result.attacker_id == attacker.object_id
    assert result.blocker_id == blocker.object_id
    assert result.damage_step is CombatDamageStepKind.REGULAR
    assert result.attacker_power == power
    assert result.blocker_toughness == toughness
    assert result.blocker_marked_damage_before == marked
    assert result.lethal_required == max(0, toughness - marked)
    assert result.blocker_damage_assigned == blocker_damage
    assert result.player_damage_assigned == player_damage
    assert result.defending_life_before == 20
    assert result.defending_life_after == 20 - player_damage
    assert result.blocker_survived == (blocker_damage + marked < toughness)
    assert result.blocker_marked_damage_after == (
        blocker_damage + marked if result.blocker_survived else None
    )


@pytest.mark.parametrize(("printed_power", "modifier"), [(0, 0), (2, -3)])
def test_zero_or_negative_effective_power_creates_no_assignment_or_trample_evidence(
    printed_power, modifier
):
    current = game()
    fact = CardFact(
        "Powerless Tramper",
        "",
        0,
        "Creature — Beast",
        "Trample",
        printed_power,
        3,
        ("Trample",),
    )
    attacker = permanent(current, fact, 0)
    blocker = permanent(current, BEAR, 1)
    if modifier:
        attacker.characteristic_effects.append(
            CharacteristicEffect(
                "negative-power",
                CharacteristicLayer.POWER_TOUGHNESS,
                PowerToughnessSubLayer.MODIFY,
                CharacteristicOperation.ADD,
                modifier,
                0,
            )
        )
    declare(current, attacker, blocker)
    evidence = current.resolve_combat_damage()
    assert all(item.source_id != attacker.object_id for item in evidence.assignments)
    assert evidence.trample_results == ()
    assert blocker.damage == 0
    assert current.players[1].life == 20


def test_changed_power_and_toughness_are_evaluated_at_damage_assignment():
    current = game()
    attacker = permanent(current, TRAMPLER, 0)
    blocker = permanent(
        current, CardFact("Wall", "", 0, "Creature — Wall", power=0, toughness=4), 1
    )
    attacker.characteristic_effects.append(
        CharacteristicEffect(
            "shrink",
            CharacteristicLayer.POWER_TOUGHNESS,
            PowerToughnessSubLayer.MODIFY,
            CharacteristicOperation.ADD,
            -2,
            0,
        )
    )
    blocker.characteristic_effects.append(
        CharacteristicEffect(
            "weaken",
            CharacteristicLayer.POWER_TOUGHNESS,
            PowerToughnessSubLayer.MODIFY,
            CharacteristicOperation.ADD,
            0,
            -2,
        )
    )
    declare(current, attacker, blocker)
    evidence = current.resolve_combat_damage()
    assert [
        item.amount for item in evidence.assignments if item.source_id == attacker.object_id
    ] == [2, 1]


def test_first_strike_trample_uses_first_damage_step_and_existing_sba_boundary():
    current = game()
    attacker = permanent(current, FIRST_TRAMPLER, 0)
    blocker = permanent(current, BEAR, 1)
    declare(current, attacker, blocker)
    first = current.resolve_combat_damage()
    assert first.kind is CombatDamageStepKind.FIRST_STRIKE
    assert [item.amount for item in first.assignments] == [2, 3]
    assert not current.is_authoritative(blocker, "battlefield")
    regular = current.resolve_combat_damage()
    assert regular.assignments == ()
    assert current.players[1].life == 17


def test_double_strike_tramples_over_after_blocker_dies_between_steps():
    current = game()
    attacker = permanent(current, DOUBLE_TRAMPLER, 0)
    blocker = permanent(current, BEAR, 1)
    declare(current, attacker, blocker)
    first = current.resolve_combat_damage()
    assert [item.amount for item in first.assignments] == [2, 3]
    regular = current.resolve_combat_damage()
    assert [(item.target_player, item.amount) for item in regular.assignments] == [(1, 5)]
    assert current.players[1].life == 12
    assert blocker.object_id in first.removed_before_next_step
    first_result = first.trample_results[0]
    assert not first_result.blocker_survived
    assert first_result.blocker_marked_damage_after is None
    second_result = regular.trample_results[0]
    assert second_result.blocker_id == blocker.object_id
    assert second_result.blocker_toughness is None
    assert second_result.blocker_marked_damage_before is None
    assert second_result.lethal_required == 0
    assert second_result.player_damage_assigned == 5
    assert second_result.defending_life_before == 17
    assert second_result.defending_life_after == 12


def test_double_strike_recalculates_lethal_from_surviving_blocker_state():
    current = game()
    attacker = permanent(current, DOUBLE_TRAMPLER, 0)
    blocker = permanent(
        current,
        CardFact("Large Wall", "", 0, "Creature — Wall", power=0, toughness=6),
        1,
    )
    declare(current, attacker, blocker)
    first = current.resolve_combat_damage()
    first_result = first.trample_results[0]
    assert first_result.lethal_required == 6
    assert first_result.blocker_damage_assigned == 5
    assert first_result.blocker_survived
    assert first_result.blocker_marked_damage_after == 5
    regular = current.resolve_combat_damage()
    second_result = regular.trample_results[0]
    assert second_result.blocker_marked_damage_before == 5
    assert second_result.blocker_toughness == 6
    assert second_result.lethal_required == 1
    assert second_result.blocker_damage_assigned == 1
    assert second_result.player_damage_assigned == 4
    assert second_result.defending_life_before == 20
    assert second_result.defending_life_after == 16
    assert not second_result.blocker_survived


def test_trample_attacker_removed_between_steps_cannot_assign_again():
    current = game()
    attacker = permanent(current, DOUBLE_TRAMPLER, 0)
    blocker = permanent(current, FIRST_BLOCKER, 1)
    declare(current, attacker, blocker)
    first = current.resolve_combat_damage()
    assert not current.is_authoritative(attacker, "battlefield")
    assert attacker.object_id in first.removed_before_next_step
    regular = current.resolve_combat_damage()
    assert all(item.source_id != attacker.object_id for item in regular.assignments)


def test_fabricated_attacker_and_blocker_state_is_rejected_atomically():
    current = game()
    attacker = permanent(current, TRAMPLER, 0)
    blocker = permanent(current, BEAR, 1)
    declare(current, attacker, blocker)
    before = (
        current.players[1].life,
        attacker.damage,
        blocker.damage,
        tuple(current.combat_damage_evidence),
    )
    current._combat_attackers = ("fabricated-attacker",)
    with pytest.raises(ValueError, match="fabricated"):
        current.resolve_combat_damage()
    assert (
        current.players[1].life,
        attacker.damage,
        blocker.damage,
        tuple(current.combat_damage_evidence),
    ) == before
    current._combat_attackers = (attacker.object_id,)
    current._combat_blocks = ((attacker.object_id, "fabricated-blocker"),)
    with pytest.raises(ValueError, match="fabricated"):
        current.resolve_combat_damage()
    assert (
        current.players[1].life,
        attacker.damage,
        blocker.damage,
        tuple(current.combat_damage_evidence),
    ) == before


def test_stale_combat_references_do_not_bind_equal_replacement_objects():
    current = game()
    attacker = permanent(current, TRAMPLER, 0)
    blocker = permanent(current, BEAR, 1)
    declare(current, attacker, blocker)
    current.put_into_graveyard(blocker)
    replacement = permanent(current, BEAR, 1)
    evidence = current.resolve_combat_damage()
    assert replacement.object_id != blocker.object_id
    assert replacement.damage == 0
    assert [(item.target_player, item.amount) for item in evidence.assignments] == [(1, 5)]

    other = game()
    stale_attacker = permanent(other, TRAMPLER, 0)
    other_blocker = permanent(other, BEAR, 1)
    declare(other, stale_attacker, other_blocker)
    other.put_into_graveyard(stale_attacker)
    replacement_attacker = permanent(other, TRAMPLER, 0)
    evidence = other.resolve_combat_damage()
    assert replacement_attacker.object_id != stale_attacker.object_id
    assert all(item.source_id != replacement_attacker.object_id for item in evidence.assignments)
    assert other.players[1].life == 20


def test_assignment_evidence_is_immutable_and_survives_combat_state_cleanup():
    current = game()
    attacker = permanent(current, TRAMPLER, 0)
    blocker = permanent(current, BEAR, 1)
    declare(current, attacker, blocker)
    evidence = current.resolve_combat_damage()
    snapshot = tuple(current.combat_damage_evidence)
    assert evidence.assignments[0].target_id == blocker.object_id
    current.advance_to(TurnStep.POSTCOMBAT_MAIN)
    assert current._combat_attackers == () and current._combat_blocks == ()
    assert tuple(current.combat_damage_evidence) == snapshot
    serialized = current.snapshot()["combat_damage"]["evidence"][-1]["trample_results"][0]
    assert serialized == {
        "attacker_id": attacker.object_id,
        "blocker_id": blocker.object_id,
        "damage_step": "regular",
        "attacker_power": 5,
        "blocker_toughness": 2,
        "blocker_marked_damage_before": 0,
        "lethal_required": 2,
        "blocker_damage_assigned": 2,
        "player_damage_assigned": 3,
        "defending_player": 1,
        "defending_life_before": 20,
        "defending_life_after": 17,
        "blocker_marked_damage_after": None,
        "blocker_survived": False,
    }


def test_multiple_blockers_remain_outside_generated_combat_options():
    current = game()
    attacker = permanent(current, TRAMPLER, 0)
    one = permanent(current, BEAR, 1)
    two = permanent(current, BEAR, 1)
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(option for option in current.legal_attack_options(0) if option.attacker_ids)
    current.execute_attack_action(attack)
    fabricated = ActionOption(
        ActionKind.DECLARE_BLOCKERS,
        1,
        blocks=((attacker.object_id, one.object_id), (attacker.object_id, two.object_id)),
    )
    assert fabricated not in current.legal_block_options(attack, 1)
    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_block_action(fabricated)


def test_no_card_name_dispatch_and_existing_unknowns_are_unchanged():
    sources = (
        inspect.getsource(CardInterpreter.trample_semantic_coverage),
        inspect.getsource(Game.evaluated_trample),
        inspect.getsource(Game.resolve_combat_damage),
    )
    assert all("Mutant Town Musicians" not in source for source in sources)
    unknowns = {
        "Arcane Signet",
        "Chromatic Lantern",
        "Command Tower",
        "Double Jump // Flying Kick",
        "Exotic Orchard",
        "Fast Forward",
        "Plague of Vermin",
    }
    assert unknowns.isdisjoint({item[1] for item in coverage_sets()[0]})


def test_authoritative_memberships_and_digests_are_locked():
    recognized, executable, full = coverage_sets()
    assert len({item[0] for item in recognized}) == 25 and len(recognized) == 26
    assert len({item[0] for item in executable}) == 20 and len(executable) == 20
    assert len({item[0] for item in full}) == 15 and len(full) == 15
    assert {item[1] for item in recognized} == RECOGNIZED_NAMES
    assert {item[1] for item in executable} == EXECUTABLE_NAMES
    assert {item[1] for item in full} == FULL_NAMES
    assert digest(recognized) == "1110d74154eec8dd568fd31387db2a2be243dd7d5ad27bd2f2c89206cc29786e"
    assert digest(executable) == "eb31687830676ca3d020256f0226cb0ab4fd7861903dd5f433ae93cf97ff15b5"
    assert digest(full) == "84bb2753b742e60f61e1790af18080b9f5c5bbfaaa786b502554eaa1ac03e67b"


def test_frozen_roster_memberships_and_deck_exposure_are_locked():
    recognized, executable, full = coverage_sets()
    decks = {
        path.parent.name: {
            line.split(" ", 1)[1]
            for line in path.read_text(encoding="utf-8").splitlines()
            if line and line != "Deck"
        }
        for path in ROOT.glob("decks/*/PROTOTYPE_0.1.txt")
    }
    all_names = set().union(*decks.values())
    assert {item[1] for item in recognized} & all_names == {
        "Mutagen Man, Living Ooze",
        "Mutant Town Musicians",
        "Saved by the Shell",
    }
    assert {item[1] for item in executable} & all_names == {
        "Mutagen Man, Living Ooze",
        "Mutant Town Musicians",
    }
    assert {item[1] for item in full} & all_names == {
        "Mutagen Man, Living Ooze",
        "Mutant Town Musicians",
    }
    assert {name for name, cards in decks.items() if cards & RECOGNIZED_NAMES} == {
        "bebop_rocksteady",
        "casey_jones",
        "michelangelo",
        "raphael",
    }
    assert {name for name, cards in decks.items() if cards & EXECUTABLE_NAMES} == {
        "bebop_rocksteady",
        "casey_jones",
        "raphael",
    }
