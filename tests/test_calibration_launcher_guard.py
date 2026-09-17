"""Compile-only guard regressions; no gameplay or calibration execution."""

import hashlib
import importlib.util
import py_compile
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "calibration_launcher_guard", ROOT / "scripts/calibration_launcher_guard.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
validate_launcher = module.validate_launcher
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
    assert validate_launcher(target)
    assert target.read_bytes() == source


def _fixture(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "launcher.py"
    payload = b"x = 1\n"
    target.write_bytes(payload)
    for command in (
        ["git", "init", "-q"],
        ["git", "add", "launcher.py"],
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
    ):
        subprocess.run(command, cwd=repo, check=True)
    digest = hashlib.sha256(payload).hexdigest().upper()
    sidecar = repo / "launcher.py.sha256"
    sidecar.write_text(f"{digest}  launcher.py\n", encoding="ascii")
    return repo, target, sidecar, digest


def test_lf_and_crlf_git_equivalent_checkouts_authenticate(tmp_path):
    repo, target, sidecar, digest = _fixture(tmp_path)
    assert (
        validate_launcher(
            target,
            git_root=repo,
            repository_path="launcher.py",
            expected_committed_sha256=digest,
            sidecar=sidecar,
        )
        == digest
    )
    target.write_bytes(b"x = 1\r\n")
    assert validate_launcher(
        target,
        git_root=repo,
        repository_path="launcher.py",
        expected_committed_sha256=digest,
        sidecar=sidecar,
    )


def test_mutation_sidecar_and_committed_blob_fail_closed(tmp_path):
    repo, target, sidecar, digest = _fixture(tmp_path)
    target.write_bytes(b"x = 2\n")
    with pytest.raises(RuntimeError, match="differs"):
        validate_launcher(
            target,
            git_root=repo,
            repository_path="launcher.py",
            expected_committed_sha256=digest,
            sidecar=sidecar,
        )
    target.write_bytes(b"x = 1\n")
    sidecar.write_text("0" * 64 + "  launcher.py\n", encoding="ascii")
    with pytest.raises(RuntimeError, match="sidecar"):
        validate_launcher(
            target,
            git_root=repo,
            repository_path="launcher.py",
            expected_committed_sha256=digest,
            sidecar=sidecar,
        )
    sidecar.write_text(f"{digest}  launcher.py\n", encoding="ascii")
    with pytest.raises(RuntimeError, match="committed"):
        validate_launcher(
            target,
            git_root=repo,
            repository_path="launcher.py",
            expected_committed_sha256="0" * 64,
            sidecar=sidecar,
        )
