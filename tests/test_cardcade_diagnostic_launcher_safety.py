from __future__ import annotations

import hashlib
import json
import multiprocessing
import subprocess
import uuid
from pathlib import Path

import pytest
from cardcade_auth_test_support import install_test_trust_anchor, signed_document

from tools import cardcade_diagnostic_launcher as launcher_module
from tools.cardcade_diagnostic_launcher import (
    APPROVED_INPUT_SHA256,
    RUN_AUTHORIZATION_SCHEMA,
    SOURCE_APPROVAL_SCHEMA,
    DiagnosticLauncherError,
    OneShotDiagnosticLauncher,
    stage002,
)

ROOT = Path(__file__).resolve().parents[1]
PRE_TEST_DESCENDANT = "5cf4a0c6cd631ddeac9dbf8123a4197c25bac66f"
ACCEPTED_MAIN = "10d2ac80ef5b81b3a209a3133eb0a84633a1f944"


def _launcher(
    tmp_path: Path,
    label: str,
    *,
    authorization_id: str | None = None,
    implementation_sha: str | None = None,
    input_hashes: dict[str, str] | None = None,
) -> OneShotDiagnosticLauncher:
    install_test_trust_anchor(launcher_module)
    output_root = ROOT / ".cardcade-diagnostic-runs"
    output_root.mkdir(exist_ok=True)
    invocation_nonce = uuid.uuid4().hex
    output = (
        output_root / f"diagnostic-game-safety-{tmp_path.parent.name}-{label}-{invocation_nonce}"
    )
    approved_sha = (
        implementation_sha
        or subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    )
    run_suffix = hashlib.sha256(
        f"{tmp_path.parent.name}-{label}-{invocation_nonce}".encode()
    ).hexdigest()[:16]
    run_id = authorization_id or f"SYNTHETIC-{run_suffix}"
    approval_id = f"HQ-SYNTHETIC-{run_id}"
    hashes = dict(input_hashes or APPROVED_INPUT_SHA256)
    approval_path = tmp_path / f"source-approval-{label}.json"
    authorization_path = tmp_path / f"run-authorization-{label}.json"
    approval_path.write_text(
        json.dumps(
            signed_document(
                {
                    "schema": SOURCE_APPROVAL_SCHEMA,
                    "approval_id": approval_id,
                    "implementation_sha": approved_sha,
                    "input_sha256": hashes,
                }
            )
        ),
        encoding="utf-8",
    )
    authorization_path.write_text(
        json.dumps(
            signed_document(
                {
                    "schema": RUN_AUTHORIZATION_SCHEMA,
                    "authorization_id": run_id,
                    "source_approval_id": approval_id,
                    "implementation_sha": approved_sha,
                    "input_sha256": hashes,
                    "game_id": "april-casey:canonical:7231",
                    "pairing_id": "april-casey",
                    "orientation": "canonical",
                    "seed": 7231,
                }
            )
        ),
        encoding="utf-8",
    )
    return OneShotDiagnosticLauncher(
        ROOT,
        output,
        source_approval_path=approval_path,
        run_authorization_path=authorization_path,
    )


def _synthetic_executor(root, spec, *, diagnostic_capture):
    """Create initial engine state and snapshot it without running gameplay."""
    catalog = stage002.load_catalog(root)
    paths = tuple(root / seat.relative_path for seat in spec.seats)
    names = {name for path in paths for _count, name in stage002._deck_rows(path)}
    facts = stage002.load_facts(catalog, names)
    game = stage002.Game(
        (stage002.load_deck(paths[0], facts), stage002.load_deck(paths[1], facts)),
        names=tuple(seat.display_id for seat in spec.seats),
        seed=spec.seed,
    )
    presence = stage002._initial_presence(game)
    diagnostic_capture.bind(game, presence)
    snapshot = game.snapshot()
    stage002._add_created_token_presence(game, presence, snapshot["events"])
    snapshot["stage002_presence"] = stage002._finish_presence(presence, snapshot["events"])
    return snapshot


def _claim_worker(root, output, approval_path, authorization_path, source, barrier, queue):
    launcher = OneShotDiagnosticLauncher(
        Path(root),
        Path(output),
        source_approval_path=Path(approval_path),
        run_authorization_path=Path(authorization_path),
    )
    barrier.wait(timeout=15)
    try:
        claim = launcher._claim_authorization(source)
    except DiagnosticLauncherError:
        queue.put("consumed")
    else:
        queue.put(f"claimed:{claim.name}")


def test_exact_source_pin_rejects_approved_ancestor_descendant(tmp_path):
    launcher = _launcher(
        tmp_path,
        "wrong-source",
        implementation_sha=PRE_TEST_DESCENDANT,
    )
    with pytest.raises(
        DiagnosticLauncherError, match="does not equal exact approved implementation"
    ):
        launcher._verify_source()


def test_source_approval_and_run_authorization_are_separate_exact_records(tmp_path):
    launcher = _launcher(tmp_path, "exact-source")
    source = launcher._verify_source()
    assert source["head"] == source["source_approval"]["implementation_sha"]
    assert source["head"] == source["run_authorization"]["implementation_sha"]
    assert (
        source["run_authorization"]["source_approval_id"]
        == source["source_approval"]["approval_id"]
    )


def test_unapproved_frozen_input_hash_fails_before_executor_call(tmp_path):
    modified = dict(APPROVED_INPUT_SHA256)
    modified["decks/april_oneil/PROTOTYPE_0.1.txt"] = "0" * 64
    launcher = _launcher(tmp_path, "wrong-input", input_hashes=modified)
    calls = 0

    def executor(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("input mismatch must stop before dispatch")

    with pytest.raises(DiagnosticLauncherError, match="approved input hashes"):
        launcher.run_once(executor=executor)
    assert calls == launcher._run_game_call_count == 0
    assert not launcher.output_directory.exists()


def test_cross_process_authorization_claim_is_exclusive(tmp_path):
    authorization_id = f"CROSS-PROCESS-{uuid.uuid4().hex}"
    launcher = _launcher(tmp_path, "cross-process", authorization_id=authorization_id)
    source = launcher._verify_source()
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(2)
    queue = context.Queue()
    outputs = [
        str(launcher.output_directory.with_name(f"diagnostic-game-process-{index}"))
        for index in range(2)
    ]
    processes = [
        context.Process(
            target=_claim_worker,
            args=(
                str(ROOT),
                outputs[index],
                str(launcher.source_approval_path),
                str(launcher.run_authorization_path),
                source,
                barrier,
                queue,
            ),
        )
        for index in range(2)
    ]
    for process in processes:
        process.start()
    outcomes = [queue.get(timeout=20) for _ in processes]
    for process in processes:
        process.join(timeout=20)
        assert process.exitcode == 0

    assert sum(outcome.startswith("claimed:") for outcome in outcomes) == 1
    assert outcomes.count("consumed") == 1


def test_claim_survives_execution_failure_and_blocks_fresh_instance(tmp_path):
    authorization_id = f"FAILED-EXECUTION-{uuid.uuid4().hex}"
    first = _launcher(tmp_path, "failed-first", authorization_id=authorization_id)
    second = _launcher(tmp_path, "failed-second", authorization_id=authorization_id)
    calls = 0
    original = RuntimeError("injected synthetic failure")

    def executor(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise original

    with pytest.raises(RuntimeError) as raised:
        first.run_once(executor=executor)
    assert raised.value is original
    with pytest.raises(DiagnosticLauncherError, match="authorization already consumed"):
        second.run_once(executor=executor)
    assert calls == 1
    claim_directory = ROOT.parent / ".cardcade-diagnostic-claims"
    assert any(claim_directory.glob("*.json"))


def test_failed_reconciliation_persists_evidence_and_blocks_cli(monkeypatch, tmp_path):
    authorization_id = f"FAILED-RECONCILIATION-{uuid.uuid4().hex}"
    launcher = _launcher(tmp_path, "reconcile-failure", authorization_id=authorization_id)
    second = _launcher(tmp_path, "reconcile-failure-repeat", authorization_id=authorization_id)
    calls = 0

    def executor(*args, **kwargs):
        nonlocal calls
        calls += 1
        return _synthetic_executor(*args, **kwargs)

    monkeypatch.setattr(stage002, "run_game", executor)
    monkeypatch.setattr(
        stage002,
        "reconcile_snapshot",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("injected reconciliation error")
        ),
    )

    exit_code = launcher_module.main(
        [
            "--output-directory",
            str(launcher.output_directory),
            "--source-approval",
            str(launcher.source_approval_path),
            "--run-authorization",
            str(launcher.run_authorization_path),
        ]
    )

    assert exit_code != 0
    assert (launcher.output_directory / "snapshot.json").is_file()
    assert (launcher.output_directory / "reconciliation_error.json").is_file()
    status = json.loads((launcher.output_directory / "run_status.json").read_text(encoding="utf-8"))
    assert status["diagnostic_status"] == "BLOCKED"
    assert "reconciliation_failed" in status["blocking_findings"]
    assert status["run_game_call_count"] == 1
    with pytest.raises(DiagnosticLauncherError, match="authorization already consumed"):
        second.run_once(executor=executor)
    assert calls == 1


@pytest.mark.parametrize(
    ("reconciliation", "finding"),
    [
        (
            {"stop_records": [{"kind": "silent_approximation"}], "invariant_violations": []},
            "blocking_reconciliation_stop_records",
        ),
        (
            {"stop_records": [], "invariant_violations": [{"event_id": "synthetic-invariant"}]},
            "reconciliation_invariant_violations",
        ),
    ],
)
def test_blocking_reconciliation_findings_produce_blocked_status(
    monkeypatch, tmp_path, reconciliation, finding
):
    launcher = _launcher(tmp_path, f"blocking-{finding}")
    monkeypatch.setattr(stage002, "reconcile_snapshot", lambda *_args, **_kwargs: reconciliation)

    with pytest.raises(DiagnosticLauncherError, match=finding):
        launcher.run_once(executor=_synthetic_executor)
    status = json.loads((launcher.output_directory / "run_status.json").read_text(encoding="utf-8"))
    assert status["diagnostic_status"] == "BLOCKED"
    assert finding in status["blocking_findings"]


def test_missing_reconciliation_report_is_not_accepted(monkeypatch, tmp_path):
    launcher = _launcher(tmp_path, "missing-reconciliation")
    monkeypatch.setattr(stage002, "reconcile_snapshot", lambda *_args, **_kwargs: None)

    with pytest.raises(DiagnosticLauncherError, match="reconciliation_missing"):
        launcher.run_once(executor=_synthetic_executor)
    status = json.loads((launcher.output_directory / "run_status.json").read_text(encoding="utf-8"))
    assert status["diagnostic_status"] == "BLOCKED"


def test_nonterminal_normal_return_is_incomplete_and_not_accepted(tmp_path):
    launcher = _launcher(tmp_path, "nonterminal")
    with pytest.raises(DiagnosticLauncherError, match="game_not_terminal"):
        launcher.run_once(executor=_synthetic_executor)
    status = json.loads((launcher.output_directory / "run_status.json").read_text(encoding="utf-8"))
    assert status["run_returned_normally"] is True
    assert status["terminal"] is False
    assert status["diagnostic_status"] == "BLOCKED"


def test_nonterminal_cli_result_exits_nonzero(monkeypatch, tmp_path):
    launcher = _launcher(tmp_path, "cli-nonterminal")
    monkeypatch.setattr(stage002, "run_game", _synthetic_executor)
    exit_code = launcher_module.main(
        [
            "--output-directory",
            str(launcher.output_directory),
            "--source-approval",
            str(launcher.source_approval_path),
            "--run-authorization",
            str(launcher.run_authorization_path),
        ]
    )
    assert exit_code == 2
    status = json.loads((launcher.output_directory / "run_status.json").read_text(encoding="utf-8"))
    assert status["diagnostic_status"] == "BLOCKED"
    assert "game_not_terminal" in status["blocking_findings"]


def test_missing_presence_evidence_blocks_normal_return(tmp_path):
    launcher = _launcher(tmp_path, "missing-presence")

    def missing_presence(root, spec, *, diagnostic_capture):
        snapshot = _synthetic_executor(root, spec, diagnostic_capture=diagnostic_capture)
        snapshot.pop("stage002_presence")
        return snapshot

    with pytest.raises(DiagnosticLauncherError):
        launcher.run_once(executor=missing_presence)
    status = json.loads((launcher.output_directory / "run_status.json").read_text(encoding="utf-8"))
    assert status["diagnostic_status"] == "BLOCKED"
    assert "presence_evidence_missing" in status["blocking_findings"]


def test_postmerge_accepted_main_pin_matches_verified_integration(tmp_path):
    """New source guard accepts the merged main while retaining exact source approval."""
    launcher = _launcher(tmp_path, "postmerge-main")
    assert launcher_module.ACCEPTED_MAIN == "891963754d7cc6342ae963a0bf4b69918861460f"
    source = launcher._verify_source()
    assert source["accepted_main"] == launcher_module.ACCEPTED_MAIN
    assert source["head"] == source["source_approval"]["implementation_sha"]


def test_postmerge_pin_rejects_preintegration_main_before_dispatch(tmp_path, monkeypatch):
    """A stale origin/main must fail closed before any executor or claim is used."""
    launcher = _launcher(tmp_path, "stale-premerge-main")
    original_git = launcher._git

    def stale_main_git(root, *args):
        if args == ("rev-parse", "refs/remotes/origin/main"):
            return "10d2ac80ef5b81b3a209a3133eb0a84633a1f944"
        return original_git(root, *args)

    monkeypatch.setattr(launcher, "_git", stale_main_git)
    called = 0

    def forbidden_executor(*_args, **_kwargs):
        nonlocal called
        called += 1
        raise AssertionError("stale main must block before dispatch")

    with pytest.raises(DiagnosticLauncherError, match="accepted main changed"):
        launcher.run_once(executor=forbidden_executor)
    assert called == launcher._run_game_call_count == 0
    assert not launcher.output_directory.exists()
