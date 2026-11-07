"""Synthetic contracts for typed spell payment using restricted mana lots."""

from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CastKind
from tmnt_design_studio.engine07 import CardFact, Game, TurnStep
from tmnt_design_studio.mana_ledger07 import (
    FloatingManaLedger,
    ManaAllocation,
    ManaSpendingContext,
)
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, reconcile_snapshot

MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land — Mountain", "({T}: Add {R}.)")
ISLAND = CardFact("Island", "", 0, "Basic Land — Island", "({T}: Add {U}.)")
ARTIFACT = CardFact("Red Artifact", "{R}", 1, "Artifact")
NONARTIFACT = CardFact("Red Creature", "{R}", 1, "Creature — Test", power=1, toughness=1)
MIXED_ARTIFACT = CardFact("Mixed Artifact", "{2}{R}", 3, "Artifact")
HYBRID_ARTIFACT = CardFact("Hybrid Artifact", "{1}{U/R}{R}", 3, "Artifact")
MANA_SOURCE = CardFact("Synthetic Mana Source", "", 0, "Artifact")


def make_game(card: CardFact) -> tuple[Game, object, object]:
    game = Game(([MOUNTAIN] * 20, [MOUNTAIN] * 20), seed=3871)
    game.begin_turn()
    source = game.create_permanent(MANA_SOURCE, 0, summoning_sick=False)
    spell = game.set_hand_for_testing(0, [card])[0]
    return game, source, spell


def add_restricted_mana(
    game: Game,
    source: object,
    event_id: str,
    color: str = "R",
    quantity: int = 1,
    contexts: frozenset[ManaSpendingContext] = frozenset({ManaSpendingContext.ARTIFACT_SPELL}),
) -> None:
    game.floating_mana.add(
        0,
        source.object_id,
        color,
        quantity,
        event_id,
        allowed_contexts=contexts,
        expiration_boundary=f"turn-{game.turn}:step-end:{game.step.value}",
    )
    game.log(
        "floating_mana_produced",
        source_id=source.object_id,
        stack_object_id=event_id,
        player_index=0,
        color=color,
        quantity=quantity,
    )


def test_repeated_ledger_payment_planning_is_pure_and_deterministic():
    ledger = FloatingManaLedger()
    ledger.add(
        0,
        "source-artifact-only",
        "R",
        1,
        "production-artifact-only",
        allowed_contexts={ManaSpendingContext.ARTIFACT_SPELL},
    )
    before = ledger.fingerprint_state()

    first = ledger.plan_payment(0, {"R": 1}, "spell-object-1", ManaSpendingContext.ARTIFACT_SPELL)
    second = ledger.plan_payment(0, {"R": 1}, "spell-object-1", ManaSpendingContext.ARTIFACT_SPELL)

    assert first == second
    assert ledger.fingerprint_state() == before
    assert not hasattr(ledger, "_issued_payment_plans")


def test_ledger_payment_plan_is_stale_after_any_mana_state_change():
    ledger = FloatingManaLedger()
    ledger.add(0, "source-one", "R", 1, "production-one")
    plan = ledger.plan_payment(0, {"R": 1}, "spell-object-1", ManaSpendingContext.ARTIFACT_SPELL)
    ledger.add(0, "source-two", "U", 1, "production-two")
    before = ledger.fingerprint_state()

    with pytest.raises(ValueError, match="stale|revision"):
        ledger.commit_payment(0, plan)

    assert ledger.fingerprint_state() == before


def test_committed_payment_identity_cannot_be_reused_by_another_controller():
    ledger = FloatingManaLedger()
    ledger.add(0, "source-zero", "R", 1, "production-zero")
    ledger.add(1, "source-one", "R", 1, "production-one")
    player_zero_plan = ledger.plan_payment(
        0, {"R": 1}, "shared-payment-id", ManaSpendingContext.ARTIFACT_SPELL
    )
    player_one_plan = ledger.plan_payment(
        1, {"R": 1}, "shared-payment-id", ManaSpendingContext.ARTIFACT_SPELL
    )
    assert player_zero_plan is not None and player_one_plan is not None
    ledger.commit_payment(0, player_zero_plan)
    before = ledger.fingerprint_state()

    with pytest.raises(ValueError, match="stale|revision|committed"):
        ledger.commit_payment(1, player_one_plan)
    assert ledger.fingerprint_state() == before
    with pytest.raises(ValueError, match="already committed"):
        ledger.plan_payment(1, {"R": 1}, "shared-payment-id", ManaSpendingContext.ARTIFACT_SPELL)


def test_artifact_spell_uses_restricted_mana_and_snapshots_exact_cast_linkage():
    game, source, card = make_game(ARTIFACT)
    add_restricted_mana(game, source, "mana-event-artifact")

    plan = game.payment_plan(0, card)
    assert plan is not None and plan.mana_payment is not None
    assert plan.mana_payment.spending_context is ManaSpendingContext.ARTIFACT_SPELL
    assert plan.mana_payment.allocations == (ManaAllocation("mana-event-artifact", 0, "R", 1),)
    spell = game.announce_spell(0, card)
    assert spell is not None and spell.cast_kind is CastKind.PERMANENT

    snapshot = game.snapshot()
    payment = snapshot["spell_payment_evidence"][0]
    cast_event = next(
        item
        for item in snapshot["rules_event_evidence"]
        if item["event_id"] == payment["spell_event_id"]
    )
    assert payment["payment_id"] == card.object_id
    assert payment["card_object_id"] == card.object_id
    assert payment["spell_object_id"] == spell.object_id
    assert payment["spending_context"] == "artifact_spell"
    assert payment["mana_allocations"][0]["production_event_id"] == "mana-event-artifact"
    assert payment["mana_allocations"][0]["quantity"] == 1
    assert cast_event["kind"] == "spell_cast"
    assert cast_event["source_id"] == spell.object_id
    assert cast_event["card_oracle_id"] == ARTIFACT.oracle_id
    lot = snapshot["floating_mana_ledger"]["players"][0]["productions"][0]
    assert lot["source_id"] == source.object_id and lot["remaining_quantity"] == 0


def test_nonartifact_cannot_spend_artifact_only_mana_but_can_use_unrestricted_mana():
    game, source, card = make_game(NONARTIFACT)
    add_restricted_mana(game, source, "mana-event-artifact-only")
    before = game.authoritative_state_fingerprint()
    before_events = tuple(game.events)

    assert game.payment_plan(0, card) is None
    assert game.announce_spell(0, card) is None
    assert game.authoritative_state_fingerprint() == before
    assert tuple(game.events) == before_events
    assert game.stack == [] and card.zone == "hand"

    game.floating_mana.add(0, source.object_id, "R", 1, "mana-event-unrestricted")
    plan = game.payment_plan(0, card)
    assert plan is not None and plan.mana_payment is not None
    assert plan.mana_payment.spending_context is ManaSpendingContext.NONARTIFACT_SPELL
    assert [item.production_event_id for item in plan.mana_payment.allocations] == [
        "mana-event-unrestricted"
    ]
    assert game.announce_spell(0, card) is not None


def test_mixed_restricted_unrestricted_and_land_payment_preserves_partial_lot():
    game, source, card = make_game(MIXED_ARTIFACT)
    add_restricted_mana(game, source, "mana-event-restricted")
    game.floating_mana.add(0, source.object_id, "R", 1, "mana-event-unrestricted")
    first_land = game.create_permanent(MOUNTAIN, 0, summoning_sick=False)
    second_land = game.create_permanent(MOUNTAIN, 0, summoning_sick=False)

    plan = game.payment_plan(0, card)
    assert plan is not None and plan.mana_payment is not None
    assert plan.floating_colors == ("R", "R")
    assert plan.source_ids == (first_land.object_id,)
    spell = game.announce_spell(0, card)
    assert spell is not None and first_land.tapped and not second_land.tapped
    lots = game.floating_mana.lots(0)
    assert [(item.production.event_id, item.remaining_quantity) for item in lots] == [
        ("mana-event-restricted", 0),
        ("mana-event-unrestricted", 0),
    ]
    allocations = game.floating_mana.consumptions(0)
    assert [(item.source_event_id, item.quantity) for item in allocations] == [
        ("mana-event-restricted", 1),
        ("mana-event-unrestricted", 1),
    ]

    partial_game, partial_source, partial_card = make_game(ARTIFACT)
    add_restricted_mana(partial_game, partial_source, "mana-event-partial", quantity=2)
    assert partial_game.announce_spell(0, partial_card) is not None
    partial_lot = partial_game.floating_mana.lots(0)[0]
    assert partial_lot.remaining_quantity == 1 and partial_lot.valid


def test_multicolor_and_hybrid_spending_uses_typed_lots_and_land_sources():
    game, source, card = make_game(HYBRID_ARTIFACT)
    add_restricted_mana(game, source, "mana-event-red", "R")
    game.floating_mana.add(0, source.object_id, "U", 1, "mana-event-blue")
    generic_land = game.create_permanent(MOUNTAIN, 0, summoning_sick=False)

    plan = game.payment_plan(0, card)
    assert plan is not None and plan.mana_payment is not None
    assert plan.source_ids == (generic_land.object_id,)
    assert plan.mana_payment.requirements == (("R", 1), ("U", 1))
    assert game.announce_spell(0, card) is not None
    assert generic_land.tapped
    assert {item.source_event_id for item in game.floating_mana.consumptions(0)} == {
        "mana-event-red",
        "mana-event-blue",
    }


def test_expired_forged_wrong_purpose_and_duplicate_spell_plans_fail_atomically():
    game, source, card = make_game(ARTIFACT)
    add_restricted_mana(game, source, "mana-event-stale")
    land = game.create_permanent(MOUNTAIN, 0, summoning_sick=False)
    plan = game.payment_plan(0, card)
    assert plan is not None and plan.mana_payment is not None
    corrupted_ledger_plan = replace(
        plan.mana_payment,
        spending_context=ManaSpendingContext.NONARTIFACT_SPELL,
    )
    forged = replace(plan, mana_payment=corrupted_ledger_plan)
    before = game.authoritative_state_fingerprint()
    with pytest.raises(ValueError, match="no longer legal"):
        game._commit_announcement_payment(
            card, forged, cast_kind=CastKind.PERMANENT, target_id=None
        )
    assert game.authoritative_state_fingerprint() == before
    assert card.zone == "hand" and not land.tapped and game.stack == []


def test_reusing_a_successful_spell_payment_plan_cannot_consume_or_cast_twice():
    game, source, card = make_game(ARTIFACT)
    add_restricted_mana(game, source, "mana-event-duplicate")
    plan = game.payment_plan(0, card)
    assert plan is not None
    first_spell = game.announce_spell(0, card)
    assert first_spell is not None
    before = game.authoritative_state_fingerprint()
    payment_count = len(game.floating_mana.consumptions(0))
    cast_event_count = sum(
        event.kind.value == "spell_cast" and event.source_id == first_spell.object_id
        for event in game._rules_events.values()
    )

    with pytest.raises(ValueError, match="no longer legal"):
        game._commit_announcement_payment(card, plan, cast_kind=CastKind.PERMANENT, target_id=None)

    assert game.authoritative_state_fingerprint() == before
    assert len(game.floating_mana.consumptions(0)) == payment_count
    assert (
        sum(
            event.kind.value == "spell_cast" and event.source_id == first_spell.object_id
            for event in game._rules_events.values()
        )
        == cast_event_count
        == 1
    )


def test_zone_failure_rolls_back_land_and_restricted_mana_payment(monkeypatch):
    game, source, card = make_game(MIXED_ARTIFACT)
    add_restricted_mana(game, source, "mana-event-zone-failure")
    land = game.create_permanent(MOUNTAIN, 0, summoning_sick=False)
    second_land = game.create_permanent(MOUNTAIN, 0, summoning_sick=False)
    plan = game.payment_plan(0, card)
    assert plan is not None and plan.mana_payment is not None
    before = game.authoritative_state_fingerprint()

    def fail_move(*_args, **_kwargs):
        raise RuntimeError("injected zone failure")

    monkeypatch.setattr(game, "move_object", fail_move)
    with pytest.raises(RuntimeError, match="injected zone failure"):
        game._commit_announcement_payment(card, plan, cast_kind=CastKind.PERMANENT, target_id=None)

    assert game.authoritative_state_fingerprint() == before
    assert card.zone == "hand" and not land.tapped and not second_land.tapped and game.stack == []
    assert not game.floating_mana.consumptions(0)
    assert not game.spell_payment_evidence
    assert not any(event.kind.value == "spell_cast" for event in game._rules_events.values())
    assert not game.floating_mana.consumptions(0)

    game.transition_to(TurnStep.BEGINNING_OF_COMBAT)
    before_expired_attempt = game.authoritative_state_fingerprint()
    with pytest.raises(ValueError, match="no longer legal"):
        game._commit_announcement_payment(card, plan, cast_kind=CastKind.PERMANENT, target_id=None)
    assert game.authoritative_state_fingerprint() == before_expired_attempt
    assert card.zone == "hand" and not land.tapped and game.stack == []


def test_legal_action_planning_is_repeatable_and_does_not_authorize_payment():
    game, source, _card = make_game(ARTIFACT)
    add_restricted_mana(game, source, "mana-event-repeated-plan")
    before = game.authoritative_state_fingerprint()

    first = game.legal_main_actions(0)
    second = game.legal_main_actions(0)

    assert first == second
    assert game.authoritative_state_fingerprint() == before
    assert not hasattr(game.floating_mana, "_issued_payment_plans")


def test_graveyard_and_exile_spell_paths_share_typed_payment_contract():
    leonardo = CardFact(
        "Leonardo, Sewer Samurai",
        "{3}{W}",
        4,
        "Legendary Creature — Mutant Ninja Turtle Samurai",
        "During your turn, you may cast creature spells with power or toughness 1 or less "
        "from your graveyard. If you cast a spell this way, that creature enters with a finality "
        "counter on it.",
        power=3,
        toughness=3,
    )
    grave_creature = CardFact(
        "Small Red Creature", "{R}", 1, "Creature — Test", power=1, toughness=1
    )
    grave_game = Game(([MOUNTAIN] * 20, [MOUNTAIN] * 20), seed=3872)
    grave_game.begin_turn()
    grave_game.advance_to(TurnStep.PRECOMBAT_MAIN)
    grave_game.create_permanent(leonardo, 0, summoning_sick=False)
    source = grave_game.create_permanent(MANA_SOURCE, 0, summoning_sick=False)
    grave_card = grave_game.set_hand_for_testing(0, [grave_creature])[0]
    grave_card = grave_game.move_object(grave_card, "graveyard", reason="synthetic_setup")
    grave_game.floating_mana.add(
        0,
        source.object_id,
        "R",
        1,
        "mana-event-graveyard",
        allowed_contexts={ManaSpendingContext.NONARTIFACT_SPELL},
    )
    grave_plan = grave_game.payment_plan(0, grave_card, allow_graveyard=True)
    assert grave_plan is not None and grave_plan.mana_payment is not None
    assert grave_game.announce_spell(0, grave_card, cast_from_graveyard=True) is not None

    raphael = CardFact(
        "Raphael, Most Attitude",
        "{3}{R}",
        4,
        "Legendary Creature",
        "Whenever Raphael attacks, you may play a card exiled with Raphael.",
        power=4,
        toughness=3,
    )
    exile_game = Game(([MOUNTAIN] * 20, [MOUNTAIN] * 20), seed=3873)
    exile_game.begin_turn()
    exile_source = exile_game.create_permanent(raphael, 0, summoning_sick=False)
    mana_source = exile_game.create_permanent(MANA_SOURCE, 0, summoning_sick=False)
    exile_card = exile_game._create_card_object(ARTIFACT, 0, "exile")
    exile_game.players[0].exile.append(exile_card)
    exile_game._raphael_linked_exile[exile_source.object_id] = [
        (exile_card.object_id, exile_card.card, exile_source.object_id)
    ]
    exile_game._raphael_permissions[exile_source.object_id] = (
        exile_game.turn,
        exile_card.object_id,
    )
    add_restricted_mana(exile_game, mana_source, "mana-event-exile")
    exile_plan = exile_game.payment_plan(0, exile_card, allow_exile=True)
    assert exile_plan is not None and exile_plan.mana_payment is not None
    assert exile_game.announce_spell(0, exile_card, cast_from_exile=True) is not None


def test_spell_payment_snapshot_reconciles_without_invented_execution_reference():
    game, source, card = make_game(ARTIFACT)
    add_restricted_mana(game, source, "mana-event-reconcile")
    spell = game.announce_spell(0, card)
    assert spell is not None
    snapshot = game.snapshot()
    snapshot["stage002_presence"] = []
    manifest = {"decks": [{"cards": []}, {"cards": []}]}
    spec = GameSpec(
        "synthetic-restricted-payment",
        "synthetic-restricted-payment",
        game.rng.seed,
        "canonical",
        (DeckSpec("A", ""), DeckSpec("B", "")),
    )

    report = reconcile_snapshot(spec, snapshot, manifest)

    assert report["stop_records"] == []
    assert snapshot["conformance"]["executed_references"] == []
    assert (
        report["authoritative_evidence"]["spell_payment_evidence"]
        == snapshot["spell_payment_evidence"]
    )


def test_reconciler_rejects_payment_evidence_that_disagrees_with_cast_or_lot():
    game, source, card = make_game(ARTIFACT)
    add_restricted_mana(game, source, "mana-event-tamper")
    assert game.announce_spell(0, card) is not None
    snapshot = game.snapshot()
    snapshot["stage002_presence"] = []
    snapshot["spell_payment_evidence"][0]["mana_allocations"][0]["quantity"] = 2
    snapshot["floating_mana_ledger"]["players"][0]["productions"][0]["source_id"] = "forged-source"
    manifest = {"decks": [{"cards": []}, {"cards": []}]}
    spec = GameSpec(
        "synthetic-restricted-payment-tamper",
        "synthetic-restricted-payment",
        game.rng.seed,
        "canonical",
        (DeckSpec("A", ""), DeckSpec("B", "")),
    )

    report = reconcile_snapshot(spec, snapshot, manifest)

    assert any(item["kind"] == "mana_payment_provenance" for item in report["stop_records"])
    assert any(
        "mana_production_source_event_invalid" in detail
        for item in report["stop_records"]
        for detail in item["detail"]
    )
    assert snapshot["conformance"]["executed_references"] == []
