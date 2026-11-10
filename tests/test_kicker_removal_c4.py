"""C4: generic kicker costs and conditional temporary removal."""

from dataclasses import replace

from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import CardFact, Game

STOMP = CardFact(
    "Stomped by the Foot",
    "{1}{B}",
    2,
    "Instant",
    "Kicker—Sacrifice an artifact or creature. (You may sacrifice an artifact or creature "
    "in addition to any other costs as you cast this spell.)\n"
    "Target creature gets -2/-2 until end of turn. If this spell was kicked, that creature "
    "gets -5/-5 until end of turn instead.",
)
SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
BEAR = CardFact("Bear", "{2}", 2, "Creature — Bear", power=3, toughness=3)
RELIC = CardFact("Relic", "{1}", 1, "Artifact")


def ready(seed: int = 4004) -> Game:
    game = Game(([SWAMP] * 20, [SWAMP] * 20), seed=seed)
    game.begin_turn()
    game.create_permanent(SWAMP, 0)
    game.create_permanent(SWAMP, 0)
    return game


def test_interpreter_requires_complete_generic_kicker_clause():
    interpreter = CardInterpreter()
    assert interpreter.cast_program(STOMP).kind is CastKind.KICKED_CREATURE_PT
    assert interpreter.unsupported_fragments(STOMP) == ()
    assert interpreter.kicked_creature_pt_program(STOMP).ordinary == (-2, -2)
    assert interpreter.kicked_creature_pt_program(STOMP).kicked == (-5, -5)
    assert (
        interpreter.kicked_creature_pt_program(
            replace(STOMP, oracle_text=STOMP.oracle_text + " Draw a card.")
        )
        is None
    )


def test_ordinary_and_kicked_choices_pay_and_resolve_with_cleanup():
    ordinary = ready()
    target = ordinary.create_permanent(BEAR, 1)
    card = ordinary.set_hand_for_testing(0, [STOMP])[0]
    options = [
        option for option in ordinary.legal_main_actions(0) if option.object_id == card.object_id
    ]
    assert {option.cost_object_id for option in options} == {None}
    spell = ordinary.announce_spell(0, card, target)
    assert spell is not None
    ordinary.resolve_top_of_stack()
    assert (target.power, target.toughness) == (1, 1)
    ordinary.end_turn()
    assert (target.power, target.toughness) == (3, 3)

    kicked = ready(4005)
    kicked_target = kicked.create_permanent(BEAR, 1)
    relic = kicked.create_permanent(RELIC, 0)
    kicked_card = kicked.set_hand_for_testing(0, [STOMP])[0]
    kick_options = [
        option
        for option in kicked.legal_main_actions(0)
        if option.object_id == kicked_card.object_id
    ]
    assert {option.cost_object_id for option in kick_options} == {None, relic.object_id}
    kicked_spell = kicked.announce_spell(0, kicked_card, kicked_target, sacrifice_cost=relic)
    assert kicked_spell is not None and kicked_spell.kicker_sacrifice_id == relic.object_id
    kicked.resolve_top_of_stack()
    assert kicked_target.zone == "former"
    assert any(event["event"] == "kicker_spell_resolved" for event in kicked.events)


def test_kicker_target_is_rechecked_and_no_retargeting_occurs():
    game = ready()
    target = game.create_permanent(BEAR, 1)
    relic = game.create_permanent(RELIC, 0)
    card = game.set_hand_for_testing(0, [STOMP])[0]
    spell = game.announce_spell(0, card, target, sacrifice_cost=relic)
    assert spell is not None
    game.move_object(target, "graveyard", reason="c4_target_departed")
    game.resolve_top_of_stack()
    assert any(event["event"] == "spell_resolved_no_effect" for event in game.events)
    assert not any(event["event"] == "kicker_spell_resolved" for event in game.events)


def test_kicker_payment_and_target_validation_fail_closed():
    game = ready()
    relic = game.create_permanent(RELIC, 0)
    card = game.set_hand_for_testing(0, [STOMP])[0]
    assert game.announce_spell(0, card, relic) is None
    assert game.announce_spell(0, card, None, sacrifice_cost=relic) is None
    assert relic.zone == "battlefield"
