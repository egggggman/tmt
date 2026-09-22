import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.calibration_launcher_release import (  # noqa: E402
    LauncherReleaseViolation,
    build_manifest,
)
from scripts.calibration_run_reservation import reserve_run  # noqa: E402

RENDERER = ROOT / "scripts" / "calibration_runtime_wrapper.py"


def _fixture(tmp_path):
    repo = tmp_path / "repo"
    for relative in (
        "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V16.json",
        "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V16.json.sha256",
        "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V17.json",
        "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V17.json.sha256",
        "docs/cardcade/CALIBRATION_RELEASE_AUTHORITY_V1.json",
        "docs/cardcade/CALIBRATION_RELEASE_AUTHORITY_V1.json.sha256",
        "docs/cardcade/CALIBRATION_RELEASE_AUTHORITY_V2.json",
        "docs/cardcade/CALIBRATION_RELEASE_AUTHORITY_V2.json.sha256",
        "docs/cardcade/CALIBRATION_RELEASE_AUTHORITY_V3.json",
        "docs/cardcade/CALIBRATION_RELEASE_AUTHORITY_V3.json.sha256",
        "docs/cardcade/CALIBRATION_RELEASE_MANIFEST_CAPACITY_V1.json",
        "scripts/calibration_runtime_wrapper.py",
    ):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=ROOT))
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": "2026-09-20T12:00:00Z",
        "GIT_COMMITTER_DATE": "2026-09-20T12:00:00Z",
    }
    for command in (
        ["git", "-c", "core.autocrlf=false", "init", "-q"],
        ["git", "config", "core.autocrlf", "false"],
        ["git", "add", "."],
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
        subprocess.run(command, cwd=repo, check=True, env=env)
    authority_path = repo / "docs/cardcade/CALIBRATION_RELEASE_AUTHORITY_V3.json"
    authority = json.loads(authority_path.read_bytes())
    renderer_blob = subprocess.check_output(
        ["git", "show", "HEAD:scripts/calibration_runtime_wrapper.py"], cwd=repo
    )
    authority["renderer"]["sha256"] = hashlib.sha256(renderer_blob).hexdigest().upper()
    capacity_blob = subprocess.check_output(
        ["git", "show", "HEAD:docs/cardcade/CALIBRATION_RELEASE_MANIFEST_CAPACITY_V1.json"],
        cwd=repo,
    )
    authority["frozen_deck_manifest"]["sha256"] = hashlib.sha256(capacity_blob).hexdigest().upper()
    authority_payload = (json.dumps(authority, sort_keys=True, indent=2) + "\n").encode()
    authority_path.write_bytes(authority_payload)
    authority_path.with_suffix(".json.sha256").write_text(
        f"{hashlib.sha256(authority_payload).hexdigest().upper()}  "
        "CALIBRATION_RELEASE_AUTHORITY_V3.json\n",
        encoding="ascii",
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True, env=env)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "fixture authority",
        ],
        cwd=repo,
        check=True,
        env=env,
    )
    reservation = reserve_run(repo, timestamp="20260920T120010Z")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, env=env)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "reservation",
        ],
        cwd=repo,
        check=True,
        env=env,
    )
    return repo, reservation["run_id"]


def _build(tmp_path):
    repo, run_id = _fixture(tmp_path)
    renderer_hash = hashlib.sha256(
        subprocess.check_output(
            ["git", "show", "HEAD:scripts/calibration_runtime_wrapper.py"], cwd=repo
        )
    ).hexdigest()
    return build_manifest(
        repo,
        run_id,
        renderer_source_sha256=renderer_hash,
        target_exists=lambda _: False,
    )


def test_pre_generation_manifest_identity_is_deterministic_and_non_authorizing(tmp_path):
    first, first_bytes = _build(tmp_path / "first")
    second, second_bytes = _build(tmp_path / "second")

    assert first == second
    assert first_bytes == second_bytes
    assert hashlib.sha256(first_bytes).hexdigest().upper() != first["renderer"]["sha256"]
    assert first["accepted_runtime"] == "60acd013b28dc9d8cb46c5c5520c11e9e3943627"
    assert first["execution_authorized"] is False
    assert first["launcher_generated"] is False
    assert first["generated_launcher_sha256"] is None
    assert first["output_rel"] == rf"G:\cardcade\calibration-runs\{first['run_id']}"


def test_tampered_checkout_release_input_fails_closed(tmp_path):
    repo, run_id = _fixture(tmp_path)
    import scripts.calibration_launcher_release as release

    selected = repo / "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V17.json"
    data = json.loads(selected.read_bytes())
    data["accepted_runtime"] = "d0b6b728c3cf0d6d883bb80a398c4b3d99a1259e"
    selected.write_text(json.dumps(data) + "\n", encoding="utf-8")
    with pytest.raises(release.LauncherReleaseViolation, match="checkout differs"):
        build_manifest(
            repo,
            run_id,
            renderer_source_sha256=hashlib.sha256(RENDERER.read_bytes()).hexdigest(),
            target_exists=lambda _: False,
        )


def test_eventual_launcher_hash_is_separate_from_manifest_identity(tmp_path):
    manifest, payload = _build(tmp_path)
    manifest_hash = hashlib.sha256(payload).hexdigest().upper()
    inputs = manifest["render_inputs"]
    from scripts import calibration_runtime_wrapper as wrapper

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


def test_reservation_and_release_authority_disagreement_fails_closed(tmp_path):
    repo, run_id = _fixture(tmp_path)
    reservation = repo / "docs/cardcade" / run_id / "RESERVATION.json"
    data = json.loads(reservation.read_bytes())
    data["reservation_identity"]["accepted_runtime"] = "d0b6b728c3cf0d6d883bb80a398c4b3d99a1259e"
    payload = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode()
    reservation.write_bytes(payload)
    sidecar = reservation.with_suffix(".json.sha256")
    sidecar.write_text(
        f"{hashlib.sha256(payload).hexdigest().upper()}  RESERVATION.json\n",
        encoding="ascii",
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "tampered reservation",
        ],
        cwd=repo,
        check=True,
    )
    with pytest.raises(LauncherReleaseViolation, match="disagree"):
        build_manifest(
            repo,
            run_id,
            renderer_source_sha256=hashlib.sha256(RENDERER.read_bytes()).hexdigest(),
            target_exists=lambda _: False,
        )
