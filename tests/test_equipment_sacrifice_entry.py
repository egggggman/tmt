"""Generic Equipment entry triggers and alternative sacrifice equip costs."""

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TurnStep

LAND = CardFact("Plain", "", 0, "Basic Land — Plains")
CREATURE = CardFact("Volunteer", "{1}", 1, "Creature", power=2, toughness=2)
ARTIFACT = CardFact("Relic", "{1}", 1, "Artifact")
EQUIPMENT = CardFact(
    "Generic Plating",
    "{1}{B}",
    2,
    "Artifact — Equipment",
    "Equipped creature gets +2/+1.\n"
    "When this Equipment enters, attach it to target creature you control.\n"
    "Equip—Sacrifice another nonland permanent. Activate only once each turn.",
)
ENTRY = "When this Equipment enters, attach it to target creature you control."
EQUIP = "Equip—Sacrifice another nonland permanent. Activate only once each turn."


def setup():
    game = Game(([LAND] * 35, [LAND] * 35), seed=306)
    game.begin_turn()
    first = game.create_permanent(CREATURE, 0)
    second = game.create_permanent(CREATURE, 0)
    cost = game.create_permanent(ARTIFACT, 0)
    equipment = game.create_permanent(EQUIPMENT, 0)
    return game, equipment, first, second, cost


def drain(game):
    while game.priority_state:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def test_oracle_shapes_are_generic_and_non_equipment_does_not_qualify():
    interpreter = CardInterpreter()
    assert interpreter.equipment_etb_attach(EQUIPMENT, ENTRY)
    assert interpreter.activated_ability_semantics(EQUIPMENT, EQUIP).coverage.fully_supported
    altered = CardFact("Relic", "{1}", 1, "Artifact", ENTRY + "\n" + EQUIP)
    assert not interpreter.equipment_etb_attach(altered, ENTRY)
    assert not interpreter.activated_ability_semantics(altered, EQUIP).coverage.fully_supported


def test_entry_target_resolution_and_source_or_target_departure():
    game, equipment, first, second, _cost = setup()
    game._process_creature_entered_triggers(equipment)
    assert game.stack[-1].target_id == first.object_id
    assert first.power == 2
    drain(game)
    assert equipment.attached_to == first.object_id
    assert (first.power, first.toughness) == (4, 3)
    game.move_object(first, "graveyard", reason="test_departure")
    game.check_state_based_actions()
    assert equipment.attached_to is None
    game._process_creature_entered_triggers(equipment)
    assert game.stack[-1].target_id == second.object_id
    game.move_object(equipment, "graveyard", reason="test_response")
    drain(game)
    assert second.power == 2
    assert not next(
        event["attached"]
        for event in reversed(game.events)
        if event["event"] == "equipment_entry_attach_resolved"
    )
    game.check_invariants()


def test_entry_target_departure_and_no_legal_target_do_not_attach():
    game, equipment, first, second, _cost = setup()
    game._process_creature_entered_triggers(equipment)
    game.move_object(first, "graveyard", reason="test_response")
    drain(game)
    assert equipment.attached_to is None
    game.move_object(second, "graveyard", reason="test_departure")
    game._process_creature_entered_triggers(equipment)
    assert not game.stack
    assert any(event["event"] == "equipment_entry_no_legal_target" for event in game.events)
    game.check_invariants()


def test_sacrifice_payment_source_change_and_land_or_enemy_rejected():
    game, equipment, first, second, cost = setup()
    land = game.create_permanent(LAND, 0)
    enemy = game.create_permanent(ARTIFACT, 1)
    for illegal in (land, enemy, equipment):
        assert (
            game.announce_activated_ability(
                0,
                equipment,
                EQUIP,
                target_ids=(second.object_id,),
                other_sacrifice_id=illegal.object_id,
            )
            is None
        )
        assert illegal.zone == "battlefield"
    assert (
        game.announce_activated_ability(
            0,
            equipment,
            EQUIP,
            target_ids=(second.object_id,),
            other_sacrifice_id=cost.object_id,
        )
        is not None
    )
    assert cost.zone == "former"
    game.move_object(equipment, "graveyard", reason="test_response")
    drain(game)
    assert second.power == 2
    assert any(event["event"] == "equipment_attach_failed_closed" for event in game.events)
    assert first.zone == "battlefield"
    game.check_invariants()


def test_alternative_cost_choice_once_per_turn_timing_and_replay():
    def scenario():
        game, equipment, first, second, cost = setup()
        options = [
            option
            for option in game.legal_main_actions(0)
            if option.kind is ActionKind.ACTIVATE_ABILITY
            and option.object_id == equipment.object_id
            and option.oracle_fragment == EQUIP
            and option.target_id == second.object_id
        ]
        assert {option.cost_object_id for option in options} == {
            first.object_id,
            second.object_id,
            cost.object_id,
        }
        assert (
            game.announce_activated_ability(
                0,
                equipment,
                EQUIP,
                target_ids=(second.object_id,),
                other_sacrifice_id=equipment.object_id,
            )
            is None
        )
        assert (
            game.announce_activated_ability(
                0,
                equipment,
                EQUIP,
                target_ids=(second.object_id,),
                other_sacrifice_id=game.players[0].library[0].object_id,
            )
            is None
        )
        assert game.execute_main_action(
            next(option for option in options if option.cost_object_id == cost.object_id)
        )
        assert cost.zone == "former"
        assert equipment.attached_to is None
        assert not any(
            option.object_id == equipment.object_id and option.oracle_fragment == EQUIP
            for option in game.legal_main_actions(0)
        )
        drain(game)
        assert equipment.attached_to == second.object_id
        assert (second.power, second.toughness) == (4, 3)
        assert (
            game.announce_activated_ability(
                0,
                equipment,
                EQUIP,
                target_ids=(first.object_id,),
                other_sacrifice_id=first.object_id,
            )
            is None
        )
        game._step = TurnStep.DECLARE_ATTACKERS
        assert (
            game.announce_activated_ability(
                0,
                equipment,
                EQUIP,
                target_ids=(first.object_id,),
                other_sacrifice_id=first.object_id,
            )
            is None
        )
        game._step = TurnStep.POSTCOMBAT_MAIN
        game._turn += 1
        assert (
            game.announce_activated_ability(
                0,
                equipment,
                EQUIP,
                target_ids=(first.object_id,),
                other_sacrifice_id=first.object_id,
            )
            is not None
        )
        assert first.zone == "former"
        drain(game)
        assert equipment.attached_to == second.object_id  # failed retarget leaves old attachment
        game.check_invariants()
        return game.snapshot(), game.events

    assert scenario() == scenario()
