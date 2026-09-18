from __future__ import annotations

import hashlib
import json
import subprocess


def blob(root, rel):
    return subprocess.check_output(["git", "show", "HEAD:" + rel], cwd=root)


def equivalent(a, b):
    return a.replace(b"\r\n", b"\n") == b.replace(b"\r\n", b"\n")


def preflight(root, packet_rel, packet_hash, launcher_rel, launcher_hash):
    for rel, expected in ((packet_rel, packet_hash), (launcher_rel, launcher_hash)):
        committed = blob(root, rel)
        path = root / rel
        if hashlib.sha256(committed).hexdigest().upper() != expected.upper():
            raise RuntimeError("committed hash mismatch")
        if (
            path.with_suffix(path.suffix + ".sha256").read_text("ascii").split()[0].upper()
            != expected.upper()
        ):
            raise RuntimeError("sidecar hash mismatch")
        if not equivalent(path.read_bytes(), committed):
            raise RuntimeError("checkout differs from committed blob")
    if json.loads(blob(root, packet_rel))["execution_authorized"] is not False:
        raise RuntimeError("non-authorizing packet required")


def render_wrapper(packet_rel, packet_hash, launcher_rel, launcher_hash):
    lines = (
        "from pathlib import Path",
        "import sys",
        "ROOT=Path(__file__).resolve().parents[3]",
        "sys.path.insert(0,str(ROOT))",
        "from scripts.calibration_runtime_wrapper import preflight",
        f"preflight(ROOT,{packet_rel!r},{packet_hash.upper()!r},{launcher_rel!r},{launcher_hash.upper()!r})",
        "print('PREFLIGHT_AUTHENTICATED_NO_EXECUTION')",
        "",
    )
    return "\n".join(lines).encode()


def write_wrapper(path, **identity):
    payload = render_wrapper(**identity)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest().upper()


def render_execution_wrapper(
    packet_rel, packet_hash, launcher_rel, launcher_hash, seed_rel, seed_hash, output_rel
):
    lines = (
        "from pathlib import Path",
        "import sys",
        "ROOT=Path(__file__).resolve().parents[3]",
        "sys.path.insert(0,str(ROOT))",
        "from scripts.calibration_runtime_wrapper import preflight",
        f"preflight(ROOT,{packet_rel!r},{packet_hash.upper()!r},{launcher_rel!r},{launcher_hash.upper()!r})",
        "from tmnt_design_studio.calibration_runner import execute_protocol",
        "from tmnt_design_studio.calibration_executor import execute_member",
        f"seed_path = ROOT / {seed_rel!r}",
        f"output_path = ROOT / {output_rel!r}",
        "execute_protocol(",
        "    seed_path,",
        "    output_path,",
        "    lambda member, duplicate: execute_member(ROOT, member, duplicate),",
        "    strict=True,",
        f"    expected_seed_table_sha256={seed_hash.upper()!r},",
        ")",
        "",
    )
    return "\n".join(lines).encode()


def write_execution_wrapper(path, **identity):
    payload = render_execution_wrapper(**identity)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest().upper()
