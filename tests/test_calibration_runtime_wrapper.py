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
        release_rel="launcher.py",
        release_hash=launcher_hash,
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


def test_execution_wrapper_handoff_is_after_authenticated_preflight(tmp_path):
    repo, packet_hash, launcher_hash = make_fixture(tmp_path)
    package = repo / "tmnt_design_studio"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8", newline="\n")
    (package / "calibration_runner.py").write_text(
        "from pathlib import Path\n"
        "def execute_protocol(\n"
        "    seed_path, output_path, executor, *, strict, expected_seed_table_sha256\n"
        "):\n"
        "    Path('HANDOFF').write_text(\n"
        "        f'{seed_path}|{output_path}|{strict}|{expected_seed_table_sha256}'\n"
        "    )\n",
        encoding="utf-8",
        newline="\n",
    )
    (package / "calibration_executor.py").write_text(
        "def execute_member(*args): raise AssertionError('member execution is forbidden')\n",
        encoding="utf-8",
        newline="\n",
    )
    identity = dict(
        packet_rel="packet.json",
        packet_hash=packet_hash,
        release_rel="launcher.py",
        release_hash=launcher_hash,
        seed_rel="seed.json",
        seed_hash="A" * 64,
        output_rel="output",
    )
    output = repo / "docs" / "v14" / "execution" / "launcher.py"
    output.parent.mkdir(parents=True)
    first = wrapper.write_execution_wrapper(output, **identity)
    assert first == wrapper.write_execution_wrapper(output, **identity)

    def invoke(path=output):
        return subprocess.run([sys.executable, str(path)], cwd=repo, text=True, capture_output=True)

    def assert_blocked(path, contents):
        marker = repo / "HANDOFF"
        marker.unlink(missing_ok=True)
        original = path.read_bytes()
        path.write_bytes(contents)
        result = invoke()
        path.write_bytes(original)
        assert result.returncode != 0
        assert not marker.exists()

    result = invoke()
    assert result.returncode == 0
    assert (repo / "HANDOFF").read_text(
        encoding="utf-8"
    ) == f"{repo / 'seed.json'}|{repo / 'output'}|True|{identity['seed_hash']}"

    (repo / "packet.json").write_bytes(b'{"execution_authorized":false}\r\n')
    (repo / "launcher.py").write_bytes(b"x = 1\r\n")
    (repo / "HANDOFF").unlink()
    assert invoke().returncode == 0
    assert (repo / "HANDOFF").exists()
    (repo / "packet.json").write_bytes(b'{"execution_authorized":false}\n')
    (repo / "launcher.py").write_bytes(b"x = 1\n")

    assert_blocked(repo / "packet.json.sha256", b"0" * 64)
    assert_blocked(repo / "launcher.py.sha256", b"0" * 64)
    assert_blocked(repo / "packet.json", b'{"execution_authorized":true}\n')
    assert_blocked(repo / "launcher.py", b"x = 2\n")

    bad_packet = output.with_name("bad-packet-hash.py")
    wrapper.write_execution_wrapper(bad_packet, **(identity | {"packet_hash": "0" * 64}))
    assert (repo / "HANDOFF").unlink(missing_ok=True) is None
    assert invoke(bad_packet).returncode != 0
    assert not (repo / "HANDOFF").exists()
    bad_launcher = output.with_name("bad-launcher-hash.py")
    wrapper.write_execution_wrapper(bad_launcher, **(identity | {"release_hash": "0" * 64}))
    assert invoke(bad_launcher).returncode != 0
    assert not (repo / "HANDOFF").exists()


def test_absolute_windows_output_is_rendered_explicitly():
    identity = {
        "packet_rel": "packet.json",
        "packet_hash": "A" * 64,
        "release_rel": "launcher.py",
        "release_hash": "B" * 64,
        "seed_rel": "docs/cardcade/CALIBRATION_SEED_TABLE_V2.json",
        "seed_hash": "C" * 64,
        "output_rel": r"G:\cardcade\calibration-runs\CALIBRATION_V1_20260921T050741Z_98aa7d180751",
    }
    rendered = wrapper.render_execution_wrapper(**identity).decode()
    assert "output_path = Path('G:\\\\cardcade\\\\calibration-runs" in rendered
    assert "output_path = ROOT /" not in rendered


def test_rendered_launcher_resolves_src_packages_without_protocol_start(tmp_path):
    repo = tmp_path / "repo"
    launcher = repo / "docs" / "cardcade" / "run" / "launcher.py"
    package = repo / "src" / "tmnt_design_studio"
    package.mkdir(parents=True)
    launcher.parent.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8", newline="\n")
    (package / "calibration_runner.py").write_text(
        "def execute_protocol(*args, **kwargs):\n"
        "    raise AssertionError('protocol execution started')\n",
        encoding="utf-8",
        newline="\n",
    )
    (package / "calibration_executor.py").write_text(
        "def execute_member(*args, **kwargs):\n"
        "    raise AssertionError('calibration execution started')\n",
        encoding="utf-8",
        newline="\n",
    )
    identity = {
        "packet_rel": "packet.json",
        "packet_hash": "A" * 64,
        "release_rel": "launcher.py",
        "release_hash": "B" * 64,
        "seed_rel": "seed.json",
        "seed_hash": "C" * 64,
        "output_rel": "output",
    }
    rendered = wrapper.render_execution_wrapper(**identity).decode()
    assert "sys.path.insert(0,str(ROOT/'src'))" in rendered
    assert "sys.path.insert(1,str(ROOT))" in rendered
    import_section = rendered.split("from scripts.calibration_runtime_wrapper import", 1)[0]
    probe = (
        import_section
        + "import tmnt_design_studio.calibration_runner\n"
        + "import tmnt_design_studio.calibration_executor\n"
        + "print('IMPORTS_RESOLVED')\n"
    )
    launcher.write_text(probe, encoding="utf-8", newline="\n")
    result = subprocess.run(
        [sys.executable, str(launcher)], cwd=repo, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "IMPORTS_RESOLVED"
