"""Native-envelope, frozen-callable and evidence-failure tests; never plays a game."""

import ast
import copy
import functools
from pathlib import Path
from unittest.mock import Mock

import pytest
from fresh900_native_fixtures import native_snapshot, reconciliation

from tmnt_design_studio import fresh900_live as live
from tmnt_design_studio import fresh900_native as native
from tmnt_design_studio import smoke01, stage002
from tmnt_design_studio.fresh900_identity import FreshRefused

ROOT = Path(__file__).resolve().parents[1]
GIT = "C:/Program Files/Git/cmd/git.exe" if __import__("os").name == "nt" else "git"


def spec():
    return stage002.GameSpec(
        "audit-game",
        "audit-pair",
        1000000,
        "candidate_first",
        (stage002.DeckSpec("a", ""), stage002.DeckSpec("b", "")),
    )


def test_envelope_tracks_every_frozen_snapshot_field():
    tree = ast.parse((ROOT / "src/tmnt_design_studio/engine07.py").read_text())
    game = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Game")
    snapshot = next(n for n in game.body if isinstance(n, ast.FunctionDef) and n.name == "snapshot")
    result = next(n.value for n in snapshot.body if isinstance(n, ast.Return))
    assert {n.value for n in result.keys} | {"stage002_presence"} == native.REQUIRED_FIELDS


def test_complete_artificial_envelope_and_real_frozen_reconciler():
    value = native_snapshot(spec())
    before = copy.deepcopy(value)
    native.validate_native(value, spec())
    report = stage002.reconcile_snapshot(spec(), value, {"decks": []})
    native.validate_reconciliation(value, spec(), report)
    assert value == before


@pytest.mark.parametrize("field", sorted(native.REQUIRED_FIELDS))
def test_each_missing_native_field_refused(field):
    value = native_snapshot(spec())
    del value[field]
    with pytest.raises(FreshRefused):
        native.validate_native(value, spec())


@pytest.mark.parametrize(
    "case",
    [
        "digest",
        "winner",
        "participant",
        "life",
        "zone",
        "rng-tail",
        "rng-chain",
        "rng-seed",
        "turn",
        "active",
        "stack",
    ],
)
def test_native_authority_disagreements_refused(case):
    value = native_snapshot(spec())
    authority = value["authoritative_state_fingerprint_preimage"]
    if case == "digest":
        value["authoritative_state_fingerprint"] = "0" * 64
    elif case == "winner":
        authority["winner_index"] = 1
    elif case == "participant":
        value["players"][0]["name"] = "foreign"
    elif case == "life":
        value["players"][1]["life"] = 5
    elif case == "zone":
        value["players"][0]["library_object_ids"] = ["substituted"]
    elif case == "rng-tail":
        value["rng"]["state_digest"] = "b" * 64
    elif case == "rng-chain":
        value["rng"]["records"][0]["state_before"] = "b" * 64
    elif case == "rng-seed":
        value["rng"]["seed"] = 1000001
    elif case == "turn":
        authority["turn"] = 11
    elif case == "active":
        authority["active_player_index"] = 1
    elif case == "stack":
        authority["stack_object_ids"] = ["missing-stack-object"]
    original = copy.deepcopy(value)
    with pytest.raises(FreshRefused):
        native.validate_native(value, spec())
    assert value == original


@pytest.mark.parametrize(
    "field,value",
    [
        ("winner", "b"),
        ("seed", -1),
        ("orientation", "opponent_first"),
        ("seats", ["b", "a"]),
        ("turn", 11),
        ("rng_state_digest", "b" * 64),
    ],
)
def test_reconciler_identity_cannot_override_native(field, value):
    raw = native_snapshot(spec())
    report = reconciliation(spec(), raw, {})
    report[field] = value
    with pytest.raises(FreshRefused):
        native.validate_reconciliation(raw, spec(), report)


def test_reconciliation_must_retain_native_evidence():
    raw = native_snapshot(spec())
    report = reconciliation(spec(), raw, {})
    report["authoritative_evidence"]["events"] = []
    with pytest.raises(FreshRefused, match="evidence conflict"):
        native.validate_reconciliation(raw, spec(), report)


@pytest.mark.parametrize("kind", ["mock", "wrapped", "code", "defaults", "origin"])
def test_real_binding_rejects_substitution_without_invocation(monkeypatch, kind):
    original = smoke01.run_smoke_game
    assert live._bind_executor(smoke01, ROOT, GIT) is original  # Identity only, no call.
    if kind == "mock":
        replacement = Mock()
        monkeypatch.setattr(smoke01, "run_smoke_game", replacement)
    elif kind == "wrapped":

        @functools.wraps(original)
        def replacement(*args, **kwargs):
            pytest.fail("wrapped gameplay must never run")

        monkeypatch.setattr(smoke01, "run_smoke_game", replacement)
    elif kind == "code":
        monkeypatch.setattr(
            original,
            "__code__",
            original.__code__.replace(
                co_consts=("altered frozen code", *original.__code__.co_consts[1:])
            ),
        )
    elif kind == "defaults":
        monkeypatch.setattr(original, "__defaults__", ("substitute pilot",))
    else:
        monkeypatch.setattr(original, "__code__", original.__code__.replace(co_filename=__file__))
    with pytest.raises(FreshRefused):
        live._bind_executor(smoke01, ROOT, GIT)
    if kind == "mock":
        replacement.assert_not_called()


def test_copy_failure_retains_primary_and_available_reference():
    class BrokenCopy(dict):
        def __deepcopy__(self, memo):
            raise ValueError("copy failure")

    primary = RuntimeError("initiating gameplay error")
    primary.snapshot = BrokenCopy(events=[{"partial": "retained"}])
    wrapped = live.AdapterGameFailure(primary)
    assert str(wrapped) == str(primary)
    assert wrapped.original_error_type == "RuntimeError"
    assert wrapped.partial_snapshot is primary.snapshot
    assert wrapped.snapshot_capture_state == "REFERENCE_ONLY_COPY_FAILED"
    assert wrapped.cleanup_failures[0][0] == "SNAPSHOT_COPY"


def test_five_original_predicate_bodies_execute_from_preserved_source():
    import test_fresh900_live_audit as audit

    for name in (
        "test_missing_native_players_cannot_complete",
        "test_conflicting_native_fingerprint_winner_cannot_complete",
        "test_replaced_executor_is_detected_before_invocation",
        "test_snapshot_capture_failure_does_not_mask_original",
        "test_full_900_identity_does_not_accept_first_incomplete_native_result",
    ):
        assert getattr(audit, name).__code__.co_filename == str(audit.ORIGINAL)
