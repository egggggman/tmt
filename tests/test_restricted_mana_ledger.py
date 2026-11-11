"""Synthetic contracts for source-authenticated, context-restricted mana lots."""

from dataclasses import replace

import pytest

from tmnt_design_studio.engine07 import CardFact, Game, TurnStep
from tmnt_design_studio.mana_ledger07 import (
    FloatingManaLedger,
    ManaAllocation,
    ManaPaymentPlan,
    ManaSpendingContext,
)


def test_expiration_does_not_reuse_an_older_same_color_production_lot():
    ledger = FloatingManaLedger()
    ledger.add(0, "source-A", "R", 1, "production-A")
    ledger.empty(0)
    ledger.add(0, "source-B", "R", 1, "production-B")

    consumed = ledger.consume(0, "R", 1, "payment-1")

    assert consumed.source_event_id == "production-B"


def test_context_restrictions_and_unrestricted_lots_are_distinct():
    ledger = FloatingManaLedger()
    ledger.add(
        0,
        "restricted-source",
        "R",
        1,
        "restricted-production",
        allowed_contexts={
            ManaSpendingContext.ARTIFACT_SPELL,
            ManaSpendingContext.ACTIVATED_ABILITY,
        },
    )
    assert ledger.snapshot(0) == {}
    assert ledger.snapshot(0, ManaSpendingContext.ARTIFACT_SPELL) == {"R": 1}
    assert (
        ledger.plan_payment(
            0, {"R": 1}, "nonartifact-payment", ManaSpendingContext.NONARTIFACT_SPELL
        )
        is None
    )
    ledger.add(0, "ordinary-source", "R", 1, "ordinary-production")
    ordinary = ledger.plan_payment(
        0, {"R": 1}, "ordinary-payment", ManaSpendingContext.NONARTIFACT_SPELL
    )
    assert ordinary.allocations == (ManaAllocation("ordinary-production", 0, "R", 1),)


def test_mixed_lots_and_partial_payment_preserve_exact_remaining_quantity():
    ledger = FloatingManaLedger()
    ledger.add(
        0,
        "restricted-source",
        "R",
        2,
        "restricted-production",
        allowed_contexts={ManaSpendingContext.ARTIFACT_SPELL},
    )
    ledger.add(0, "ordinary-source", "R", 1, "ordinary-production")
    mixed = ledger.plan_payment(0, {"R": 3}, "artifact-payment", ManaSpendingContext.ARTIFACT_SPELL)
    assert mixed.allocations == (
        ManaAllocation("restricted-production", 0, "R", 2),
        ManaAllocation("ordinary-production", 0, "R", 1),
    )
    committed = ledger.commit_payment(0, mixed)
    assert [item.source_event_id for item in committed] == [
        "restricted-production",
        "ordinary-production",
    ]

    ledger.add(
        0,
        "partial-source",
        "R",
        2,
        "partial-production",
        allowed_contexts={ManaSpendingContext.ACTIVATED_ABILITY},
    )
    partial = ledger.plan_payment(
        0, {"R": 1}, "ability-payment", ManaSpendingContext.ACTIVATED_ABILITY
    )
    ledger.commit_payment(0, partial)
    lot = next(item for item in ledger.lots(0) if item.production.event_id == "partial-production")
    assert lot.remaining_quantity == 1 and lot.valid
    assert ledger.snapshot(0, ManaSpendingContext.ACTIVATED_ABILITY) == {"R": 1}


def test_payment_rejections_are_atomic_for_forged_duplicate_and_wrong_context_allocations():
    ledger = FloatingManaLedger()
    ledger.add(
        0,
        "restricted-source",
        "R",
        1,
        "restricted-production",
        allowed_contexts={ManaSpendingContext.ARTIFACT_SPELL},
    )
    plan = ledger.plan_payment(0, {"R": 1}, "payment-1", ManaSpendingContext.ARTIFACT_SPELL)
    before = ledger.fingerprint_state()
    with pytest.raises(ValueError):
        ledger.commit_payment(
            0,
            replace(
                plan,
                allocations=plan.allocations + (ManaAllocation("forged-event", 0, "U", 1),),
            ),
        )
    assert ledger.fingerprint_state() == before

    with pytest.raises(ValueError):
        ledger.commit_payment(
            0,
            ManaPaymentPlan(
                controller=0,
                payment_id="unissued-payment",
                spending_context=ManaSpendingContext.ARTIFACT_SPELL,
                requirements=(("R", 1),),
                allocations=(ManaAllocation("restricted-production", 0, "R", 1),),
            ),
        )
    assert ledger.fingerprint_state() == before

    with pytest.raises(ValueError):
        ledger.commit_payment(0, replace(plan, allocations=plan.allocations + plan.allocations))
    assert ledger.fingerprint_state() == before

    with pytest.raises(ValueError):
        ledger.commit_payment(
            0,
            replace(
                plan,
                allocations=(ManaAllocation("restricted-production", 0, "U", 1),),
            ),
        )
    assert ledger.fingerprint_state() == before

    with pytest.raises(ValueError):
        ledger.commit_payment(
            0,
            replace(
                plan,
                allocations=(ManaAllocation("restricted-production", 0, "R", 2),),
            ),
        )
    assert ledger.fingerprint_state() == before

    with pytest.raises(ValueError):
        ledger.commit_payment(
            0, replace(plan, spending_context=ManaSpendingContext.NONARTIFACT_SPELL)
        )
    assert ledger.fingerprint_state() == before


def test_expired_or_incorrect_controller_allocations_cannot_be_committed():
    ledger = FloatingManaLedger()
    ledger.add(
        0,
        "restricted-source",
        "R",
        1,
        "production-1",
        allowed_contexts={ManaSpendingContext.ARTIFACT_SPELL},
    )
    plan = ledger.plan_payment(0, {"R": 1}, "payment-1", ManaSpendingContext.ARTIFACT_SPELL)
    ledger.expire(0, "turn-1:step-end:precombat_main")
    before = ledger.fingerprint_state()
    with pytest.raises(ValueError):
        ledger.commit_payment(0, plan)
    assert ledger.fingerprint_state() == before

    ledger.add(
        0,
        "second-source",
        "R",
        1,
        "production-2",
        allowed_contexts={ManaSpendingContext.ACTIVATED_ABILITY},
    )
    valid_plan = ledger.plan_payment(
        0, {"R": 1}, "payment-2", ManaSpendingContext.ACTIVATED_ABILITY
    )
    forged_controller = replace(
        valid_plan,
        allocations=(ManaAllocation("production-2", 1, "R", 1),),
    )
    before = ledger.fingerprint_state()
    with pytest.raises(ValueError):
        ledger.commit_payment(0, forged_controller)
    assert ledger.fingerprint_state() == before


def test_lifecycle_evidence_preserves_consumption_expiration_and_boundary():
    ledger = FloatingManaLedger()
    ledger.add(
        0,
        "source-A",
        "R",
        2,
        "production-A",
        allowed_contexts={ManaSpendingContext.ARTIFACT_SPELL},
        expiration_boundary="turn-1:step-end:precombat_main",
    )
    plan = ledger.plan_payment(0, {"R": 1}, "payment-1", ManaSpendingContext.ARTIFACT_SPELL)
    ledger.commit_payment(0, plan)
    expired = ledger.expire(0, "turn-1:step-end:precombat_main")
    assert len(expired) == 1
    assert expired[0].production_event_id == "production-A"
    assert expired[0].quantity == 1
    assert ledger.lots(0)[0].remaining_quantity == 0
    assert not ledger.lots(0)[0].valid
    assert ledger.snapshot(0, ManaSpendingContext.ARTIFACT_SPELL) == {}
    evidence = ledger.evidence_snapshot()["players"][0]
    assert evidence["productions"][0]["source_id"] == "source-A"
    assert evidence["payments"][0]["production_event_id"] == "production-A"
    assert evidence["expirations"][0]["boundary_id"] == "turn-1:step-end:precombat_main"


def test_legacy_payment_can_consume_multiple_colors_under_one_payment_id():
    ledger = FloatingManaLedger()
    ledger.add(0, "red-source", "R", 1, "red-production")
    ledger.add(0, "blue-source", "U", 1, "blue-production")

    red = ledger.consume(0, "R", 1, "multicolor-spell")
    blue = ledger.consume(0, "U", 1, "multicolor-spell")

    assert red.payment_id == blue.payment_id == "multicolor-spell"
    assert [item.source_event_id for item in ledger.consumptions(0)] == [
        "red-production",
        "blue-production",
    ]


def test_game_snapshot_and_fingerprint_include_authenticated_frog_mana_lifecycle():
    land = CardFact("Forest", "", 0, "Basic Land — Forest")
    frog = CardFact(
        "Frog Butler",
        "{1}{G}",
        2,
        "Creature — Frog Spirit",
        "{T}: Add one mana of any color.",
        power=2,
        toughness=2,
    )
    game = Game(([land] * 20, [land] * 20), seed=771)
    game.begin_turn()
    source = game.create_permanent(frog, 0, summoning_sick=False)
    before = game.authoritative_state_fingerprint()
    ability = game.announce_activated_ability(
        0, source, "{T}: Add one mana of any color.", choice_ids=("R",)
    )
    assert ability is not None and ability.zone == "former"
    snapshot = game.snapshot()
    production = snapshot["floating_mana_ledger"]["players"][0]["productions"][0]
    assert production["source_id"] == source.object_id
    assert production["controller"] == 0
    assert production["event_id"] == ability.object_id
    assert production["color"] == "R" and production["remaining_quantity"] == 1
    assert production["expiration_boundary"] == "turn-1:step-end:precombat_main"
    assert (
        snapshot["authoritative_state_fingerprint_preimage"]["floating_mana_ledger"]
        == game.floating_mana.fingerprint_state()
    )
    assert snapshot["authoritative_state_fingerprint"] != before

    game.transition_to(TurnStep.BEGINNING_OF_COMBAT)
    after_expiration = game.snapshot()["floating_mana_ledger"]["players"][0]
    expired_production = after_expiration["productions"][0]
    assert expired_production["remaining_quantity"] == 0
    assert expired_production["valid"] is False
    assert after_expiration["expirations"][0]["production_event_id"] == ability.object_id
