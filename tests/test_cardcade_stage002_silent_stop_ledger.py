import pytest

from tools.cardcade_stage002_silent_stop_ledger import reconciled_stop_sources


def test_raw_stops_keep_exact_indices_and_derived_stops_keep_distinct_identity():
    raw_stops = [
        {"kind": "silent_approximation", "detail": ["raw-a"]},
        {"kind": "silent_approximation", "detail": ["raw-b"]},
    ]
    derived_stop = {"kind": "silent_approximation", "detail": ["derived"]}

    sources = reconciled_stop_sources("run-1", raw_stops, [*raw_stops, derived_stop])

    assert sources == [
        ("run-1:snapshot.conformance.stop_records[0]", "/snapshot/conformance/stop_records/0"),
        ("run-1:snapshot.conformance.stop_records[1]", "/snapshot/conformance/stop_records/1"),
        ("run-1:frozen-reconciler-derived-stop:2", "/snapshot/conformance"),
    ]


def test_inserted_reconciler_stop_before_raw_suffix_is_rejected():
    raw_stops = [
        {"kind": "silent_approximation", "detail": ["raw-a"]},
        {"kind": "silent_approximation", "detail": ["raw-b"]},
    ]
    inserted = {"kind": "silent_approximation", "detail": ["derived"]}

    with pytest.raises(ValueError, match="raw snapshot prefix at index 1"):
        reconciled_stop_sources("run-1", raw_stops, [raw_stops[0], inserted, raw_stops[1]])


def test_reordered_reconciler_raw_stops_are_rejected():
    raw_stops = [
        {"kind": "silent_approximation", "detail": ["raw-a"]},
        {"kind": "silent_approximation", "detail": ["raw-b"]},
    ]

    with pytest.raises(ValueError, match="raw snapshot prefix at index 0"):
        reconciled_stop_sources("run-1", raw_stops, list(reversed(raw_stops)))


def test_omitted_reconciler_raw_stop_is_rejected():
    raw_stops = [
        {"kind": "silent_approximation", "detail": ["raw-a"]},
        {"kind": "silent_approximation", "detail": ["raw-b"]},
    ]

    with pytest.raises(ValueError, match="omitted raw snapshot stop records"):
        reconciled_stop_sources("run-1", raw_stops, raw_stops[:1])
