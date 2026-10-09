"""Generic Equipment characteristics follow the current legal attachment."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, StrikeKeyword
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, load_facts

LAND = CardFact("Mountain", "", 0, "Basic Land — Mountain")
BEAR = CardFact("Runner", "{R}", 1, "Creature", power=2, toughness=2)
EQUIPMENT = CardFact(
    "Speed Boots",
    "{1}",
    1,
    "Artifact — Equipment",
    "Equipped creature gets +1/+0 and has haste.\n"
    "Equip {1} ({1}: Attach to target creature you control. Equip only as a sorcery.)",
)


def setup(card=EQUIPMENT):
    game = Game(([LAND] * 35, [LAND] * 35), seed=291)
    game.begin_turn()
    for _ in range(4):
        game.create_permanent(LAND, 0, summoning_sick=False)
    first = game.create_permanent(BEAR, 0)
    second = game.create_permanent(BEAR, 0)
    game.set_hand_for_testing(0, [card])
    option = next(o for o in game.legal_main_actions(0) if o.kind is ActionKind.CAST)
    game.execute_main_action(option)
    equipment = next(p for p in game.players[0].battlefield if p.card is card)
    return game, equipment, first, second


def equip(game, equipment, creature):
    option = next(
        o
        for o in game.legal_main_actions(0)
        if o.kind is ActionKind.ACTIVATE_ABILITY
        and o.object_id == equipment.object_id
        and o.target_id == creature.object_id
    )
    game.execute_main_action(option)
    while game.priority_state:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def test_renamed_equipment_grants_and_moves_haste_and_power():
    game, equipment, first, second = setup()
    assert first.power == second.power == 2
    assert not game.legal_attackers(0)
    equip(game, equipment, first)
    assert first.power == 3 and first.toughness == 2
    assert first in game.legal_attackers(0) and second not in game.legal_attackers(0)
    equip(game, equipment, second)
    assert first.power == 2 and second.power == 3
    assert first not in game.legal_attackers(0) and second in game.legal_attackers(0)
    game.put_into_graveyard(second)
    assert equipment.attached_to is None
    assert first.power == 2
    game.check_invariants()


def test_other_grammar_keywords_apply_to_combat_and_recalculate():
    variants = (
        ("vigilance", "Equipped creature gets +2/+1 and has vigilance."),
        ("trample", "Equipped creature gets +1/+1 and has trample."),
        ("double strike", "Equipped creature has double strike."),
    )
    for keyword, clause in variants:
        card = replace(
            EQUIPMENT,
            name="Gear " + keyword,
            oracle_text=clause + "\n" + EQUIPMENT.oracle_text.splitlines()[-1],
        )
        game, equipment, creature, _other = setup(card)
        assert CardInterpreter().equipment_static_semantics(card, clause)
        equip(game, equipment, creature)
        if keyword == "vigilance":
            assert (creature.power, creature.toughness) == (4, 3)
            assert game._has_keyword(creature, "Vigilance")
        elif keyword == "trample":
            assert (creature.power, creature.toughness) == (3, 3)
            assert game.evaluated_trample(creature)
        else:
            assert StrikeKeyword.DOUBLE_STRIKE in game.evaluated_strike_keywords(creature)
        game.move_object(equipment, "graveyard", reason="test_departure")
        assert (creature.power, creature.toughness) == (2, 2)
        assert not game._has_keyword(creature, keyword)
        game.check_invariants()


def test_equipment_granted_haste_obeys_aura_ability_loss_timestamp():
    root = Path(__file__).resolve().parents[1]
    catalog = load_card_data(
        root / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        root / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    aura_card = load_facts(catalog, {"Retro-Mutation"})["Retro-Mutation"]
    game, equipment, creature, _other = setup()
    equip(game, equipment, creature)
    assert game._has_keyword(creature, "Haste")
    aura = game.create_permanent(aura_card, 1)
    game.attach_aura(aura, creature)
    assert (creature.power, creature.toughness) == (1, 1)
    assert not game._has_keyword(creature, "Haste")
    game.move_object(aura, "graveyard", reason="test_aura_removed")
    assert game._has_keyword(creature, "Haste")
    game.check_invariants()
