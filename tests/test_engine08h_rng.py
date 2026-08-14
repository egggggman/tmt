import inspect
import json
import random
from dataclasses import replace

import pytest

from tmnt_design_studio import engine07
from tmnt_design_studio.engine07 import CardFact, DeterministicRNG, Game

PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")


def test_service_preserves_exact_legacy_shuffle_algorithm_and_state_continuity():
    first = list(range(20))
    second = list(range(15))
    legacy = random.Random(9001)
    expected_first = list(first)
    expected_second = list(second)
    legacy.shuffle(expected_first)
    legacy.shuffle(expected_second)
    service = DeterministicRNG(9001)

    assert service.shuffled(first, domain="first") == expected_first
    assert service.shuffled(second, domain="second") == expected_second
    assert service.export_state() == legacy.getstate()


def test_every_consumption_has_sequence_domain_result_and_chained_state_evidence():
    service = DeterministicRNG(7)
    service.shuffled(list(range(5)), domain="opening_library:0")
    result = service.randrange(100, domain="future_casey_jones_choice")

    assert [record.sequence for record in service.records] == [1, 2]
    assert [record.domain for record in service.records] == [
        "opening_library:0",
        "future_casey_jones_choice",
    ]
    assert service.records[1].result == result
    assert service.records[0].state_after == service.records[1].state_before
    assert service.records[-1].state_after == service.state_digest


def test_exported_state_is_json_serializable_and_restores_exact_future_results():
    original = DeterministicRNG(11)
    original.randrange(10, domain="before_export")
    state = original.export_state()
    serialized_state = json.loads(json.dumps(state))
    restored = DeterministicRNG(999)
    restored.restore_state(serialized_state)

    assert restored.records == []
    assert restored.state_digest == original.state_digest
    assert restored.randrange(10_000, domain="after_restore") == original.randrange(
        10_000, domain="after_export"
    )
    assert restored.state_digest == original.state_digest


def test_invalid_state_and_unscoped_consumption_are_rejected_without_consumption():
    service = DeterministicRNG(12)
    before = service.state_digest

    with pytest.raises(ValueError, match="domain"):
        service.shuffled([1, 2], domain="")
    with pytest.raises(ValueError, match="positive bound"):
        service.randrange(0, domain="bad")
    with pytest.raises(ValueError, match="invalid"):
        service.restore_state((1, 2))

    assert service.state_digest == before
    assert service.records == []


def test_game_retains_two_opening_shuffle_records_and_serializes_rng_evidence():
    deck = [PLAINS] * 60
    first = Game((deck, deck), seed=13)
    second = Game((deck, deck), seed=13)

    assert first.rng.records == second.rng.records
    assert [record.domain for record in first.rng.records] == [
        "opening_library:0",
        "opening_library:1",
    ]
    assert json.dumps(first.snapshot(), sort_keys=True) == json.dumps(
        second.snapshot(), sort_keys=True
    )
    first.check_invariants()


def test_rng_ledger_tampering_fails_invariants_and_random_is_encapsulated():
    deck = [PLAINS] * 60
    current = Game((deck, deck), seed=14)
    current.rng.records[1] = replace(current.rng.records[1], sequence=99)
    with pytest.raises(AssertionError, match="sequence"):
        current.check_invariants()

    source = inspect.getsource(engine07)
    assert source.count("random.Random(") == 1
