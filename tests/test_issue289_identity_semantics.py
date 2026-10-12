"""Generic Oracle patterns exercised with frozen identity cards and renamed fixtures."""

import pytest

from tmnt_design_studio.engine07 import ActionKind, ActionOption, CardFact, Game, TurnStep

LAND = CardFact("Mountain", "", 0, "Basic Land")
BEAR = CardFact("Grizzly Bears", "{1}{G}", 2, "Creature", "", 2, 2)
BEPOP = CardFact(
    "Bebop & Rocksteady",
    "{3}{R}",
    4,
    "Creature",
    "Whenever Bebop & Rocksteady attack or block, sacrifice a permanent unless you discard a card.",
    4,
    4,
)
APRIL = CardFact(
    "April O'Neil, Hacktivist",
    "{2}{U}",
    3,
    "Creature",
    "At the beginning of your end step, draw a card for each card type among "
    "spells you've cast this turn.",
    2,
    2,
)
RAPHAEL = CardFact(
    "Raphael, Most Attitude",
    "{3}{R}",
    4,
    "Creature",
    "Alliance — Whenever another creature you control enters, you may exile "
    "the top card of your library.\n"
    "Whenever Raphael attacks, until end of turn, you may play a card exiled with Raphael.",
    4,
    3,
)
MUST_BLOCK = CardFact("Provoker", "", 0, "Creature", "Provoker must be blocked if able.", 2, 2)


def drain(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def setup(*, seed=1):
    game = Game(([LAND] * 28, [LAND] * 28), seed=seed)
    game.begin_turn()
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    return game


@pytest.mark.parametrize("discard", [True, False])
def test_attack_consequence_is_mandatory_but_attacking_is_optional(discard):
    game = setup()
    source = game.create_permanent(BEPOP, 0, summoning_sick=False)
    assert any(not option.attacker_ids for option in game.legal_attack_options(0))
    if not discard:
        for card in tuple(game.players[0].hand):
            game.move_object(card, "graveyard", reason="fixture_discard")
        game.discard_or_sacrifice_chooser = lambda _p, _s, _d, permanents: (
            "sacrifice",
            permanents[0],
        )
    else:
        game.discard_or_sacrifice_chooser = lambda _p, _s, discards, _sacs: ("discard", discards[0])
    game.execute_attack_action(game.legal_attack_options(0)[1])
    assert game.step is TurnStep.DECLARE_ATTACKERS
    trigger = game.stack[-1]
    if discard:
        game.put_into_graveyard(source, state_based_action="independent_removal")
    drain(game)
    resolved = [e for e in game.events if e["event"] == "combat_discard_or_sacrifice_resolved"]
    assert len(resolved) == 1 and resolved[0]["choice"] == ("discard" if discard else "sacrifice")
    assert resolved[0]["event_id"] == trigger.event.event_id
    game.check_invariants()


def test_block_declaration_triggers_before_damage_and_legality_is_rechecked():
    game = setup()
    game.create_permanent(BEAR, 0, summoning_sick=False)
    blocker = game.create_permanent(BEPOP, 1)
    attack = game.legal_attack_options(0)[1]
    game.execute_attack_action(attack)
    option = next(o for o in game.legal_block_options(attack, 1) if o.blocks)
    game.execute_block_action(option)
    assert game.step is TurnStep.DECLARE_BLOCKERS
    assert game.stack[-1].event.subject_ids == (blocker.object_id,)
    with pytest.raises(ValueError):
        game.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))
    drain(game)
    assert game.step is TurnStep.DECLARE_BLOCKERS
    assert any(e["event"] == "combat_discard_or_sacrifice_resolved" for e in game.events)
    game.execute_sneak_action(ActionOption(ActionKind.PASS, 0))
    assert game.step is TurnStep.COMBAT_DAMAGE


def test_must_block_if_able_filters_legal_declarations():
    game = setup()
    source = game.create_permanent(MUST_BLOCK, 0, summoning_sick=False)
    blocker = game.create_permanent(BEAR, 1)
    attack = game.legal_attack_options(0)[1]
    game.execute_attack_action(attack)
    options = game.legal_block_options(attack, 1)
    assert options and all(o.blocks == ((source.object_id, blocker.object_id),) for o in options)
    with pytest.raises(ValueError):
        game.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))


def test_linked_permission_survives_source_removal_and_expires():
    game = setup()
    source = game.create_permanent(RAPHAEL, 0, summoning_sick=False)
    entering = game.create_permanent(BEAR, 0)
    game._process_creature_entered_triggers(entering)
    drain(game)
    exiled_id = game._raphael_linked_exile[source.object_id][0][0]
    exiled = game._objects[exiled_id]
    game.resolve_attack_pt_effects([source])
    game.put_into_graveyard(source, state_based_action="independent_removal")
    drain(game)
    assert game._raphael_permission_for(0, exiled) == source.object_id
    assert game._raphael_permission_for(1, exiled) is None
    game._turn += 1
    assert game._raphael_permission_for(0, exiled) is None


def test_end_step_type_count_snapshots_cast_history_and_source_removal():
    game = Game(([LAND] * 25, [LAND] * 25), seed=4)
    game.begin_turn()
    source = game.create_permanent(APRIL, 0)
    game.log("spell_cast", player_index=0, card_types=("Creature", "Artifact"))
    game.log("spell_cast", player_index=0, card_types=("Creature",))
    game.log("spell_cast", player_index=1, card_types=("Sorcery",))
    game.advance_to(TurnStep.COMBAT_DAMAGE)
    game.resolve_combat_damage()
    game.advance_to(TurnStep.END_STEP)
    trigger = game.stack[-1]
    assert trigger.event.step == TurnStep.END_STEP.value
    game.put_into_graveyard(source, state_based_action="independent_removal")
    before = len(game.players[0].hand)
    drain(game)
    assert len(game.players[0].hand) == before + 2
    assert any(
        e["event"] == "end_step_spell_types_draw_resolved"
        and e["card_types"] == ["Artifact", "Creature"]
        for e in game.events
    )
    game.check_invariants()
