import pytest

from tmnt_design_studio.engine07 import ActionKind, ActionOption, CardFact, Game, TurnStep

LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
MENACE = CardFact(
    "Menace Beast",
    "{2}",
    2,
    "Creature — Beast",
    "Menace",
    power=5,
    toughness=5,
    keywords=("Menace",),
)
MENACE_POWER_LIMIT = CardFact(
    "Restricted Menace Beast",
    "{2}",
    2,
    "Creature — Beast",
    "Menace\nThis creature can't be blocked by creatures with power 3 or greater.",
    power=5,
    toughness=5,
    keywords=("Menace",),
)
MENACE_SINGLE_BLOCK = CardFact(
    "Conflicted Menace Beast",
    "{2}",
    2,
    "Creature — Beast",
    "Menace\nThis creature can't be blocked by more than one creature.",
    power=5,
    toughness=5,
    keywords=("Menace",),
)
BODY = CardFact("Bear", "{1}", 1, "Creature — Bear", power=2, toughness=2)
POWER_THREE = CardFact("Ogre", "{3}", 3, "Creature — Ogre", power=3, toughness=3)
POWER_FOUR = CardFact("Giant", "{4}", 4, "Creature — Giant", power=4, toughness=4)


def prepare_combat(attacker_facts, blocker_facts):
    game = Game(([LAND] * 20, [LAND] * 20), seed=38101)
    game.begin_turn()
    attackers = [game.create_permanent(card, 0, summoning_sick=False) for card in attacker_facts]
    blockers = [game.create_permanent(card, 1, summoning_sick=False) for card in blocker_facts]
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        option
        for option in game.legal_attack_options(0)
        if option.attacker_ids == tuple(item.object_id for item in attackers)
    )
    game.execute_attack_action(attack)
    return game, attack, attackers, blockers


def record_choice(game, attack, options, selected):
    game.record_block_options_presented(attack, 1, options)
    game.record_block_option_selected(attack, options, selected)
    return next(
        event for event in reversed(game.events) if event["event"] == "block_options_presented"
    )


def selected_event(game):
    return next(
        event for event in reversed(game.events) if event["event"] == "block_option_selected"
    )


def test_one_eligible_blocker_is_not_presented_as_menace_block():
    game, attack, attackers, blockers = prepare_combat([MENACE], [BODY])
    options = game.legal_block_options(attack, 1)
    selected = options[0]
    evidence = record_choice(game, attack, options, selected)

    assert evidence["menace_attacker_ids"] == [attackers[0].object_id]
    assert evidence["untapped_creature_blocker_ids"] == [blockers[0].object_id]
    assert evidence["eligible_blockers_by_attacker"] == {
        attackers[0].object_id: [blockers[0].object_id]
    }
    assert [option["blocks"] for option in evidence["offered_options"]] == [[]]
    assert selected_event(game)["blocks"] == []
    assert selected_event(game)["was_offered"] is True


def test_two_eligible_blockers_present_pair_and_damage_uses_selected_pair():
    game, attack, attackers, blockers = prepare_combat([MENACE], [BODY, BODY])
    options = game.legal_block_options(attack, 1)
    selected = next(option for option in options if len(option.blocks) == 2)
    evidence = record_choice(game, attack, options, selected)

    assert all(len(option["blocks"]) in (0, 2) for option in evidence["offered_options"])
    assert selected_event(game)["blocks"] == [list(pair) for pair in selected.blocks]
    assert selected_event(game)["was_offered"] is True
    game.execute_block_action(selected)
    damage = game.resolve_combat_damage()
    assert {
        item.target_id for item in damage.assignments if item.source_id == attackers[0].object_id
    } == {blocker.object_id for blocker in blockers}
    declared = next(event for event in game.events if event["event"] == "blockers_declared")
    assert declared["blocks"] == [list(pair) for pair in selected.blocks]


def test_three_eligible_blockers_offer_only_menace_legal_groups():
    game, attack, attackers, _blockers = prepare_combat([MENACE], [BODY, BODY, BODY])
    options = game.legal_block_options(attack, 1)
    evidence = record_choice(game, attack, options, options[0])

    groups = [option["blocks"] for option in evidence["offered_options"]]
    assert all(len(group) == 0 or len(group) >= 2 for group in groups)
    assert {len(group) for group in groups} == {0, 2, 3}
    assert evidence["menace_attacker_ids"] == [attackers[0].object_id]


def test_multiple_menace_attackers_never_reuse_blockers_or_offer_single_blocks():
    game, attack, attackers, _blockers = prepare_combat([MENACE, MENACE], [BODY] * 3)
    options = game.legal_block_options(attack, 1)
    evidence = record_choice(game, attack, options, options[0])

    assert evidence["menace_attacker_ids"] == [item.object_id for item in attackers]
    for option in evidence["offered_options"]:
        by_attacker = {}
        blocker_ids = []
        for attacker_id, blocker_id in option["blocks"]:
            by_attacker.setdefault(attacker_id, []).append(blocker_id)
            blocker_ids.append(blocker_id)
        assert len(blocker_ids) == len(set(blocker_ids))
        assert all(len(group) in (0, 2, 3) for group in by_attacker.values())


def test_supported_power_restriction_filters_menace_blocker_candidates():
    game, attack, attackers, blockers = prepare_combat(
        [MENACE_POWER_LIMIT], [BODY, POWER_THREE, POWER_FOUR]
    )
    options = game.legal_block_options(attack, 1)
    evidence = record_choice(game, attack, options, options[0])

    assert evidence["eligible_blockers_by_attacker"] == {
        attackers[0].object_id: [blockers[0].object_id]
    }
    assert [option["blocks"] for option in evidence["offered_options"]] == [[]]


def test_menace_and_single_block_restriction_have_no_legal_block_opportunity():
    game, attack, attackers, blockers = prepare_combat([MENACE_SINGLE_BLOCK], [BODY, BODY, BODY])
    options = game.legal_block_options(attack, 1)
    evidence = record_choice(game, attack, options, options[0])

    assert evidence["eligible_blockers_by_attacker"] == {
        attackers[0].object_id: [blocker.object_id for blocker in blockers]
    }
    assert [option["blocks"] for option in evidence["offered_options"]] == [[]]


def test_selection_not_in_offered_options_is_recorded_as_unoffered():
    game, attack, _attackers, _blockers = prepare_combat([MENACE], [BODY])
    options = game.legal_block_options(attack, 1)
    fabricated = ActionOption(
        ActionKind.DECLARE_BLOCKERS,
        1,
        blocks=((attack.attacker_ids[0], "not-a-blocker"),),
    )
    record_choice(game, attack, options, fabricated)

    assert selected_event(game)["was_offered"] is False


def test_execute_rejects_fabricated_single_block_against_menace():
    game, attack, _attackers, blockers = prepare_combat([MENACE], [BODY, BODY])
    options = game.legal_block_options(attack, 1)
    illegal = ActionOption(
        ActionKind.DECLARE_BLOCKERS,
        1,
        blocks=((attack.attacker_ids[0], blockers[0].object_id),),
    )
    record_choice(game, attack, options, illegal)

    assert selected_event(game)["was_offered"] is False
    with pytest.raises(ValueError, match="not currently legal"):
        game.execute_block_action(illegal)


def test_ordinary_combat_keeps_existing_block_assignment_telemetry_only():
    game, attack, _attackers, _blockers = prepare_combat([BODY], [BODY])
    options = game.legal_block_options(attack, 1)
    selected = options[0]
    game.record_block_options_presented(attack, 1, options)
    game.record_block_option_selected(attack, options, selected)
    game.execute_block_action(selected)

    assert not any(
        event["event"] in {"block_options_presented", "block_option_selected"}
        for event in game.events
    )
    assert any(event["event"] == "blockers_declared" for event in game.events)
