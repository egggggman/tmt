"""Synthetic contracts for source-authenticated, context-restricted mana lots."""

from tmnt_design_studio.mana_ledger07 import FloatingManaLedger


def test_expiration_does_not_reuse_an_older_same_color_production_lot():
    ledger = FloatingManaLedger()
    ledger.add(0, "source-A", "R", 1, "production-A")
    ledger.empty(0)
    ledger.add(0, "source-B", "R", 1, "production-B")

    consumed = ledger.consume(0, "R", 1, "payment-1")

    assert consumed.source_event_id == "production-B"
