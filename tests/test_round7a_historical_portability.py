"""R7-A's read-only gates authenticate frozen evidence in either EOL mode."""

import json
import subprocess
from pathlib import Path

import pytest

from tools import build_objective_balance_lab_round7a_results as report
from tools import run_objective_balance_lab_round7a as run
from tools import validate_objective_balance_lab_round7a_readiness as readiness


@pytest.mark.parametrize("eol", [b"\n", b"\r\n"])
def test_archived_readiness_and_saved_results_accept_only_checkout_eol(monkeypatch, eol):
    original = Path.read_bytes

    def checkout(path):
        raw = original(path)
        if path.suffix in {".json", ".md", ".txt", ".py"}:
            return raw.replace(b"\r\n", b"\n").replace(b"\n", eol)
        return raw

    monkeypatch.setattr(Path, "read_bytes", checkout)
    saved = readiness.snapshot()
    assert saved == json.loads(readiness.OUTPUT.read_text(encoding="utf-8"))
    assert readiness.render(saved) == readiness.REPORT.read_text(encoding="utf-8")
    assert saved["candidate_games_executed"] == saved["candidate_replays_executed"] == 0
    assert report.build() == json.loads(report.ANALYSIS.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", [readiness.OUTPUT, readiness.REPORT, run.AUTHORITY])
def test_edited_readiness_fails_even_when_json_or_markdown_is_equivalent(monkeypatch, path):
    original = Path.read_bytes

    def tampered(candidate):
        raw = original(candidate)
        return raw + b" " if candidate == path else raw

    monkeypatch.setattr(Path, "read_bytes", tampered)
    with pytest.raises(ValueError, match="differs from Git authority"):
        if path == run.AUTHORITY:
            run.preflight(historical=True)
        else:
            readiness.snapshot()


def test_archived_readiness_rejects_missing_frozen_source(monkeypatch):
    actual = subprocess.check_output

    def missing(args, **kwargs):
        if args[:2] == ["git", "show"] and args[2].startswith("897f8501"):
            raise subprocess.CalledProcessError(128, args)
        return actual(args, **kwargs)

    monkeypatch.setattr(subprocess, "check_output", missing)
    with pytest.raises(subprocess.CalledProcessError):
        readiness.snapshot()


def test_archived_readiness_rejects_frozen_driver_hash_mismatch(monkeypatch):
    actual = readiness.git

    def changed(*args):
        raw = actual(*args)
        if args[0] == "show" and args[1].endswith("run_objective_balance_lab_round6c.py"):
            return raw + b"# altered driver\n"
        return raw

    monkeypatch.setattr(readiness, "git", changed)
    with pytest.raises(AssertionError):
        readiness.snapshot()
