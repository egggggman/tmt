import pytest

from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    DamageTargetKind,
    DamageTransaction,
    Game,
    TemporaryKeyword,
    TemporaryKeywordEffect,
    TurnStep,
)

LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
DEATHTOUCH = CardFact(
    "Touch of Death", "{1}{B}", 2, "Creature — Mutant", "Deathtouch", 1, 1, ("Deathtouch",)
)
FIRST_DEATHTOUCH = CardFact(
    "First Touch",
    "{1}{B}",
    2,
    "Creature — Mutant",
    "First strike\nDeathtouch",
    1,
    1,
    ("First strike", "Deathtouch"),
)
DOUBLE_DEATHTOUCH = CardFact(
    "Double Touch",
    "{1}{B}",
    2,
    "Creature — Mutant",
    "Double strike\nDeathtouch",
    1,
    1,
    ("Double strike", "Deathtouch"),
)
PLAIN_SOURCE = CardFact("Plain Source", "{1}", 1, "Creature — Bear", power=2, toughness=2)
HIGH_TOUGHNESS = CardFact("Large Bear", "{3}", 3, "Creature — Bear", power=2, toughness=5)
INDESTRUCTIBLE = CardFact(
    "Unbreakable Bear",
    "{3}",
    3,
    "Creature — Bear",
    "Indestructible",
    2,
    5,
    ("Indestructible",),
)


def game(seed=991):
    current = Game(([LAND] * 60, [LAND] * 60), seed=seed)
    current.begin_turn()
    return current


def damage(current, source, target, amount=1, *, defer=True):
    return current.deal_damage(
        DamageTransaction(
            source.controller,
            source,
            DamageTargetKind.CREATURE,
            amount,
            "Source deals damage to target creature.",
            target=target,
        ),
        defer_post_damage=defer,
    )


def declare_blocked_combat(current, attacker, blocker):
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        option
        for option in current.legal_attack_options(attacker.controller)
        if option.attacker_ids == (attacker.object_id,)
    )
    current.execute_attack_action(attack)
    current.execute_block_action(
        ActionOption(
            ActionKind.DECLARE_BLOCKERS,
            blocker.controller,
            blocks=((attacker.object_id, blocker.object_id),),
        )
    )


def test_positive_deathtouch_damage_destroys_higher_toughness_creature():
    current = game()
    source = current.create_permanent(DEATHTOUCH, 0, summoning_sick=False)
    target = current.create_permanent(HIGH_TOUGHNESS, 1, summoning_sick=False)
    before = current.authoritative_state_fingerprint()

    damage(current, source, target)

    assert target.damage == 1
    assert target.damage_from_deathtouch
    assert current.authoritative_state_fingerprint() != before
    assert target.zone == "battlefield"
    current.check_state_based_actions()
    assert target.zone == "former"
    assert not target.damage_from_deathtouch
    assert any(event.get("reason") == "lethal_damage" for event in current.events)


def test_ordinary_damage_below_toughness_does_not_destroy_creature():
    current = game()
    source = current.create_permanent(PLAIN_SOURCE, 0, summoning_sick=False)
    target = current.create_permanent(HIGH_TOUGHNESS, 1, summoning_sick=False)
    damage(current, source, target, amount=4)
    current.check_state_based_actions()
    assert target.damage == 4
    assert not target.damage_from_deathtouch
    assert current.is_authoritative(target, "battlefield")


def test_zero_damage_is_rejected_without_marking_or_mutating_target():
    current = game()
    source = current.create_permanent(DEATHTOUCH, 0, summoning_sick=False)
    target = current.create_permanent(HIGH_TOUGHNESS, 1, summoning_sick=False)
    with pytest.raises(ValueError, match="damage amount must be positive"):
        damage(current, source, target, amount=0)
    assert target.damage == 0
    assert not target.damage_from_deathtouch
    assert current.is_authoritative(target, "battlefield")


def test_fully_prevented_damage_does_not_create_a_damage_transaction():
    """The bounded engine has no prevention replacement; zero actual damage is omitted."""
    current = game()
    source = current.create_permanent(DEATHTOUCH, 0, summoning_sick=False)
    target = current.create_permanent(HIGH_TOUGHNESS, 1, summoning_sick=False)
    # The caller passes the post-prevention amount. A fully prevented event has no damage.
    with pytest.raises(ValueError, match="damage amount must be positive"):
        damage(current, source, target, amount=0)
    current.check_state_based_actions()
    assert target.damage == 0
    assert not target.damage_from_deathtouch
    assert current.is_authoritative(target, "battlefield")


def test_multiple_simultaneous_sources_mark_only_from_deathtouch_source():
    current = game()
    source = current.create_permanent(DEATHTOUCH, 0, summoning_sick=False)
    ordinary = current.create_permanent(PLAIN_SOURCE, 0, summoning_sick=False)
    target = current.create_permanent(HIGH_TOUGHNESS, 1, summoning_sick=False)
    damage(current, ordinary, target, amount=1)
    damage(current, source, target, amount=1)
    assert target.damage == 2
    assert target.damage_from_deathtouch
    current.check_state_based_actions()
    assert target.zone == "former"
    assert not target.damage_from_deathtouch


def test_damage_source_keyword_changes_do_not_rewrite_damage_history():
    current = game()
    source = current.create_permanent(PLAIN_SOURCE, 0, summoning_sick=False)
    target = current.create_permanent(HIGH_TOUGHNESS, 1, summoning_sick=False)
    source.temporary_keyword_effects.append(
        TemporaryKeywordEffect(
            TemporaryKeyword.DEATHTOUCH,
            "until_end_of_turn",
            "synthetic-grant",
            "gains deathtouch until end of turn.",
        )
    )
    damage(current, source, target)
    source.temporary_keyword_effects.clear()
    assert target.damage_from_deathtouch
    current.check_state_based_actions()
    assert target.zone == "former"

    current = game(seed=992)
    source = current.create_permanent(PLAIN_SOURCE, 0, summoning_sick=False)
    target = current.create_permanent(HIGH_TOUGHNESS, 1, summoning_sick=False)
    damage(current, source, target)
    source.temporary_keyword_effects.append(
        TemporaryKeywordEffect(
            TemporaryKeyword.DEATHTOUCH,
            "until_end_of_turn",
            "synthetic-grant",
            "gains deathtouch until end of turn.",
        )
    )
    current.check_state_based_actions()
    assert not target.damage_from_deathtouch
    assert current.is_authoritative(target, "battlefield")


def test_indestructible_still_prevents_deathtouch_state_based_destruction():
    current = game()
    source = current.create_permanent(DEATHTOUCH, 0, summoning_sick=False)
    target = current.create_permanent(HIGH_TOUGHNESS, 1, summoning_sick=False)
    target.temporary_keyword_effects.append(
        TemporaryKeywordEffect(
            TemporaryKeyword.INDESTRUCTIBLE,
            "until_end_of_turn",
            "synthetic-grant",
            "gains indestructible until end of turn.",
        )
    )
    damage(current, source, target)
    current.check_state_based_actions()
    assert target.damage == 1 and not target.damage_from_deathtouch
    assert current.is_authoritative(target, "battlefield")
    target.temporary_keyword_effects.clear()
    current.check_state_based_actions()
    assert current.is_authoritative(target, "battlefield")


def test_cleanup_clears_deathtouch_damage_marker_with_marked_damage():
    current = game()
    source = current.create_permanent(DEATHTOUCH, 0, summoning_sick=False)
    target = current.create_permanent(HIGH_TOUGHNESS, 1, summoning_sick=False)
    damage(current, source, target)
    assert target.damage_from_deathtouch
    current._perform_cleanup()
    assert target.damage == 0
    assert not target.damage_from_deathtouch


@pytest.mark.parametrize("attacker_card", [FIRST_DEATHTOUCH, DOUBLE_DEATHTOUCH])
def test_first_and_double_strike_deathtouch_damage_is_applied_in_existing_steps(attacker_card):
    current = game()
    attacker = current.create_permanent(attacker_card, 0, summoning_sick=False)
    blocker = current.create_permanent(HIGH_TOUGHNESS, 1, summoning_sick=False)
    declare_blocked_combat(current, attacker, blocker)

    first = current.resolve_combat_damage()

    assert first.kind.value == "first_strike"
    assert first.removed_before_next_step == (blocker.object_id,)
    assert blocker.damage == 1
    assert not blocker.damage_from_deathtouch
    assert not current.is_authoritative(blocker, "battlefield")
    regular = current.resolve_combat_damage()
    assert not any(item.source_id == attacker.object_id for item in regular.assignments)


def test_deathtouch_blocker_does_not_change_non_deathtouch_trample_assignment():
    current = game()
    trampler = current.create_permanent(
        CardFact("Trampler", "{3}{G}", 4, "Creature — Beast", "Trample", 4, 4, ("Trample",)),
        0,
        summoning_sick=False,
    )
    blocker = current.create_permanent(DEATHTOUCH, 1, summoning_sick=False)
    declare_blocked_combat(current, trampler, blocker)
    evidence = current.resolve_combat_damage()
    attacker_assignments = [
        item for item in evidence.assignments if item.source_id == trampler.object_id
    ]
    blocker_assignment = next(item for item in attacker_assignments if item.target_id)
    player_assignment = next(
        item for item in attacker_assignments if item.target_player is not None
    )
    assert blocker_assignment.target_id == blocker.object_id
    assert blocker_assignment.amount == blocker.toughness
    assert blocker_assignment.trample
    assert player_assignment.amount == 3
    assert blocker.zone == "former"
    assert trampler.damage == 1
    assert not trampler.damage_from_deathtouch
    assert trampler.zone == "former"
