"""Strict persistence and provenance tests for new control artifacts."""

from __future__ import annotations

import gzip
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.artifact_integrity import (
    ArtifactIntegrityError,
    assert_new_control_classification,
    read_validated_artifact,
    write_validated_artifact,
)


def payload() -> dict[str, object]:
    return {
        "schema": "test-control-v1",
        "evidence_id": "TEST-CONTROL-001",
        "semantic_runtime_sha256": "runtime",
        "schedule_sha256": "schedule",
        "required_games": 10,
        "games": list(range(10)),
        "status": "COMPLETE",
    }


def test_valid_artifact_is_finalized_and_read_back(tmp_path: Path):
    path = tmp_path / "control.json.gz"
    digest = write_validated_artifact(path, payload(), expected_manifest={"status": "COMPLETE"})
    restored, reread_digest = read_validated_artifact(
        path, expected_sha256=digest, expected_manifest={"evidence_id": "TEST-CONTROL-001"}
    )
    assert restored == payload()
    assert reread_digest == digest
    assert not list(tmp_path.glob("*.tmp"))


def test_truncated_or_modified_bytes_are_rejected(tmp_path: Path):
    path = tmp_path / "control.json.gz"
    write_validated_artifact(path, payload())
    raw = path.read_bytes()
    path.write_bytes(raw[:-1])
    with pytest.raises(ArtifactIntegrityError):
        read_validated_artifact(path)


def test_manifest_hash_and_schema_mismatches_are_rejected(tmp_path: Path):
    path = tmp_path / "control.json.gz"
    digest = write_validated_artifact(path, payload())
    with pytest.raises(ArtifactIntegrityError):
        read_validated_artifact(path, expected_sha256="0" * 64)
    with pytest.raises(ArtifactIntegrityError):
        read_validated_artifact(path, expected_manifest={"schema": "other-v1"})
    assert digest != "0" * 64


def test_failed_write_is_quarantined(monkeypatch, tmp_path: Path):
    path = tmp_path / "control.json.gz"
    original = gzip.compress

    def truncated(data: bytes, *, mtime: int = 0) -> bytes:
        return original(data, mtime=mtime)[:-1]

    monkeypatch.setattr("tools.artifact_integrity.gzip.compress", truncated)
    with pytest.raises(ArtifactIntegrityError):
        write_validated_artifact(path, payload())
    assert not path.exists()
    assert list(tmp_path.glob("*.quarantine"))


def test_historical_exception_is_rejected_for_new_controls():
    with pytest.raises(ArtifactIntegrityError):
        assert_new_control_classification(
            {"historical_classification": "HISTORICAL_CORRUPT_EXCLUDED"}
        )
    assert_new_control_classification({"evidence_id": "NEW-CONTROL"})
