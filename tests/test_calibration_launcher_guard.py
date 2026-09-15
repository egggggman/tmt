"""Compile-only guard regressions; no gameplay or calibration execution."""

import py_compile
from pathlib import Path

import pytest

from scripts.calibration_launcher_guard import validate_launcher

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "docs/cardcade/CALIBRATION_V1_20260915T180636Z_77400eb2480d/launcher.py.txt"


def test_preserved_malformed_launcher_is_rejected_without_execution(tmp_path):
    target = tmp_path / "historical_launcher.py"
    target.write_bytes(HISTORICAL.read_bytes())
    with pytest.raises(py_compile.PyCompileError, match="expected 'except' or 'finally'"):
        validate_launcher(target)


def test_corrected_launcher_construction_path_compiles_exact_bytes(tmp_path):
    source = (ROOT / "scripts/calibration_v1_launcher.py").read_bytes()
    target = tmp_path / "generated_launcher.py"
    target.write_bytes(source)
    digest = validate_launcher(target)
    assert digest
    assert target.read_bytes() == source
