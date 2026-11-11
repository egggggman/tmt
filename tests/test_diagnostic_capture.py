from __future__ import annotations

import copy
from pathlib import Path

import pytest

from tmnt_design_studio import stage002
from tmnt_design_studio.card_interpreter07 import TokenCreationProgram, TokenDefinition
from tmnt_design_studio.engine07 import CardFact, Game

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Capture fixture land", "", 0, "Basic Land — Plains", oracle_id="capture-land")
DRONE = TokenDefinition(
    "Capture Drone",
    "Artifact Creature — Robot",
    power=1,
    toughness=1,
    oracle_text="Vigilance",
    keywords=("Vigilance",),
)


def _game() -> Game:
    return Game(([LAND] * 60, [LAND] * 60), seed=4408)


def test_nested_failure_uses_explicit_runner_binding_not_innermost_game_local():
    game = _game()
    presence: list[dict[str, object]] = []
    capture = stage002.DiagnosticExecutionCapture()
    original_fingerprint = game.authoritative_state_fingerprint()
    original_error = RuntimeError("injected nested diagnostic failure")

    def wrapper():
        game = object()
        _ = game

        def nested_action():
            game = object()
            _ = game
            raise original_error

        return nested_action()

    with pytest.raises(RuntimeError) as raised:
        stage002.capture_diagnostic_call(
            capture,
            lambda: (capture.bind(game, presence), wrapper())[1],
        )

    assert raised.value is original_error
    assert capture.failure is not None
    assert capture.failure["message"] == "injected nested diagnostic failure"
    assert "nested_action" in capture.failure["traceback"]
    snapshot = capture.failure["snapshot"]
    assert isinstance(snapshot, dict)
    assert snapshot["authoritative_state_fingerprint"] == original_fingerprint
    assert snapshot["stage002_presence"] == []


def test_run_game_exception_capture_preserves_presence_and_authenticates_token(
    monkeypatch,
):
    capture = stage002.DiagnosticExecutionCapture()
    bound_game: Game | None = None
    live_presence: list[dict[str, object]] | None = None
    original_presence: list[dict[str, object]] | None = None
    injected = RuntimeError("injected after runner state binding")

    def fail_after_token_creation(game, _pilot):
        nonlocal bound_game, live_presence, original_presence
        bound_game = game
        assert capture._presence is not None
        live_presence = capture._presence
        original_presence = copy.deepcopy(capture._presence)
        game.create_tokens(
            0,
            TokenCreationProgram(DRONE, 1),
            source_card="Diagnostic capture fixture",
            source_id=game.players[0].library[0].object_id,
            oracle_fragment="Create a Capture Drone.",
        )
        raise injected

    monkeypatch.setattr(stage002, "_wire_damage_target_chooser", fail_after_token_creation)
    spec = stage002.stage_games()[0]

    with pytest.raises(RuntimeError) as raised:
        stage002.capture_diagnostic_call(
            capture,
            lambda: stage002.run_game(
                ROOT,
                spec,
                diagnostic_capture=capture,
            ),
        )

    assert raised.value is injected
    assert capture.failure is not None
    assert capture.failure["type"] == "RuntimeError"
    assert "injected after runner state binding" in capture.failure["traceback"]
    snapshot = capture.failure["snapshot"]
    assert isinstance(snapshot, dict)
    assert bound_game is not None
    assert live_presence is not None
    assert original_presence is not None
    assert live_presence == original_presence
    assert snapshot["authoritative_state_fingerprint"] == (
        bound_game.authoritative_state_fingerprint()
    )
    token_rows = [row for row in snapshot["stage002_presence"] if row["card"] == DRONE.name]
    assert len(token_rows) == 1
    token_event = next(event for event in snapshot["events"] if event["event"] == "tokens_created")
    assert token_rows[0]["creation_event_id"] == token_event["event_id"]
    assert token_rows[0]["creation_source_id"] == token_event["source_id"]
    original_ids = {row["initial_object_id"] for row in original_presence}
    captured_original_rows = [
        row for row in snapshot["stage002_presence"] if row["initial_object_id"] in original_ids
    ]
    assert {row["initial_object_id"] for row in captured_original_rows} == original_ids

    execution_index = stage002._authoritative_execution_index(snapshot)
    assert execution_index[("tokens_created", token_event["event_id"])] == [
        {
            "source_id": token_event["source_id"],
            "oracle_fragment": "Create a Capture Drone.",
        }
    ]
    report = stage002.reconcile_snapshot(spec, snapshot, stage002.build_stage_manifest(ROOT))
    assert report["stop_records"] == []
    assert any(row["semantic_key"] == token_rows[0]["semantic_key"] for row in report["presence"])


def test_missing_or_ambiguous_runner_binding_fails_closed_without_hiding_error():
    error = RuntimeError("original failure")
    missing = stage002.DiagnosticExecutionCapture()

    with pytest.raises(RuntimeError) as raised:
        stage002.capture_diagnostic_call(missing, lambda: (_ for _ in ()).throw(error))

    assert raised.value is error
    assert missing.failure is not None
    assert missing.failure["snapshot"] is None
    assert missing.failure["capture_error"] == "diagnostic runner state was not bound"
    assert "original failure" in missing.failure["traceback"]

    game = _game()
    ambiguous = stage002.DiagnosticExecutionCapture()
    first_presence: list[dict[str, object]] = []
    second_presence: list[dict[str, object]] = []

    with pytest.raises(RuntimeError) as ambiguous_raised:
        stage002.capture_diagnostic_call(
            ambiguous,
            lambda: (
                ambiguous.bind(game, first_presence),
                ambiguous.bind(game, second_presence),
            ),
        )

    assert str(ambiguous_raised.value) == "diagnostic runner state was bound more than once"
    assert ambiguous.failure is not None
    assert ambiguous.failure["snapshot"] is None
    assert ambiguous.failure["capture_error"] == (
        "diagnostic runner state was bound more than once"
    )
    assert first_presence == []
    assert second_presence == []


def test_capture_finalizes_a_copy_of_presence_without_mutating_live_ledger():
    game = _game()
    game.create_tokens(
        0,
        TokenCreationProgram(DRONE, 1),
        source_card="Diagnostic capture fixture",
        oracle_fragment="Create a Capture Drone.",
    )
    presence: list[dict[str, object]] = []
    capture = stage002.DiagnosticExecutionCapture()
    original_presence = copy.deepcopy(presence)

    with pytest.raises(RuntimeError):

        def fail_after_binding():
            capture.bind(game, presence)
            raise RuntimeError("capture now")

        stage002.capture_diagnostic_call(capture, fail_after_binding)

    assert presence == original_presence
    assert capture.failure is not None
    assert len(capture.failure["snapshot"]["stage002_presence"]) == 1


def test_reused_capture_does_not_attach_previous_game_to_unbound_failure():
    previous_game = _game()
    capture = stage002.DiagnosticExecutionCapture()

    with pytest.raises(RuntimeError, match="first execution failed"):

        def first_failure():
            capture.bind(previous_game, [])
            raise RuntimeError("first execution failed")

        stage002.capture_diagnostic_call(capture, first_failure)
    assert capture.failure is not None
    assert capture.failure["snapshot"] is not None

    with pytest.raises(RuntimeError, match="failure before a new binding"):
        stage002.capture_diagnostic_call(
            capture,
            lambda: (_ for _ in ()).throw(RuntimeError("failure before a new binding")),
        )

    assert capture.failure is not None
    assert capture.failure["snapshot"] is None
    assert capture.failure["capture_error"] == "diagnostic runner state was not bound"


def test_unprintable_snapshot_capture_error_does_not_mask_original_exception():
    class UnprintableSnapshotError(RuntimeError):
        def __str__(self):
            raise RuntimeError("snapshot error formatting failed")

    game = _game()
    capture = stage002.DiagnosticExecutionCapture()
    game.snapshot = lambda: (_ for _ in ()).throw(UnprintableSnapshotError())
    original = ValueError("original diagnostic execution error")

    with pytest.raises(ValueError) as raised:

        def snapshot_failure():
            capture.bind(game, [])
            raise original

        stage002.capture_diagnostic_call(capture, snapshot_failure)

    assert raised.value is original
    assert capture.failure is not None
    assert capture.failure["snapshot"] is None
    assert "UnprintableSnapshotError" in capture.failure["capture_error"]


def test_non_game_success_after_failure_clears_stale_failure_and_binding():
    game = _game()
    capture = stage002.DiagnosticExecutionCapture()

    def first_execution():
        capture.bind(game, [])
        raise RuntimeError("first run failed")

    with pytest.raises(RuntimeError, match="first run failed"):
        stage002.capture_diagnostic_call(capture, first_execution)
    assert capture.failure is not None
    assert capture.failure["snapshot"] is not None

    marker = object()
    result = stage002.capture_diagnostic_call(capture, lambda: marker)

    assert result is marker
    assert capture.failure is None
    assert capture._game is None
    assert capture._presence is None


def test_run_game_without_capture_preserves_setup_exception(monkeypatch):
    original = RuntimeError("legacy runner setup exception")

    def fail_before_gameplay_loop(_game, _pilot):
        raise original

    monkeypatch.setattr(stage002, "_wire_damage_target_chooser", fail_before_gameplay_loop)

    with pytest.raises(RuntimeError) as raised:
        stage002.run_game(ROOT, stage002.stage_games()[0])

    assert raised.value is original


def test_presence_finalization_and_traceback_format_failures_keep_original_exception(
    monkeypatch,
):
    class UnprintableFinalizationError(RuntimeError):
        def __str__(self):
            raise RuntimeError("finalization formatting failed")

    game = _game()
    capture = stage002.DiagnosticExecutionCapture()
    original = ValueError("original execution failure")

    def fail_finalize(_presence, _events):
        raise UnprintableFinalizationError()

    monkeypatch.setattr(stage002, "_finish_presence", fail_finalize)

    def failing_operation():
        capture.bind(game, [])
        raise original

    with pytest.raises(ValueError) as raised:
        stage002.capture_diagnostic_call(capture, failing_operation)

    assert raised.value is original
    assert capture.failure is not None
    assert capture.failure["snapshot"] is None
    assert "UnprintableFinalizationError" in capture.failure["capture_error"]

    monkeypatch.undo()

    class UnprintableExecutionError(RuntimeError):
        def __str__(self):
            raise RuntimeError("execution formatting failed")

    capture2 = stage002.DiagnosticExecutionCapture()
    capture_error = UnprintableExecutionError()
    monkeypatch.setattr(
        stage002.traceback,
        "format_exception",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("traceback unavailable")),
    )

    def fail_traceback_format():
        capture2.bind(game, [])
        raise capture_error

    with pytest.raises(RuntimeError) as traceback_raised:
        stage002.capture_diagnostic_call(capture2, fail_traceback_format)

    assert traceback_raised.value is capture_error
    assert capture2.failure is not None
    assert capture2.failure["message"].startswith("<exception message unavailable:")
    assert capture2.failure["traceback"] == "<traceback unavailable>"
    assert isinstance(capture2.failure["snapshot"], dict)


def test_failure_inside_capture_bookkeeping_cannot_replace_execution_exception(
    monkeypatch,
):
    game = _game()
    capture = stage002.DiagnosticExecutionCapture()
    original = ValueError("authoritative execution failure")

    def fail_recording(_error):
        raise RuntimeError("capture bookkeeping failed")

    monkeypatch.setattr(capture, "capture_exception", fail_recording)

    def failing_operation():
        capture.bind(game, [])
        raise original

    with pytest.raises(ValueError) as raised:
        stage002.capture_diagnostic_call(capture, failing_operation)

    assert raised.value is original
    assert capture.failure is not None
    assert capture.failure["snapshot"] is None
    assert capture.failure["capture_error"] == "RuntimeError"
