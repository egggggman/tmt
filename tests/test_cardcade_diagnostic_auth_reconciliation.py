from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from cardcade_auth_test_support import (
    OTHER_TEST_KEY_ID,
    signed_document,
)
from test_cardcade_diagnostic_launcher_safety import _launcher, _synthetic_executor

from tools import cardcade_diagnostic_launcher as launcher_module
from tools.cardcade_diagnostic_launcher import DiagnosticLauncherError, stage002


def _unique_launcher(tmp_path: Path, label: str):
    nonce = uuid.uuid4().hex
    return _launcher(
        tmp_path,
        f"{label[:2]}-{nonce[:8]}",
        authorization_id=f"RED-{nonce}",
    )


def test_unsigned_authorization_documents_are_rejected(tmp_path):
    launcher = _unique_launcher(tmp_path, "unsigned")
    for path in (launcher.source_approval_path, launcher.run_authorization_path):
        document = json.loads(path.read_text(encoding="utf-8"))
        document.pop("signature")
        document.pop("signing_key_id")
        path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(DiagnosticLauncherError, match="signed fields"):
        launcher._verify_source()


def test_valid_synthetic_signature_is_bound_to_both_documents(tmp_path):
    launcher = _unique_launcher(tmp_path, "valid-signatures")
    source = launcher._verify_source()

    assert (
        source["source_approval"]["signing_key_id"] == source["run_authorization"]["signing_key_id"]
    )


@pytest.mark.parametrize("document_name", ["source_approval", "run_authorization"])
def test_altered_authorization_content_fails_signature_verification(tmp_path, document_name):
    launcher = _unique_launcher(tmp_path, f"altered-{document_name}")
    path = getattr(launcher, f"{document_name}_path")
    document = json.loads(path.read_text(encoding="utf-8"))
    document["implementation_sha"] = "0" * 40
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(DiagnosticLauncherError, match="signature verification failed"):
        launcher._verify_source()


def test_source_and_run_authorization_must_use_same_trusted_signer(tmp_path):
    launcher = _unique_launcher(tmp_path, "signer-mismatch")
    document = json.loads(launcher.run_authorization_path.read_text(encoding="utf-8"))
    document.pop("signature")
    signed = signed_document(document, key_id=OTHER_TEST_KEY_ID)
    launcher.run_authorization_path.write_text(json.dumps(signed), encoding="utf-8")

    with pytest.raises(DiagnosticLauncherError, match="different HQ signing keys"):
        launcher._verify_source()


def test_unknown_signer_and_unconfigured_trust_anchor_fail_closed(monkeypatch, tmp_path):
    launcher = _unique_launcher(tmp_path, "unknown-signer")
    module = launcher_module
    monkeypatch.setattr(module, "TRUSTED_HQ_AUTHORIZATION_KEYS", {})

    with pytest.raises(DiagnosticLauncherError, match="untrusted key ID"):
        launcher._verify_source()


def test_duplicate_json_authorization_fields_are_rejected(tmp_path):
    launcher = _unique_launcher(tmp_path, "duplicate-field")
    original = launcher.source_approval_path.read_text(encoding="utf-8")
    duplicate = original[:-1] + ',"approval_id":"forged"}'
    launcher.source_approval_path.write_text(duplicate, encoding="utf-8")

    with pytest.raises(DiagnosticLauncherError, match="duplicate authorization field"):
        launcher._verify_source()


def test_incomplete_stage002_reconciliation_cannot_return_ready(monkeypatch, tmp_path):
    launcher = _unique_launcher(tmp_path, "incomplete-reconciliation")
    monkeypatch.setattr(
        stage002,
        "reconcile_snapshot",
        lambda *_args, **_kwargs: {"stop_records": [], "invariant_violations": []},
    )

    def terminal_setup_snapshot(root, spec, *, diagnostic_capture):
        snapshot = _synthetic_executor(root, spec, diagnostic_capture=diagnostic_capture)
        snapshot["terminal"] = True
        return snapshot

    monkeypatch.setattr(stage002, "run_game", terminal_setup_snapshot)
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
    assert "reconciliation_failed" in status["blocking_findings"]
    assert (launcher.output_directory / "snapshot.json").is_file()
    assert (launcher.output_directory / "reconciliation.json").is_file()

    assert launcher_module.stage002 is stage002


def test_fabricated_complete_report_with_recomputed_digest_cannot_return_ready(
    monkeypatch, tmp_path
):
    launcher = _unique_launcher(tmp_path, "forged-derived-fields")
    original_reconcile = stage002.reconcile_snapshot

    def forged_reconcile(spec, snapshot, manifest):
        report = original_reconcile(spec, snapshot, manifest)
        report["transaction_counts"] = {"forged_execution": 1}
        body = {key: value for key, value in report.items() if key != "report_digest"}
        report["report_digest"] = stage002.stable_digest(body)
        return report

    monkeypatch.setattr(stage002, "reconcile_snapshot", forged_reconcile)

    def terminal_setup_snapshot(root, spec, *, diagnostic_capture):
        snapshot = _synthetic_executor(root, spec, diagnostic_capture=diagnostic_capture)
        snapshot["terminal"] = True
        return snapshot

    monkeypatch.setattr(stage002, "run_game", terminal_setup_snapshot)
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

    status = json.loads((launcher.output_directory / "run_status.json").read_text(encoding="utf-8"))
    supplied = json.loads(
        (launcher.output_directory / "reconciliation.json").read_text(encoding="utf-8")
    )
    assert exit_code == 2
    assert status["diagnostic_status"] == "BLOCKED"
    assert "reconciliation_failed" in status["blocking_findings"]
    assert supplied["transaction_counts"] == {"forged_execution": 1}
    assert supplied["report_digest"] == stage002.stable_digest(
        {key: value for key, value in supplied.items() if key != "report_digest"}
    )
    assert (launcher.output_directory / "snapshot.json").is_file()
    assert (launcher.output_directory / "reconciliation.json").is_file()


def test_actual_reconciliation_digest_and_manifest_binding_are_preserved(tmp_path):
    launcher = _unique_launcher(tmp_path, "actual-contract")
    source = launcher._verify_source()
    spec = launcher._match_spec()
    manifest = stage002.build_stage_manifest(launcher.root)
    capture = stage002.DiagnosticExecutionCapture()
    snapshot = stage002.capture_diagnostic_call(
        capture,
        lambda: _synthetic_executor(launcher.root, spec, diagnostic_capture=capture),
    )
    report = stage002.reconcile_snapshot(spec, snapshot, manifest)

    assert launcher._validate_reconciliation(report, spec, snapshot, manifest, source) == []
    with pytest.raises(DiagnosticLauncherError, match="game_not_terminal"):
        launcher.run_once(executor=_synthetic_executor)
    binding = json.loads(
        (launcher.output_directory / "reconciliation_binding.json").read_text(encoding="utf-8")
    )
    assert binding["implementation_sha"] == source["head"]
    assert binding["stage_manifest_digest"] == manifest["manifest_digest"]
    assert binding["reconciliation_report_digest"] == report["report_digest"]


@pytest.mark.parametrize("defect", ["digest", "game_identity", "source_evidence", "manifest_game"])
def test_incomplete_or_altered_stage002_report_is_blocked(monkeypatch, tmp_path, defect):
    launcher = _unique_launcher(tmp_path, f"altered-report-{defect}")
    original_reconcile = stage002.reconcile_snapshot
    original_manifest_builder = stage002.build_stage_manifest

    def altered_manifest(root):
        manifest = original_manifest_builder(root)
        if defect == "manifest_game":
            manifest["games"] = [
                item
                for item in manifest["games"]
                if item["game_id"] != "april-casey:canonical:7231"
            ]
            body = {key: value for key, value in manifest.items() if key != "manifest_digest"}
            manifest["manifest_digest"] = stage002.stable_digest(body)
        return manifest

    def altered_reconcile(spec, snapshot, manifest):
        report = original_reconcile(spec, snapshot, manifest)
        if defect == "digest":
            report["report_digest"] = "0" * 64
        elif defect == "game_identity":
            report["game_id"] = "forged-game"
            body = {key: value for key, value in report.items() if key != "report_digest"}
            report["report_digest"] = stage002.stable_digest(body)
        elif defect == "source_evidence":
            report["authoritative_evidence"]["events"] = []
            body = {key: value for key, value in report.items() if key != "report_digest"}
            report["report_digest"] = stage002.stable_digest(body)
        return report

    monkeypatch.setattr(stage002, "build_stage_manifest", altered_manifest)
    monkeypatch.setattr(stage002, "reconcile_snapshot", altered_reconcile)

    def terminal_setup_snapshot(root, spec, *, diagnostic_capture):
        snapshot = _synthetic_executor(root, spec, diagnostic_capture=diagnostic_capture)
        snapshot["terminal"] = True
        return snapshot

    with pytest.raises(DiagnosticLauncherError, match="reconciliation"):
        launcher.run_once(executor=terminal_setup_snapshot)

    status = json.loads((launcher.output_directory / "run_status.json").read_text(encoding="utf-8"))
    assert status["diagnostic_status"] == "BLOCKED"
    assert (launcher.output_directory / "snapshot.json").is_file()
    assert (launcher.output_directory / "reconciliation.json").is_file()
