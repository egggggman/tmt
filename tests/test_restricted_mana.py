"""Oracle-derived tap mana, per-unit spending restrictions, and exact payment lineage."""

from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, StackObject
from tmnt_design_studio.mana_ledger07 import FloatingManaLedger

PUNKS = CardFact(
    "Unrelated Source",
    "{1}{R}",
    2,
    "Creature — Rogue",
    "{T}: Add {R}. Spend this mana only to cast an artifact spell or to activate an ability.",
    power=2,
    toughness=2,
)
FRAGMENT = PUNKS.oracle_text
ARTIFACT = CardFact(
    "Artifact Recipient", "{R}", 1, "Artifact Creature — Construct", power=1, toughness=1
)
CREATURE = CardFact("Creature Recipient", "{R}", 1, "Creature — Construct", power=1, toughness=1)
DRAW = CardFact(
    "One-use Tool",
    "{1}",
    1,
    "Artifact",
    "{R}, Sacrifice this artifact: Draw one card.",
)
CYCLING_TEXT = (
    "Islandcycling {2} ({2}, Discard this card: Search your library for an Island "
    "card, reveal it, put it into your hand, then shuffle.)"
)
CYCLER = CardFact("Anonymous Cycler", "{3}", 3, "Creature", CYCLING_TEXT, 2, 2)


def setup(*hand):
    game = Game(([CREATURE] * 25, [CREATURE] * 25), seed=289)
    game.begin_turn()
    game.set_hand_for_testing(0, list(hand))
    source = game.create_permanent(PUNKS, 0, summoning_sick=False)
    return game, source


def activate(game, source):
    option = next(
        option
        for option in game.legal_main_actions(0)
        if option.kind is ActionKind.ACTIVATE_ABILITY
        and option.object_id == source.object_id
        and option.oracle_fragment == FRAGMENT
    )
    assert option.choice_ids == ("R",)
    assert game.execute_main_action(option)
    assert source.tapped and not game.stack and game.priority_state is None
    return game.floating_mana.productions(0)[-1]


def test_generic_interpretation_rejects_unrepresented_restrictions_and_output():
    interpreter = CardInterpreter()
    assert interpreter.mana_ability_program(FRAGMENT).allowed_spending == (
        "artifact_spell",
        "activate_ability",
    )
    assert interpreter.activated_ability_semantics(PUNKS, FRAGMENT).coverage.fully_supported
    assert interpreter.activated_ability_semantics(
        replace(PUNKS, name="Other"), FRAGMENT
    ).coverage.fully_supported
    for text in (
        "{T}: Add {R}. Spend this mana only to cast a creature spell.",
        "{T}: Add {R}{R}.",
        "{T}: Add {R}. Draw a card.",
    ):
        assert interpreter.mana_ability_program(text) is None
        assert not interpreter.activated_ability_semantics(
            replace(PUNKS, oracle_text=text), text
        ).coverage.fully_supported


def test_restricted_unit_cannot_pay_creature_but_can_pay_artifact_with_lineage():
    def run():
        game, source = setup(CREATURE, ARTIFACT)
        production = activate(game, source)
        assert production.source_id == source.object_id
        assert production.allowed_spending == ("artifact_spell", "activate_ability")
        assert game.floating_mana.snapshot(0) == {"R": 1}
        creature, artifact = game.players[0].hand
        assert game.payment_plan(0, creature) is None and not game.can_afford(0, CREATURE)
        assert not any(
            option.kind is ActionKind.CAST and option.object_id == creature.object_id
            for option in game.legal_main_actions(0)
        )
        plan = game.payment_plan(0, artifact)
        assert plan is not None and plan.floating_event_ids == (production.event_id,)
        spell = game.announce_spell(0, artifact)
        assert spell is not None
        assert game.floating_mana.snapshot(0) == {}
        assert game.floating_mana.consumptions(0)[-1].source_event_id == production.event_id
        assert game.floating_mana.consumptions(0)[-1].payment_id == artifact.object_id
        game.resolve_top_of_stack()
        game.check_invariants()
        return game.snapshot()

    assert run() == run()


def test_restricted_unit_pays_activated_cost_after_source_leaves():
    game, source = setup()
    production = activate(game, source)
    game.move_object(source, "graveyard", reason="test_departure")
    tool = game.create_permanent(DRAW, 0)
    plan = game.activation_payment_plan(0, tool, DRAW.oracle_text)
    assert plan is not None and plan.floating_event_ids == (production.event_id,)
    ability = game.announce_activated_ability(0, tool, DRAW.oracle_text)
    assert ability is not None
    assert not game.floating_mana.snapshot(0)
    assert game.floating_mana.consumptions(0)[-1].payment_id == ability.object_id
    assert tool.zone == "former" and game.stack[-1] is ability
    while game.priority_state is not None:
        state = game.priority_state
        if state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(game.legal_priority_actions(state.player_index)[0])
    game.check_invariants()


def test_restricted_unit_contributes_to_generic_hand_ability_cost():
    game, source = setup(CYCLER)
    game.create_permanent(CardFact("Island", "", 0, "Basic Land — Island"), 0)
    # The Island pays the other generic mana; the restricted unit pays one.
    production = activate(game, source)
    card = game.players[0].hand[0]
    assert any(
        option.object_id == card.object_id and option.oracle_fragment == CYCLING_TEXT
        for option in game.legal_hand_activated_ability_actions(0)
    )
    ability = game.announce_hand_activated_ability(0, card, CYCLING_TEXT)
    assert ability is not None
    assert game.floating_mana.consumptions(0)[-1].source_event_id == production.event_id
    assert game.floating_mana.consumptions(0)[-1].payment_id == ability.object_id


def test_stale_plan_and_invalid_context_fail_before_resource_mutation():
    game, source = setup(ARTIFACT, ARTIFACT)
    production = activate(game, source)
    first, second = game.players[0].hand
    stale = game.payment_plan(0, second)
    assert stale is not None
    with pytest.raises(ValueError, match="payment context"):
        game.floating_mana.consume_events(0, (production.event_id,), "bad", "other_spell")
    assert game.floating_mana.snapshot(0) == {"R": 1}
    assert game.announce_spell(0, first) is not None
    with pytest.raises(ValueError, match="no longer legal"):
        game._commit_announcement_payment(
            second, stale, cast_kind=CastKind.PERMANENT, target_id=None
        )
    assert game.is_authoritative(second, "hand") and not game.floating_mana.snapshot(0)
    assert len(game.floating_mana.consumptions(0)) == 1


def test_priority_mana_activation_resolves_without_changing_existing_stack():
    game, source = setup()
    pending = StackObject(game._allocate_object_id(), CREATURE, 1, 1, CastKind.CREATURE)
    game._register(pending)
    game.stack.append(pending)
    game._begin_priority_window()
    state = game.priority_state
    option = next(
        option
        for option in game.legal_priority_actions(0)
        if option.kind is ActionKind.ACTIVATE_ABILITY and option.object_id == source.object_id
    )
    game.execute_priority_action(option)
    assert game.priority_state == state and game.stack == [pending]
    assert game.floating_mana.snapshot(0) == {"R": 1}
    game.check_invariants()


def test_summoning_sickness_and_step_expiration():
    game, source = setup()
    source.summoning_sick = True
    assert game.activation_payment_plan(0, source, FRAGMENT) is None
    assert not any(
        option.kind is ActionKind.ACTIVATE_ABILITY and option.object_id == source.object_id
        for option in game.legal_main_actions(0)
    )
    source.summoning_sick = False
    production = activate(game, source)
    game.advance_step()
    assert game.floating_mana.snapshot(0) == {}
    assert game.floating_mana.eligible(0, "artifact_spell") == ()
    assert game.floating_mana.consumptions(0)[-1].source_event_id == production.event_id


def test_ledger_checks_all_units_transactionally_and_preserves_mixed_sources():
    ledger = FloatingManaLedger()
    ledger.add(0, "restricted", "R", 1, "one", ("artifact_spell", "activate_ability"))
    ledger.add(0, "unrestricted", "R", 1, "two")
    assert [unit.event_id for unit in ledger.eligible(0, "other_spell")] == ["two"]
    with pytest.raises(ValueError, match="payment context"):
        ledger.consume_events(0, ("two", "one"), "failed", "other_spell")
    assert ledger.snapshot(0) == {"R": 2} and ledger.consumptions(0) == ()
    ledger.consume_events(0, ("two",), "ordinary", "other_spell")
    assert ledger.snapshot(0) == {"R": 1}
    ledger.consume_events(0, ("one",), "artifact", "artifact_spell")
    assert [item.source_event_id for item in ledger.consumptions(0)] == ["two", "one"]
