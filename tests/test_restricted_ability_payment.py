from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TurnStep
from tmnt_design_studio.mana_ledger07 import ManaSpendingContext
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, reconcile_snapshot

LAND = CardFact("Mountain", "", 0, "Basic Land — Mountain", "({T}: Add {R}.)")
PAID_CREATURE = CardFact(
    "Synthetic Red Hero",
    "",
    0,
    "Creature — Test Hero",
    "{R}: Synthetic Red Hero gains first strike until end of turn.",
    2,
    2,
)


def setup_paid_food():
    game = Game(([LAND] * 20, [LAND] * 20), seed=38701)
    game.begin_turn()
    source = game.create_permanent(PAID_CREATURE, 0, summoning_sick=False)
    game.floating_mana.add(
        0,
        source.object_id,
        "R",
        1,
        "restricted-red-activation-production",
        allowed_contexts={ManaSpendingContext.ACTIVATED_ABILITY},
        expiration_boundary=f"turn-{game.turn}:step-end:{game.step.value}",
    )
    game.log(
        "floating_mana_produced",
        source_id=source.object_id,
        stack_object_id="restricted-red-activation-production",
        player_index=0,
        color="R",
        quantity=1,
    )
    return game, source


def test_supported_battlefield_ability_uses_activated_ability_restricted_mana():
    game, source = setup_paid_food()
    fragment = PAID_CREATURE.oracle_text
    semantics = CardInterpreter().activated_ability_semantics(PAID_CREATURE, fragment)
    assert semantics is not None and semantics.coverage.fully_supported
    assert semantics.program.effect_kind is ActivatedEffectKind.GRANT_SELF_FIRST_STRIKE_UNTIL_EOT

    plan = game.activation_payment_plan(0, source, fragment)
    assert plan is not None
    assert plan.mana_payment is not None
    assert plan.mana_payment.spending_context is ManaSpendingContext.ACTIVATED_ABILITY
    ability = game.announce_activated_ability(0, source, fragment)
    assert ability is not None
    assert game.floating_mana.consumptions(0)[0].payment_id == ability.object_id
    assert game.priority_state is not None
    assert game.priority_state.player_index == 0
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )
    assert ability.zone == "former"
    assert game.activation_evidence[-1].resolved
    assert game.stack == []
    assert game.floating_mana.snapshot(0, ManaSpendingContext.ACTIVATED_ABILITY) == {}
    assert game.floating_mana.consumptions(0)[0].source_event_id == (
        "restricted-red-activation-production"
    )
    game.check_invariants()


def test_wrong_context_is_rejected_without_mutating_activation_state():
    game, source = setup_paid_food()
    game.floating_mana = type(game.floating_mana)()
    game.floating_mana.add(
        0,
        source.object_id,
        "R",
        1,
        "artifact-only-red",
        allowed_contexts={ManaSpendingContext.ARTIFACT_SPELL},
    )
    before = game.snapshot()

    assert game.activation_payment_plan(0, source, PAID_CREATURE.oracle_text) is None
    assert game.announce_activated_ability(0, source, PAID_CREATURE.oracle_text) is None
    assert game.snapshot() == before


def test_mixed_restricted_unrestricted_and_land_activation_payment():
    card = CardFact(
        "Synthetic Mixed Payment Hero",
        "",
        0,
        "Creature — Test Hero",
        "{2}{R}: Synthetic Mixed Payment Hero gains first strike until end of turn.",
        2,
        2,
    )
    game = Game(([LAND] * 20, [LAND] * 20), seed=38702)
    game.begin_turn()
    source = game.create_permanent(card, 0, summoning_sick=False)
    land = game.create_permanent(LAND, 0, summoning_sick=False)
    game.floating_mana.add(
        0,
        source.object_id,
        "R",
        1,
        "restricted-activation-red",
        allowed_contexts={ManaSpendingContext.ACTIVATED_ABILITY},
    )
    game.floating_mana.add(0, source.object_id, "U", 1, "unrestricted-activation-blue")
    plan = game.activation_payment_plan(0, source, card.oracle_text)

    assert plan is not None and plan.mana_payment is not None
    assert plan.mana_source_ids == (land.object_id,)
    assert {item.production_event_id for item in plan.mana_payment.allocations} == {
        "restricted-activation-red",
        "unrestricted-activation-blue",
    }
    ability = game.announce_activated_ability(0, source, card.oracle_text)
    assert ability is not None and land.tapped
    assert {item.source_event_id for item in game.floating_mana.consumptions(0)} == {
        "restricted-activation-red",
        "unrestricted-activation-blue",
    }
    assert all(
        item.spending_context is ManaSpendingContext.ACTIVATED_ABILITY
        for item in game.floating_mana.consumptions(0)
    )


def test_activation_mana_plan_rejects_stale_and_forged_ledger_allocations():
    game, source = setup_paid_food()
    fragment = PAID_CREATURE.oracle_text
    plan = game.activation_payment_plan(0, source, fragment)
    assert plan is not None and plan.mana_payment is not None
    forged = replace(
        plan.mana_payment,
        spending_context=ManaSpendingContext.ARTIFACT_SPELL,
    )
    before_forgery = game.floating_mana.fingerprint_state()
    with pytest.raises(ValueError, match="forged|ineligible|stale"):
        game.floating_mana.commit_payment(0, forged)
    assert game.floating_mana.fingerprint_state() == before_forgery
    game.floating_mana.add(0, source.object_id, "U", 1, "revision-changing-production")
    after_change = game.floating_mana.fingerprint_state()
    try:
        game.floating_mana.commit_payment(0, plan.mana_payment)
    except ValueError as error:
        assert "stale" in str(error) or "revision" in str(error)
    else:
        raise AssertionError("stale activation payment plan was accepted")
    assert game.floating_mana.fingerprint_state() == after_change


def test_activation_action_enumeration_is_repeatable_and_pure():
    game, source = setup_paid_food()
    before = game.authoritative_state_fingerprint()

    first = game.legal_main_actions(0)
    second = game.legal_main_actions(0)

    assert first == second
    assert any(item.object_id == source.object_id for item in first)
    assert game.authoritative_state_fingerprint() == before


def test_hand_landcycling_uses_activation_context_and_authenticated_allocation():
    card = CardFact(
        "Synthetic Islandcycler",
        "{3}{U}",
        4,
        "Creature — Insect",
        "Islandcycling {2} ({2}, Discard this card: Search your library for an Island card, "
        "reveal it, put it into your hand, then shuffle.)",
        2,
        2,
    )
    island = CardFact("Island", "", 0, "Basic Land — Island")
    game = Game(([island] * 10, [LAND] * 10), seed=38703)
    game.begin_turn()
    game.create_permanent(island, 0, summoning_sick=False)
    game.set_hand_for_testing(0, [card])
    source = game.create_permanent(PAID_CREATURE, 0, summoning_sick=False)
    fragment = CardInterpreter().fragments(card)[0]
    for event_id in ("hand-cycle-red-1", "hand-cycle-red-2"):
        game.floating_mana.add(
            0,
            source.object_id,
            "R",
            1,
            event_id,
            allowed_contexts={ManaSpendingContext.ACTIVATED_ABILITY},
        )
    option = next(
        item
        for item in game.legal_main_actions(0)
        if item.kind is ActionKind.ACTIVATE_ABILITY and item.oracle_fragment == fragment
    )
    assert game.execute_main_action(option)
    ability = game.stack[-1]
    assert all(
        item.payment_id == game.activation_evidence[-1].payment_id
        for item in game.floating_mana.consumptions(0)
    )
    assert {item.source_event_id for item in game.floating_mana.consumptions(0)} == {
        "hand-cycle-red-1",
        "hand-cycle-red-2",
    }
    assert ability.discarded_destination_id is not None


def test_tunnel_rats_can_spend_activation_restricted_black_mana_at_end_step():
    rats = CardFact(
        "Tunnel Rats",
        "{1}{B}",
        2,
        "Creature — Rat",
        "{4}{B}: Return this card from your graveyard to the battlefield tapped.",
        2,
        2,
    )
    forest = CardFact("Forest", "", 0, "Basic Land — Forest")
    game = Game(([forest] * 20, [forest] * 20), seed=38704)
    game.begin_turn()
    for _ in range(4):
        game.create_permanent(forest, 0, summoning_sick=False)
    source = game._create_card_object(rats, 0, "graveyard")
    game.players[0].graveyard.append(source)
    game.floating_mana.add(
        0,
        source.object_id,
        "B",
        1,
        "rats-restricted-black",
        allowed_contexts={ManaSpendingContext.ACTIVATED_ABILITY},
    )
    game._step = TurnStep.END_STEP
    game._begin_priority_window(allow_empty=True, priority_player=0)
    option = next(
        item
        for item in game.legal_priority_actions(0)
        if item.object_id == source.object_id and item.oracle_fragment == rats.oracle_text
    )

    assert game.execute_priority_action(option)
    allocation = game.floating_mana.consumptions(0)[0]
    assert allocation.source_event_id == "rats-restricted-black"
    assert allocation.payment_id == game.activation_evidence[-1].payment_id
    assert allocation.spending_context is ManaSpendingContext.ACTIVATED_ABILITY
    assert all(permanent.tapped for permanent in game.players[0].battlefield)
    game.check_invariants()


def test_food_sacrifice_activation_rolls_back_restricted_payment_on_stack_failure(monkeypatch):
    from tmnt_design_studio.card_interpreter07 import TokenCreationProgram

    food = CardInterpreter.PREDEFINED_TOKENS["food"]
    game = Game(([LAND] * 20, [LAND] * 20), seed=38705)
    game.begin_turn()
    source = game.create_tokens(
        0,
        TokenCreationProgram(food, 1),
        controller=0,
        source_card="synthetic test",
        oracle_fragment="Create a Food token.",
    )[0]
    for index in range(2):
        game.floating_mana.add(
            0,
            source.object_id,
            "R",
            1,
            f"food-restricted-generic-{index}",
            allowed_contexts={ManaSpendingContext.ACTIVATED_ABILITY},
        )
    before = game.snapshot()
    original_register = game._register

    def fail_activated_ability(obj):
        from tmnt_design_studio.engine07 import ActivatedAbilityObject

        if isinstance(obj, ActivatedAbilityObject):
            raise RuntimeError("synthetic activation registration failure")
        return original_register(obj)

    monkeypatch.setattr(game, "_register", fail_activated_ability)
    with pytest.raises(RuntimeError, match="synthetic activation registration failure"):
        game.announce_activated_ability(0, source, CardInterpreter.CANONICAL_FOOD_ACTIVATION)
    assert game.snapshot() == before
    assert not game.floating_mana.consumptions(0)


def test_food_sacrifice_activation_commits_restricted_payment_before_resolution():
    from tmnt_design_studio.card_interpreter07 import TokenCreationProgram

    food = CardInterpreter.PREDEFINED_TOKENS["food"]
    game = Game(([LAND] * 20, [LAND] * 20), seed=38706)
    game.begin_turn()
    source = game.create_tokens(
        0,
        TokenCreationProgram(food, 1),
        controller=0,
        source_card="synthetic test",
        oracle_fragment="Create a Food token.",
    )[0]
    for index in range(2):
        event_id = f"food-restricted-payment-{index}"
        game.floating_mana.add(
            0,
            source.object_id,
            "R",
            1,
            event_id,
            allowed_contexts={ManaSpendingContext.ACTIVATED_ABILITY},
        )
        game.log(
            "floating_mana_produced",
            source_id=source.object_id,
            stack_object_id=event_id,
            player_index=0,
            color="R",
            quantity=1,
        )

    plan = game.activation_payment_plan(0, source, CardInterpreter.CANONICAL_FOOD_ACTIVATION)
    assert plan is not None and plan.mana_payment is not None
    assert len(plan.mana_payment.allocations) == 2
    ability = game.announce_activated_ability(0, source, CardInterpreter.CANONICAL_FOOD_ACTIVATION)

    assert ability is not None and source.zone == "former"
    assert len(game.stack) == 1 and game.stack[-1] is ability
    assert len(game.floating_mana.consumptions(0)) == 2
    assert all(
        item.spending_context is ManaSpendingContext.ACTIVATED_ABILITY
        and item.payment_id == ability.object_id
        for item in game.floating_mana.consumptions(0)
    )
    assert game.priority_state is not None
    game.check_invariants()


def test_activation_payment_snapshot_reconciles_exact_source_and_allocation():
    game, source = setup_paid_food()
    fragment = PAID_CREATURE.oracle_text
    assert game.announce_activated_ability(0, source, fragment) is not None
    snapshot = game.snapshot()
    snapshot["stage002_presence"] = []
    spec = GameSpec(
        "synthetic-activation-payment",
        "synthetic-activation-payment",
        game.rng.seed,
        "canonical",
        (DeckSpec("A", ""), DeckSpec("B", "")),
    )
    report = reconcile_snapshot(spec, snapshot, {"decks": [{"cards": []}, {"cards": []}]})

    assert not [
        item for item in report["stop_records"] if item["kind"] == "mana_payment_provenance"
    ]
    evidence = snapshot["activated_abilities"][0]
    assert evidence["source_id"] == source.object_id
    assert evidence["oracle_fragment"] == fragment
    assert evidence["spending_context"] == "activated_ability"
    assert evidence["mana_allocations"][0]["production_event_id"] == (
        "restricted-red-activation-production"
    )
    assert snapshot["conformance"]["executed_references"] == []

    tampered = game.snapshot()
    tampered["stage002_presence"] = []
    tampered["activated_abilities"][0]["source_id"] = "forged-activation-source"
    bad_report = reconcile_snapshot(spec, tampered, {"decks": [{"cards": []}, {"cards": []}]})
    assert any(item["kind"] == "mana_payment_provenance" for item in bad_report["stop_records"])

    missing = game.snapshot()
    missing["stage002_presence"] = []
    missing.pop("activated_abilities")
    missing_report = reconcile_snapshot(spec, missing, {"decks": [{"cards": []}, {"cards": []}]})
    assert any(
        "activation_payment_evidence_missing" in item["detail"]
        for item in missing_report["stop_records"]
        if item["kind"] == "mana_payment_provenance"
    )
