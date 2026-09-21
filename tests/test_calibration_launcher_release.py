import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
storage_spec = importlib.util.spec_from_file_location(
    "scripts.calibration_storage_target", ROOT / "scripts/calibration_storage_target.py"
)
storage = importlib.util.module_from_spec(storage_spec)
assert storage_spec.loader is not None
storage_spec.loader.exec_module(storage)
sys.modules["scripts.calibration_storage_target"] = storage
spec = importlib.util.spec_from_file_location(
    "calibration_launcher_release", ROOT / "scripts/calibration_launcher_release.py"
)
release = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(release)

RUN_ID = "CALIBRATION_V1_20260921T050741Z_98aa7d180751"
RENDERER = ROOT / "scripts" / "calibration_runtime_wrapper.py"


def build():
    return release.build_manifest(
        ROOT,
        RUN_ID,
        renderer_source_sha256=hashlib.sha256(RENDERER.read_bytes()).hexdigest(),
        target_exists=lambda _: False,
    )


def test_pre_generation_manifest_identity_is_deterministic_and_non_authorizing():
    first, first_bytes = build()
    second, second_bytes = build()

    assert first == second
    assert first_bytes == second_bytes
    assert hashlib.sha256(first_bytes).hexdigest().upper() != first["renderer"]["sha256"]
    assert first["execution_authorized"] is False
    assert first["launcher_generated"] is False
    assert first["generated_launcher_sha256"] is None
    assert first["run_id"] == RUN_ID
    assert first["output_rel"] == rf"G:\cardcade\calibration-runs\{RUN_ID}"
    assert first["schedule"]["distinct_games"] == 184320
    assert first["schedule"]["executions"] == 368640


def test_tampered_checkout_release_input_fails_closed(monkeypatch):
    original = release._checkout_bytes

    def tampered(root, relative):
        payload = original(root, relative)
        if relative == release.BASELINE_REL:
            return payload.replace(
                b'"execution_authorized": false', b'"execution_authorized": true'
            )
        return payload

    monkeypatch.setattr(release, "_checkout_bytes", tampered)
    with pytest.raises(release.LauncherReleaseViolation, match="checkout differs"):
        build()


def test_eventual_launcher_hash_is_separate_from_manifest_identity():
    manifest, payload = build()
    manifest_hash = hashlib.sha256(payload).hexdigest().upper()
    inputs = manifest["render_inputs"]
    from_wrapper = importlib.util.spec_from_file_location(
        "calibration_runtime_wrapper", ROOT / "scripts/calibration_runtime_wrapper.py"
    )
    wrapper = importlib.util.module_from_spec(from_wrapper)
    assert from_wrapper.loader is not None
    from_wrapper.loader.exec_module(wrapper)
    launcher_bytes = wrapper.render_execution_wrapper(
        packet_rel=inputs["packet_rel"],
        packet_hash=inputs["packet_sha256"],
        release_rel=inputs["release_manifest_rel"],
        release_hash=manifest_hash,
        seed_rel=inputs["seed_rel"],
        seed_hash=inputs["seed_sha256"],
        output_rel=manifest["output_rel"],
    )
    launcher_hash = hashlib.sha256(launcher_bytes).hexdigest().upper()

    assert launcher_hash != manifest_hash
    assert manifest["generated_launcher_sha256"] is None
    assert manifest["execution_authorized"] is False
    assert "execute_protocol" in launcher_bytes.decode()
