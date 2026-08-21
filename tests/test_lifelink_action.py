import hashlib
import inspect
import json
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, DamageTargetKind
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    CombatDamageStepKind,
    DamageTransaction,
    Game,
    TurnStep,
)
from tmnt_design_studio.semantic_coverage import SemanticCoverage

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
LIFELINKER = CardFact(
    "Generic Lifeline",
    "{1}{W}",
    2,
    "Creature — Cleric",
    "Lifelink",
    3,
    3,
    ("Lifelink",),
)
DOUBLE_LIFELINKER = CardFact(
    "Generic Double Lifeline",
    "{2}{W}",
    3,
    "Creature — Cleric",
    "Double strike\nLifelink",
    3,
    3,
    ("Double strike", "Lifelink"),
)
TRAMPLE_LIFELINKER = CardFact(
    "Generic Trampling Lifeline",
    "{3}{W}",
    4,
    "Creature — Beast",
    "Trample\nLifelink",
    5,
    5,
    ("Trample", "Lifelink"),
)
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
CUTTING_EDGE = CardFact(
    "Leonardo, Cutting Edge",
    "{1}{W}",
    2,
    "Legendary Creature — Turtle Ninja",
    "Lifelink\nWhenever you gain life, put a +1/+1 counter on Leonardo, Cutting Edge.",
    1,
    1,
    ("Lifelink", "Sneak"),
)
RECOGNIZED_NAMES = {
    "Foot Mystic",
    "Hidden Hideout",
    "Leonardo, Cutting Edge",
    "Leonardo, the Balance",
    "Shadowspear",
    "The Last Ronin",
}
EXECUTABLE_NAMES = {"Foot Mystic", "Leonardo, Cutting Edge"}


def game(seed=808):
    current = Game(([LAND] * 60, [LAND] * 60), seed=seed)
    current.begin_turn()
    return current


def permanent(current, fact, controller, *, owner=None):
    result = current.create_permanent(
        fact, controller if owner is None else owner, summoning_sick=False
    )
    if controller != result.controller:
        current.change_controller(result, controller)
    return result


def declare(current, attackers, blocks=()):
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    option = next(
        item
        for item in current.legal_attack_options(0)
        if item.attacker_ids == tuple(attacker.object_id for attacker in attackers)
    )
    current.execute_attack_action(option)
    current.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1, blocks=blocks))


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
            semantics = interpreter.lifelink_semantic_coverage(card, fragment)
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


def test_generic_recognition_and_semantic_boundaries():
    interpreter = CardInterpreter()
    intrinsic = interpreter.lifelink_semantic_coverage(LIFELINKER, "Lifelink")
    assert intrinsic is not None
    assert intrinsic.coverage == SemanticCoverage(True, True, True)
    assert intrinsic.program.executable

    cases = {
        "{2}, {T}: Target creature gains lifelink until end of turn.": (
            "lifelink_activation_context_not_implemented",
            "lifelink_compound_semantics_not_implemented",
        ),
        "Equipped creature has lifelink.": (
            "lifelink_attachment_context_not_implemented",
            "lifelink_compound_semantics_not_implemented",
        ),
        "Whenever this creature attacks, it gains lifelink until end of turn.": (
            "lifelink_trigger_context_not_implemented",
            "lifelink_compound_semantics_not_implemented",
        ),
        "Creatures you control gain lifelink until end of turn.": (
            "lifelink_grant_context_not_implemented",
            "lifelink_compound_semantics_not_implemented",
        ),
    }
    for fragment, limitations in cases.items():
        semantics = interpreter.lifelink_semantic_coverage(BEAR, fragment)
        assert semantics is not None
        assert not semantics.coverage.payload_executable
        assert not semantics.coverage.parent_executable
        assert not semantics.coverage.fully_supported
        assert semantics.limitations == limitations


def test_unblocked_and_blocked_combat_gain_life_from_damage_actually_dealt():
    unblocked = game()
    attacker = permanent(unblocked, LIFELINKER, 0)
    declare(unblocked, (attacker,))
    unblocked.resolve_combat_damage()
    assert (unblocked.players[0].life, unblocked.players[1].life) == (23, 17)
    assert [(item.source_id, item.amount) for item in unblocked.lifelink_evidence] == [
        (attacker.object_id, 3)
    ]

    blocked = game()
    attacker = permanent(blocked, LIFELINKER, 0)
    blocker = permanent(blocked, BEAR, 1)
    declare(blocked, (attacker,), ((attacker.object_id, blocker.object_id),))
    blocked.resolve_combat_damage()
    assert blocked.players[0].life == 23
    assert blocked.lifelink_evidence[0].target_ids == (blocker.object_id,)
    assert blocked.lifelink_evidence[0].target_players == ()


def test_zero_and_negative_power_produce_no_lifelink_event():
    for power_delta in (-3, -5):
        current = game()
        attacker = permanent(current, LIFELINKER, 0)
        current.apply_pt_modifier(
            attacker,
            power_delta,
            0,
            duration="until_end_of_turn",
            source_card="Test",
            oracle_fragment="Test",
        )
        declare(current, (attacker,))
        evidence = current.resolve_combat_damage()
        assert evidence.assignments == ()
        assert current.players[0].life == 20
        assert current.lifelink_evidence == []


def test_controller_not_owner_gains_life_and_evidence_is_immutable():
    current = game()
    attacker = permanent(current, LIFELINKER, 0, owner=1)
    declare(current, (attacker,))
    current.resolve_combat_damage()
    evidence = current.lifelink_evidence[0]
    assert attacker.owner == 1 and attacker.controller == 0
    assert current.players[0].life == 23 and current.players[1].life == 17
    assert (evidence.controller, evidence.life_before, evidence.life_after) == (0, 20, 23)
    current.move_object(attacker, "graveyard", reason="test")
    assert evidence.source_id != current.players[1].graveyard[-1].object_id
    assert (evidence.life_before, evidence.life_after) == (20, 23)


def test_lethal_simultaneous_combat_preserves_lifelink_before_sbas():
    current = game()
    attacker = permanent(current, LIFELINKER, 0)
    blocker = permanent(current, LIFELINKER, 1)
    declare(current, (attacker,), ((attacker.object_id, blocker.object_id),))
    current.resolve_combat_damage()
    assert current.players[0].life == 23 and current.players[1].life == 23
    assert len(current.lifelink_evidence) == 2
    assert attacker.zone == "former" and blocker.zone == "former"
    assert {item.source_id for item in current.lifelink_evidence} == {
        attacker.object_id,
        blocker.object_id,
    }


def test_double_strike_creates_separate_life_gain_per_damage_step():
    current = game()
    attacker = permanent(current, DOUBLE_LIFELINKER, 0)
    declare(current, (attacker,))
    first = current.resolve_combat_damage()
    second = current.resolve_combat_damage()
    assert first.kind is CombatDamageStepKind.FIRST_STRIKE
    assert second.kind is CombatDamageStepKind.REGULAR
    assert current.players[0].life == 26 and current.players[1].life == 14
    assert [item.damage_step for item in current.lifelink_evidence] == [
        CombatDamageStepKind.FIRST_STRIKE,
        CombatDamageStepKind.REGULAR,
    ]


def test_multiple_lifelink_sources_create_separate_life_gain_events():
    current = game()
    first = permanent(current, LIFELINKER, 0)
    second = permanent(current, LIFELINKER, 0)
    declare(current, (first, second))
    current.resolve_combat_damage()
    assert current.players[0].life == 26 and current.players[1].life == 14
    assert [(item.source_id, item.amount) for item in current.lifelink_evidence] == [
        (first.object_id, 3),
        (second.object_id, 3),
    ]
    assert len({item.event_id for item in current.lifelink_evidence}) == 2


def test_trample_split_is_one_source_life_gain_for_total_damage():
    current = game()
    attacker = permanent(current, TRAMPLE_LIFELINKER, 0)
    blocker = permanent(current, BEAR, 1)
    blocker.damage = 1
    declare(current, (attacker,), ((attacker.object_id, blocker.object_id),))
    current.resolve_combat_damage()
    evidence = current.lifelink_evidence[0]
    assert evidence.amount == 5
    assert evidence.target_ids == (blocker.object_id,)
    assert evidence.target_players == (1,)
    assert (current.players[0].life, current.players[1].life) == (25, 16)


def test_noncombat_damage_reuses_transaction_and_lifelink_result():
    current = game()
    source = permanent(current, LIFELINKER, 0)
    current.deal_damage(
        DamageTransaction(
            0,
            source,
            DamageTargetKind.PLAYER,
            2,
            "Generic Lifeline deals 2 damage to target opponent.",
            target_player=1,
        )
    )
    assert (current.players[0].life, current.players[1].life) == (22, 18)
    assert len(current.lifelink_evidence) == 1
    assert not current.lifelink_evidence[0].combat


def test_fabricated_and_stale_sources_cannot_gain_life():
    current = game()
    source = permanent(current, LIFELINKER, 0)
    fabricated = type(source)(
        source.object_id,
        source.card,
        source.owner,
        source.controller,
        summoning_sick=False,
    )
    assert not current.evaluated_lifelink(fabricated)
    with pytest.raises(ValueError, match="source is not authoritative"):
        current.deal_damage(
            DamageTransaction(
                0,
                fabricated,
                DamageTargetKind.PLAYER,
                2,
                "damage",
                target_player=1,
            )
        )
    current.move_object(source, "graveyard", reason="test")
    assert not current.evaluated_lifelink(source)
    assert current.players[0].life == 20


def test_fabricated_damage_controller_cannot_redirect_lifelink_gain():
    current = game()
    source = permanent(current, LIFELINKER, 0)
    before = tuple(player.life for player in current.players)
    with pytest.raises(ValueError, match="does not control"):
        current.deal_damage(
            DamageTransaction(
                1,
                source,
                DamageTargetKind.PLAYER,
                2,
                "damage",
                target_player=1,
            )
        )
    assert tuple(player.life for player in current.players) == before
    assert current.lifelink_evidence == []


def test_life_gain_trigger_is_detected_before_sba_and_delivered_after_damage():
    current = game()
    attacker = permanent(current, CUTTING_EDGE, 0)
    declare(current, (attacker,))
    current.resolve_combat_damage()
    replacement = next(
        item for item in current.players[0].battlefield if item.object_id == attacker.object_id
    )
    assert replacement.counters == {"+1/+1": 1}
    assert current.players[0].life == 21
    lifelink_index = next(
        index for index, event in enumerate(current.events) if event["event"] == "lifelink_result"
    )
    counter_index = next(
        index for index, event in enumerate(current.events) if event["event"] == "counters_placed"
    )
    assert lifelink_index < counter_index


def test_snapshot_serializes_deterministic_immutable_evidence():
    snapshots = []
    for _ in range(2):
        current = game(812)
        attacker = permanent(current, LIFELINKER, 0)
        declare(current, (attacker,))
        current.resolve_combat_damage()
        snapshots.append(json.dumps(current.snapshot(), sort_keys=True))
    assert snapshots[0] == snapshots[1]
    row = json.loads(snapshots[0])["lifelink"][0]
    assert row["amount"] == 3
    assert row["life_before"] == 20 and row["life_after"] == 23


def test_authoritative_memberships_and_digests_are_locked():
    recognized, executable, full = coverage_sets()
    assert len(recognized) == len({item[0] for item in recognized}) == 6
    assert len(executable) == len({item[0] for item in executable}) == 2
    assert len(full) == len({item[0] for item in full}) == 2
    assert {item[1] for item in recognized} == RECOGNIZED_NAMES
    assert {item[1] for item in executable} == EXECUTABLE_NAMES
    assert {item[1] for item in full} == EXECUTABLE_NAMES
    assert digest(recognized) == "315914585ff72e84306d6e16fba01646ae382c96330f20e6ddf540efbec02761"
    assert digest(executable) == "e1645c8d6fbcd411ecbd507968b89bdc7293567531aee5e833cf83ab38c80e53"
    assert digest(full) == "e1645c8d6fbcd411ecbd507968b89bdc7293567531aee5e833cf83ab38c80e53"


def test_frozen_roster_membership_and_deck_exposure_are_locked():
    recognized, executable, full = coverage_sets()
    decks = {
        path.parent.name: {
            line.split(" ", 1)[1]
            for line in path.read_text(encoding="utf-8").splitlines()
            if line and line != "Deck"
        }
        for path in ROOT.glob("decks/*/PROTOTYPE_0.1.txt")
    }
    frozen = set().union(*decks.values())
    assert {item[1] for item in recognized} & frozen == EXECUTABLE_NAMES
    assert {item[1] for item in executable} & frozen == EXECUTABLE_NAMES
    assert {item[1] for item in full} & frozen == EXECUTABLE_NAMES
    assert {name for name, cards in decks.items() if cards & EXECUTABLE_NAMES} == {
        "leonardo",
        "shredder",
        "splinter",
    }


def test_unknowns_unchanged_and_no_card_name_dispatch():
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
    source = "\n".join(
        (
            inspect.getsource(CardInterpreter.lifelink_semantic_coverage),
            inspect.getsource(Game.evaluated_lifelink),
            inspect.getsource(Game._apply_lifelink_result),
        )
    )
    assert RECOGNIZED_NAMES.isdisjoint(source)
