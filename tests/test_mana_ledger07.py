import pytest

from tmnt_design_studio.mana_ledger07 import FloatingManaLedger


def test_production_and_exact_lineage_consumption():
    ledger = FloatingManaLedger()
    ledger.add(0, "frog-1", "G", 1, "mana-event-1")
    ledger.add(0, "frog-1", "U", 1, "mana-event-2")
    assert ledger.snapshot(0) == {"G": 1, "U": 1}
    consumed = ledger.consume(0, "U", 1, "payment-1")
    assert consumed.source_event_id == "mana-event-2"
    assert ledger.snapshot(0) == {"G": 1}


def test_invalid_or_duplicate_consumption_fails_closed():
    ledger = FloatingManaLedger()
    ledger.add(0, "source", "R", 1, "event")
    ledger.consume(0, "R", 1, "payment")
    with pytest.raises(ValueError):
        ledger.consume(0, "R", 1, "payment")
    with pytest.raises(ValueError):
        ledger.add(0, "source", "X", 1, "bad")


def test_unused_mana_empties_deterministically():
    ledger = FloatingManaLedger()
    ledger.add(1, "source", "C", 2, "event")
    ledger.empty(1)
    assert ledger.snapshot(1) == {}
    assert ledger.productions(1)[0].event_id == "event"
