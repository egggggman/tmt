import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_calibration_run_reservation import _fixture  # noqa: E402

from scripts import calibration_release_authority as authority  # noqa: E402


def test_promoted_authority_authenticates_selected_runtime_and_immutable_inputs(tmp_path):
    result = authority.authenticate_release_authority(_fixture(tmp_path))
    assert result["accepted_runtime"] == "60acd013b28dc9d8cb46c5c5520c11e9e3943627"
    assert result["v16_baseline_sha256"] == (
        "10BDC8CD2C78BBA7C0777E71B10E15592655DFA353859A01D6BE94DAE36A8EC8"
    )
    assert len(result["deck_hashes"]) == 10


def test_missing_promotion_artifact_fails_closed(tmp_path, monkeypatch):
    repo = _fixture(tmp_path)
    original = authority._git_blob

    def missing(root, relative):
        if relative == authority.AUTHORITY_REL:
            raise authority.ReleaseAuthorityViolation("missing promotion artifact")
        return original(root, relative)

    monkeypatch.setattr(authority, "_git_blob", missing)
    with pytest.raises(authority.ReleaseAuthorityViolation, match="missing promotion"):
        authority.authenticate_release_authority(repo)


def test_wrong_promotion_sha_fails_closed(tmp_path, monkeypatch):
    repo = _fixture(tmp_path)
    original = authority._git_blob

    def wrong_hash(root, relative):
        payload = original(root, relative)
        if relative == authority.AUTHORITY_REL:
            data = json.loads(payload)
            data["selected_runtime_artifact"]["sha256"] = "0" * 64
            return (json.dumps(data) + "\n").encode()
        return payload

    monkeypatch.setattr(authority, "_git_blob", wrong_hash)
    with pytest.raises(authority.ReleaseAuthorityViolation, match="checkout|sidecar|hash"):
        authority.authenticate_release_authority(repo)


def test_runtime_refresh_tampering_fails_closed(tmp_path, monkeypatch):
    repo = _fixture(tmp_path)
    original = authority._git_blob

    def tampered(root, relative):
        payload = original(root, relative)
        if relative.endswith("CALIBRATION_RELEASE_BASELINE_REFRESH_V17.json"):
            return payload.replace(
                b'"execution_authorized": false', b'"execution_authorized": true'
            )
        return payload

    monkeypatch.setattr(authority, "_git_blob", tampered)
    with pytest.raises(authority.ReleaseAuthorityViolation, match="checkout|sidecar"):
        authority.authenticate_release_authority(repo)


def test_selected_authority_cannot_fallback_to_v16(tmp_path, monkeypatch):
    repo = _fixture(tmp_path)
    original = authority._git_blob
    original_authority = original(repo, authority.AUTHORITY_REL)
    data = json.loads(original_authority)
    data["selected_runtime_artifact"] = {
        "rel": authority.V16_REL,
        "sha256": hashlib.sha256(original(repo, authority.V16_REL)).hexdigest().upper(),
    }
    replacement = (json.dumps(data) + "\n").encode()

    def fallback(root, relative):
        if relative == authority.AUTHORITY_REL:
            return replacement
        if relative == f"{authority.AUTHORITY_REL}.sha256":
            return f"{hashlib.sha256(replacement).hexdigest().upper()}  x\n".encode()
        return original(root, relative)

    monkeypatch.setattr(authority, "_git_blob", fallback)
    with pytest.raises(authority.ReleaseAuthorityViolation, match="checkout|not V17"):
        authority.authenticate_release_authority(repo)


def test_historical_v16_mutation_fails_closed(tmp_path, monkeypatch):
    repo = _fixture(tmp_path)
    original = authority._git_blob

    def tampered(root, relative):
        payload = original(root, relative)
        if relative == authority.V16_REL:
            return payload.replace(
                b'"execution_authorized": false', b'"execution_authorized": true'
            )
        return payload

    monkeypatch.setattr(authority, "_git_blob", tampered)
    with pytest.raises(authority.ReleaseAuthorityViolation, match="checkout|sidecar"):
        authority.authenticate_release_authority(repo)
