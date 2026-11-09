from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from tools import cardcade_diagnostic_launcher as launcher_module
from tools.cardcade_diagnostic_launcher import DiagnosticLauncherError, stage002
from test_cardcade_diagnostic_launcher_safety import _launcher, _synthetic_executor


def _unique_launcher(tmp_path: Path, label: str):
    nonce = uuid.uuid4().hex
    return _launcher(
        tmp_path,
        f"{label}-{nonce}",
        authorization_id=f"RED-{nonce}",
    )


def test_unsigned_authorization_documents_are_rejected(tmp_path):
    launcher = _unique_launcher(tmp_path, "unsigned")

    with pytest.raises(DiagnosticLauncherError, match="signature"):
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

    with pytest.raises(DiagnosticLauncherError, match="reconciliation"):
        launcher.run_once(executor=terminal_setup_snapshot)

    assert launcher_module.stage002 is stage002
