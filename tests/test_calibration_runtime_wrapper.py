import hashlib
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "wrapper", ROOT / "scripts/calibration_runtime_wrapper.py"
)
wrapper = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(wrapper)


def make_fixture(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "scripts").mkdir()
    shutil.copy2(ROOT / "scripts/calibration_runtime_wrapper.py", repo / "scripts")
    (repo / "packet.json").write_bytes(b'{"execution_authorized":false}\n')
    (repo / "launcher.py").write_bytes(b"x = 1\n")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "packet.json", "launcher.py"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=x", "-c", "user.email=x@y", "commit", "-qm", "fixture"],
        cwd=repo,
        check=True,
    )
    packet_hash = (
        hashlib.sha256(subprocess.check_output(["git", "show", "HEAD:packet.json"], cwd=repo))
        .hexdigest()
        .upper()
    )
    launcher_hash = (
        hashlib.sha256(subprocess.check_output(["git", "show", "HEAD:launcher.py"], cwd=repo))
        .hexdigest()
        .upper()
    )
    (repo / "packet.json.sha256").write_text(packet_hash, encoding="ascii")
    (repo / "launcher.py.sha256").write_text(launcher_hash, encoding="ascii")
    return repo, packet_hash, launcher_hash


def test_generated_wrapper_preflight_and_fail_closed_cases(tmp_path):
    repo, packet_hash, launcher_hash = make_fixture(tmp_path)
    identity = dict(
        packet_rel="packet.json",
        packet_hash=packet_hash,
        launcher_rel="launcher.py",
        launcher_hash=launcher_hash,
    )
    first = wrapper.render_wrapper(**identity)
    assert first == wrapper.render_wrapper(**identity)
    assert (
        hashlib.sha256(first).hexdigest()
        == hashlib.sha256(wrapper.render_wrapper(**identity)).hexdigest()
    )
    output = repo / "docs" / "v14" / "run" / "launcher.py"
    output.parent.mkdir(parents=True)
    wrapper.write_wrapper(output, **identity)
    result = subprocess.run(
        [sys.executable, str(output)],
        cwd=repo,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert "PREFLIGHT_AUTHENTICATED_NO_EXECUTION" in result.stdout
    assert not (repo / "RUN_HEARTBEAT.json").exists()
    (repo / "packet.json").write_bytes(b'{"execution_authorized":false}\r\n')
    wrapper.preflight(repo, **identity)
    for path, value, message in (
        (repo / "packet.json.sha256", "0" * 64, "sidecar"),
        (repo / "launcher.py.sha256", "0" * 64, "sidecar"),
    ):
        path.write_text(value, encoding="ascii")
        with pytest.raises(RuntimeError, match=message):
            wrapper.preflight(repo, **identity)
        path.write_text(
            packet_hash if path.name.startswith("packet") else launcher_hash, encoding="ascii"
        )
    with pytest.raises(RuntimeError, match="committed hash"):
        wrapper.preflight(repo, "packet.json", "0" * 64, "launcher.py", launcher_hash)
    with pytest.raises(RuntimeError, match="committed hash"):
        wrapper.preflight(repo, "packet.json", packet_hash, "launcher.py", "0" * 64)
    (repo / "packet.json").write_bytes(b'{"execution_authorized":true}\n')
    with pytest.raises(RuntimeError, match="checkout"):
        wrapper.preflight(repo, **identity)
    (repo / "packet.json").write_bytes(b'{"execution_authorized":false}\n')
    (repo / "launcher.py").write_bytes(b"x = 2\n")
    with pytest.raises(RuntimeError, match="checkout"):
        wrapper.preflight(repo, **identity)
