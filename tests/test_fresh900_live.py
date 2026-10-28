"""Mock-only adapter tests. The actual gameplay entrypoint is never called."""

from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fresh900_native_fixtures import native_snapshot, reconciliation
from test_fresh900_independent import execute, rows
from test_fresh900_independent import fixture as fixture

from tmnt_design_studio import fresh900 as persistence
from tmnt_design_studio import fresh900_live as live
from tmnt_design_studio.fresh900_identity import FreshRefused, digest

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Deck:
    display_id: str
    relative_path: str


@dataclass(frozen=True)
class Spec:
    game_id: str
    pairing_id: str
    seed: int
    orientation: str
    seats: tuple


@pytest.fixture
def boundary(fixture, monkeypatch):
    plan = fixture
    plan["runtime"]["git_executable"] = "mock-binding-only"
    for row in plan["schedule"]:
        row["opponent"] = "opponent"
        row["seats"] = (
            ["bad_guys_cronies_sandbox_0_2", "opponent"]
            if row["orientation"] == "candidate_first"
            else ["opponent", "bad_guys_cronies_sandbox_0_2"]
        )
    approved_schedule = copy.deepcopy(plan["schedule"])

    def verify(p):
        assert p["schedule"] == approved_schedule

    monkeypatch.setattr(persistence, "verify_plan", verify)
    source = Path(plan["runtime"]["source"])
    manifest = source / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"decks": [{"deck_key": "opponent", "source_path": "approved-opponent.txt"}]})
    )
    calls = []

    def game(root, spec):
        calls.append(spec)
        row = next(r for r in plan["schedule"] if r["game_id"] == spec.game_id)
        assert row["seats"] == [seat.display_id for seat in spec.seats]
        return native_snapshot(spec)

    smoke = SimpleNamespace(
        __file__=str(source / "src/tmnt_design_studio/smoke01.py"),
        run_smoke_game=Mock(side_effect=game),
    )
    stage = SimpleNamespace(
        __file__=str(source / "src/tmnt_design_studio/stage002.py"),
        DeckSpec=Deck,
        GameSpec=Spec,
        load_catalog=Mock(return_value="mock catalog"),
        build_deck_manifest=Mock(return_value={"cards": []}),
        reconcile_snapshot=Mock(side_effect=reconciliation),
    )
    # Boundary fixture explicitly replaces attestation/source roles. Separate
    # frozen-source/runtime checks are tested independently without these seams.
    monkeypatch.setattr(live, "authenticate_source", lambda _: None)
    monkeypatch.setattr(live, "bindings", lambda: (smoke, stage, lambda _: "Deck\n60 Mock Card\n"))
    # Explicit unit-test-only binding seam. Actual binding rejection is separately
    # exercised with the real verifier; production has no mock/executor argument.
    monkeypatch.setattr(live, "_bind_executor", lambda *_: smoke.run_smoke_game)
    monkeypatch.setattr(live, "plain", lambda p: Path(p).absolute())
    monkeypatch.setattr(live, "sys", SimpleNamespace(version_info=(3, 13, 15)))
    monkeypatch.setattr(
        persistence, "resources", lambda: dict(physical=8 * 2**30, commit=8 * 2**30)
    )
    approval = dict(
        action="fresh900-live-execution",
        approved_by="MOCK ISSUER ONLY",
        plan_sha256=digest(plan),
        independent_review_sha256="1" * 64,
        design_approval_sha256="2" * 64,
        preflight_sha256="3" * 64,
    )
    return plan, approval, smoke, stage, calls


def run(boundary):
    plan, approval, *_ = boundary
    return live.run_authorized_live(plan, approval, expected_authorization_sha256=digest(approval))


def test_mock_mapping_and_all_telemetry_reach_checkpoint(boundary):
    plan, _, smoke, _, calls = boundary
    result = run(boundary)
    assert result["completed_games"] == 2 and result["synthetic"] is False
    assert smoke.run_smoke_game.call_count == 2
    for spec, row in zip(calls, rows(), strict=True):
        assert (spec.game_id, spec.pairing_id, spec.seed, spec.orientation) == (
            row["game_id"],
            row["pairing_id"],
            row["seed"],
            row["orientation"],
        )
        assert [s.display_id for s in spec.seats] == (
            ["bad_guys_cronies_sandbox_0_2", "opponent"]
            if row["orientation"] == "candidate_first"
            else ["opponent", "bad_guys_cronies_sandbox_0_2"]
        )
    saved = json.loads((Path(plan["output"]) / "checkpoints/checkpoint.json").read_bytes())
    for value in saved["records"]:
        assert value["events"] == [
            {
                "event": "AUDIT_SYNTHETIC",
                "kind": "synthetic",
                "value": 17,
                "turn": 10,
                "phase": "main",
                "step": "precombat_main",
            }
        ]
        assert value["rng"]["records"][0]["detail"] == "retain RNG evidence"
        assert value["native_extra"] == {"nested": [1, {"complete": "retain all"}]}
    with pytest.raises(FreshRefused, match="unused"):
        run(boundary)
    assert smoke.run_smoke_game.call_count == 2


@pytest.mark.parametrize(
    "field,value",
    [
        ("action", "synthetic-review"),
        ("approved_by", ""),
        ("plan_sha256", "f" * 64),
        ("design_approval_sha256", ""),
        ("preflight_sha256", ""),
        ("independent_review_sha256", ""),
    ],
)
def test_bad_authority_never_reserves_or_calls(boundary, field, value):
    plan, approval, smoke, *_ = boundary
    approval[field] = value
    with pytest.raises(FreshRefused):
        run(boundary)
    assert not Path(plan["output"]).exists()
    smoke.run_smoke_game.assert_not_called()


def test_wrong_independent_pin_never_calls(boundary):
    plan, approval, smoke, *_ = boundary
    with pytest.raises(FreshRefused, match="approval mismatch"):
        live.run_authorized_live(plan, approval, expected_authorization_sha256="f" * 64)
    assert not Path(plan["output"]).exists()
    smoke.run_smoke_game.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("seed", 123),
        ("terminal", False),
        ("winner", "foreign"),
        ("events", None),
        ("rng", {"seed": -1}),
        ("game_id", "foreign"),
    ],
)
def test_malformed_native_results_do_not_commit(boundary, field, value):
    plan, _, smoke, *_ = boundary
    original = smoke.run_smoke_game.side_effect

    def bad(root, spec):
        result = original(root, spec)
        result[field] = value
        return result

    smoke.run_smoke_game.side_effect = bad
    with pytest.raises((FreshRefused, live.AdapterGameFailure)):
        run(boundary)
    saved = json.loads((Path(plan["output"]) / "checkpoints/checkpoint.json").read_bytes())
    assert saved["completed_games"] == 0
    assert not (Path(plan["output"]) / "results/summary.json").exists()


def test_partial_snapshot_and_cause_survive(boundary):
    plan, _, smoke, *_ = boundary

    class FrozenFailure(RuntimeError):
        snapshot = {"events": [{"partial": "complete failure evidence"}]}

    original = FrozenFailure("mock engine failure")
    smoke.run_smoke_game.side_effect = original
    with pytest.raises(live.AdapterGameFailure) as caught:
        run(boundary)
    assert caught.value.__cause__ is original
    root = Path(plan["output"])
    assert json.loads((root / "failures/game-snapshot.json").read_bytes()) == original.snapshot
    stop = json.loads((root / "failures/stop.json").read_bytes())
    assert stop["original_error_type"] == "FrozenFailure"
    assert stop["checkpoint_integrity_verified"] is True


def test_resource_failure_never_calls(boundary, monkeypatch):
    plan, _, smoke, *_ = boundary
    monkeypatch.setattr(persistence, "resources", lambda: dict(physical=0, commit=0))
    with pytest.raises(FreshRefused, match="physical memory"):
        run(boundary)
    assert not Path(plan["output"]).exists()
    smoke.run_smoke_game.assert_not_called()


def test_interruption_stops_without_replay(boundary):
    plan, _, smoke, *_ = boundary
    smoke.run_smoke_game.side_effect = KeyboardInterrupt("mock interruption")
    with pytest.raises(KeyboardInterrupt):
        run(boundary)
    stop = json.loads((Path(plan["output"]) / "failures/stop.json").read_bytes())
    assert stop["error_type"] == "KeyboardInterrupt" and not stop["ownership_unresolved"]
    with pytest.raises(FreshRefused, match="unused"):
        run(boundary)


def test_runtime_failure_never_reserves(boundary, monkeypatch):
    plan, _, smoke, *_ = boundary

    def refuse(_):
        raise FreshRefused("mock runtime/input substitution")

    monkeypatch.setattr(persistence, "verify_plan", refuse)
    with pytest.raises(FreshRefused, match="runtime/input"):
        run(boundary)
    assert not Path(plan["output"]).exists()
    smoke.run_smoke_game.assert_not_called()


def test_nonapproved_python_refused(boundary, monkeypatch):
    plan, _, smoke, *_ = boundary
    monkeypatch.setattr(live, "sys", SimpleNamespace(version_info=(3, 12, 10)))
    with pytest.raises(FreshRefused, match="3.13.15"):
        run(boundary)
    assert not Path(plan["output"]).exists()
    smoke.run_smoke_game.assert_not_called()


def test_synthetic_api_still_rejects_live_action(fixture):
    with pytest.raises(FreshRefused, match="execution action"):
        execute(fixture, approval_change={"action": "fresh900-live-execution"})


def test_binding_is_frozen_without_executing_a_game():
    smoke, stage, candidate = live.bindings()
    assert smoke.run_smoke_game.__module__ == "tmnt_design_studio.smoke01"
    assert stage.GameSpec.__module__ == "tmnt_design_studio.stage002"
    assert candidate.__name__ == "_candidate_text"
    assert sys.version_info >= (3, 12)


def test_all_900_schedule_rows_map_exactly_without_gameplay(tmp_path):
    from test_fresh900 import schedule

    stage = SimpleNamespace(DeckSpec=Deck, GameSpec=Spec)
    for row in schedule():
        spec = live.game_spec(stage, row, tmp_path / "candidate.txt", "opponent.txt")
        assert spec.game_id == row["game_id"] and spec.seed == row["seed"]
        assert spec.pairing_id == row["pairing_id"] and spec.orientation == row["orientation"]
        assert [s.display_id for s in spec.seats] == row["seats"]


def test_competing_writer_cannot_enter_during_mock_game(boundary):
    from tmnt_design_studio.calibration_integrity import CheckpointIntegrityError, WriterLock

    plan, _, smoke, *_ = boundary

    def competing(*_):
        with WriterLock(Path(plan["output"]) / "checkpoints/checkpoint.json", "competitor"):
            pytest.fail("competing writer entered")

    smoke.run_smoke_game.side_effect = competing
    with pytest.raises(live.AdapterGameFailure) as caught:
        run(boundary)
    assert isinstance(caught.value.__cause__, CheckpointIntegrityError)
    saved = json.loads((Path(plan["output"]) / "checkpoints/checkpoint.json").read_bytes())
    assert saved["completed_games"] == 0


def test_partial_evidence_write_error_does_not_mask_game_failure(boundary, monkeypatch):
    plan, _, smoke, *_ = boundary

    class Failure(RuntimeError):
        snapshot = {"partial": "keep"}

    original = Failure("initiating mock failure")
    smoke.run_smoke_game.side_effect = original
    atomic = persistence.atomic_json

    def denied(path, value):
        if path.name == "game-snapshot.json":
            raise PermissionError("mock partial publication denial")
        return atomic(path, value)

    monkeypatch.setattr(persistence, "atomic_json", denied)
    with pytest.raises(live.AdapterGameFailure) as caught:
        run(boundary)
    assert caught.value.__cause__ is original
    assert caught.value.partial_snapshot == original.snapshot
    stop = json.loads((Path(plan["output"]) / "failures/stop.json").read_bytes())
    assert stop["cleanup_failures"][0]["stage"] == "PARTIAL_GAME_EVIDENCE"
    assert stop["resources_unresolved"] is True


def test_frozen_game_failure_can_be_reported_without_mutation(boundary):
    from tmnt_design_studio.smoke01 import SmokeGameFailure

    plan, _, smoke, *_ = boundary
    snapshot = {"events": [{"complete": "immutable exception evidence"}]}
    failure = SmokeGameFailure("frozen mock failure", snapshot)
    smoke.run_smoke_game.side_effect = failure
    with pytest.raises(live.AdapterGameFailure) as caught:
        run(boundary)
    assert caught.value.__cause__ is failure
    saved = json.loads((Path(plan["output"]) / "failures/game-snapshot.json").read_bytes())
    assert saved == snapshot


def test_frozen_source_rejects_unreviewed_paths_without_gameplay(monkeypatch):
    monkeypatch.setattr(
        live.subprocess, "check_output", lambda *a, **k: "src/tmnt_design_studio/engine07.py\n"
    )
    plan = {"runtime": {"source": str(ROOT), "git_executable": "git", "source_commit": "fake"}}
    with pytest.raises(FreshRefused, match="frozen gameplay source differs"):
        live.authenticate_source(plan)
