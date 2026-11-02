"""Disposable trust-boundary tests for the historical batch verifier.

These tests patch verifier paths to temporary directories and use a test-only
RSA key. They do not read live keys, outputs, grants, or consumption ledgers.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import math
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

REVIEW_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = REVIEW_ROOT / "sources"

SOURCE_SHA256 = {
    "verify_completed_batch.py": "259c5f18edbfe262778ba351651c28f845901f687764193afb2d0ef85402f39a",
    "stage002_authorization.py": "1fd4db87131a0fef996fc2df7aee5f6634fdbc2d7b90f226c76217596fdb6540",
    "stage002_batch.py": "30720c8d720b52a9538b79063d785e57dc37762bf5099215b7ee05cef0a80293",
}


def load_source_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load preserved source: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


for _name, _expected in SOURCE_SHA256.items():
    _path = SOURCE_ROOT / _name
    if _sha256(_path) != _expected:
        raise RuntimeError(f"preserved source identity mismatch: {_path}")

authorization = load_source_module(
    "stage002_authorization", SOURCE_ROOT / "stage002_authorization.py"
)
batch = load_source_module("stage002_batch", SOURCE_ROOT / "stage002_batch.py")
verifier = load_source_module("reviewed_batch_verifier", SOURCE_ROOT / "verify_completed_batch.py")

# Fixed, test-only 512-bit RSA key. This weak key is never used outside these
# disposable fixtures and is intentionally unrelated to the owner key.
_TEST_P = int("d6521f405b968742231841635814364b169536d933e6cc9418036f2437b9aa23", 16)
_TEST_Q = int("f23ca1604718bd39318f3288806faa2add35cb82cf8ac728dfdb6371d4264ec5", 16)
_TEST_E = 65537
_TEST_N = _TEST_P * _TEST_Q
_TEST_D = pow(_TEST_E, -1, math.lcm(_TEST_P - 1, _TEST_Q - 1))
_DIGEST_INFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


def _sign_test_claims(document: dict[str, Any]) -> dict[str, Any]:
    signed = dict(document)
    digest_info = _DIGEST_INFO_PREFIX + hashlib.sha256(
        authorization.canonical_claims(signed)
    ).digest()
    size = (_TEST_N.bit_length() + 7) // 8
    padding_length = size - len(digest_info) - 3
    encoded = b"\x00\x01" + b"\xff" * padding_length + b"\x00" + digest_info
    signature = pow(int.from_bytes(encoded, "big"), _TEST_D, _TEST_N).to_bytes(size, "big")
    signed["signature_b64"] = base64.b64encode(signature).decode("ascii")
    return signed


class VerifierFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="cardcade-verifier-trust-")
        self.root = Path(self.temporary.name)
        self.output_root = self.root / "diagnostics"
        self.output_root.mkdir()
        self.auth_root = self.root / "grants"
        self.ledger = self.root / "consumed"
        self.public_key_path = self.root / "mock-public-key.json"
        self.public_key = {
            "modulus_hex": format(_TEST_N, "x"),
            "public_exponent": _TEST_E,
        }
        self.public_key_path.write_text(json.dumps(self.public_key), encoding="utf-8")
        self._old_values = (
            verifier.OUTPUT_ROOT,
            verifier.PUBLIC_KEY_PATH,
            verifier.USED_LEDGER,
        )
        verifier.OUTPUT_ROOT = self.output_root
        verifier.PUBLIC_KEY_PATH = self.public_key_path
        verifier.USED_LEDGER = self.ledger
        self.manifest = batch.create_manifest(
            source_commit=verifier.EXPECTED_COMMIT,
            source_blobs={"stage002.py": "a" * 40},
            baseline_manifest_sha256="b" * 64,
            card_data_sha256="c" * 64,
            runtime={
                "python_version": "3.13.15",
                "python_executable_sha256": "d" * 64,
                "python_nuget_package_sha512": "e" * 128,
                "uv_lock_sha256": "f" * 64,
            },
            supervisor_sha256="1" * 64,
            batch_controller_sha256="2" * 64,
            issuer_sha256="3" * 64,
            output_root=str(self.output_root),
            authorization_root=str(self.auth_root),
            baseline_input_root=str(self.root / "inputs"),
            batch_id="cardcade-smoke10-trusttest",
        )
        self.manifest_sha = batch.digest(self.manifest)
        self.manifest_path = self.root / "manifest.json"
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self._build_successful_disposable_batch()

    def tearDown(self) -> None:
        verifier.OUTPUT_ROOT, verifier.PUBLIC_KEY_PATH, verifier.USED_LEDGER = self._old_values
        self.temporary.cleanup()

    def _build_successful_disposable_batch(self) -> None:
        issued = datetime.now(UTC) - timedelta(minutes=1)
        expires = datetime.now(UTC) + timedelta(hours=1)
        status_games = []
        for index, row in enumerate(self.manifest["games"], 1):
            output = self.output_root / row["run_id"]
            output.mkdir()
            telemetry = output / "telemetry.json"
            telemetry.write_text(json.dumps({"run_id": row["run_id"], "events": []}), encoding="utf-8")
            run_manifest = {
                "run_id": row["run_id"],
                "batch_manifest_sha256": self.manifest_sha,
                "source_commit": verifier.EXPECTED_COMMIT,
                "process_memory_limit_bytes": verifier.EXPECTED_MEMORY,
                "runtime_seconds_limit": verifier.EXPECTED_RUNTIME,
            }
            (output / "run_manifest.json").write_text(json.dumps(run_manifest), encoding="utf-8")
            winner = row["seats"][0]["deck_key"]
            result = {
                "run_id": row["run_id"],
                "seed": row["seed"],
                "completion_state": "COMPLETE",
                "snapshot": {"winner": winner, "turn": 24},
            }
            (output / "result.json").write_text(json.dumps(result), encoding="utf-8")
            artifact_hashes = {
                name: _sha256(output / name)
                for name in ("telemetry.json", "run_manifest.json", "result.json")
            }
            status_games.append(
                {
                    "index": index,
                    "run_id": row["run_id"],
                    "state": "RETURNED",
                    "exit_code": 0,
                    "resource_gate": {
                        "available_physical_bytes": 8_000_000_000,
                        "system_commit_headroom_bytes": 8_000_000_000,
                        "minimum_each_bytes": 2_997_489_664,
                    },
                    "storage_gate": {
                        "file_system": "NTFS",
                        "volume_label": "TMT",
                        "available_bytes": 100_000_000,
                        "required_free_bytes": 1_000_000,
                    },
                    "artifacts_sha256": artifact_hashes,
                }
            )
            grant_doc = {
                **batch.entry_claims(self.manifest, self.manifest_sha, index),
                "schema": "cardcade-stage002-one-game-v1",
                "nonce": f"{index:032x}",
                "issued_utc": issued.isoformat().replace("+00:00", "Z"),
                "expires_utc": expires.isoformat().replace("+00:00", "Z"),
            }
            grant = _sign_test_claims(grant_doc)
            grant_path = Path(row["authorization_file"])
            grant_path.parent.mkdir(parents=True, exist_ok=True)
            grant_path.write_text(json.dumps(grant), encoding="utf-8")
            nonce = grant["nonce"]
            consumed = hashlib.sha256(authorization.canonical_claims(grant)).hexdigest()
            used_path = self.ledger / f"{nonce}.used"
            used_path.parent.mkdir(parents=True, exist_ok=True)
            used_path.write_text(consumed + "\n", encoding="ascii")

        status = {
            "state": "COMPLETE",
            "completed_games": 10,
            "automatic_retries": 0,
            "manifest_sha256": self.manifest_sha,
            "games": status_games,
        }
        status_path = self.output_root / f"{self.manifest['batch_id']}.status.json"
        status_path.write_text(json.dumps(status), encoding="utf-8")

    def _status(self) -> tuple[Path, dict[str, Any]]:
        path = self.output_root / f"{self.manifest['batch_id']}.status.json"
        return path, json.loads(path.read_text(encoding="utf-8"))

    def test_untampered_disposable_batch_verifies(self) -> None:
        result = verifier.verify(self.manifest_path)
        self.assertEqual(result["state"], "VERIFIED_COMPLETE")
        self.assertEqual(result["games_verified"], 10)
        self.assertEqual(result["artifact_hashes_rechecked"], 30)

    def test_altered_result_is_rejected_against_recorded_artifact_hash(self) -> None:
        row = self.manifest["games"][0]
        result_path = self.output_root / row["run_id"] / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["seed"] += 1
        result_path.write_text(json.dumps(result), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "artifact mismatch"):
            verifier.verify(self.manifest_path)

    def test_altered_result_with_rewritten_unsigned_hash_is_accepted(self) -> None:
        row = self.manifest["games"][0]
        result_path = self.output_root / row["run_id"] / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["snapshot"]["winner"] = row["seats"][1]["deck_key"]
        result_path.write_text(json.dumps(result), encoding="utf-8")
        status_path, status = self._status()
        status["games"][0]["artifacts_sha256"]["result.json"] = _sha256(result_path)
        status_path.write_text(json.dumps(status), encoding="utf-8")
        verified = verifier.verify(self.manifest_path)
        self.assertEqual(verified["state"], "VERIFIED_COMPLETE")
        self.assertEqual(verified["outcomes"][0]["winner"], row["seats"][1]["deck_key"])

    def test_altered_telemetry_artifact_is_rejected(self) -> None:
        row = self.manifest["games"][0]
        telemetry_path = self.output_root / row["run_id"] / "telemetry.json"
        telemetry_path.write_text('{"altered":true}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "artifact mismatch"):
            verifier.verify(self.manifest_path)

    def test_empty_artifact_inventory_and_altered_telemetry_are_accepted(self) -> None:
        status_path, status = self._status()
        for record in status["games"]:
            record["artifacts_sha256"] = {}
        status_path.write_text(json.dumps(status), encoding="utf-8")
        row = self.manifest["games"][0]
        (self.output_root / row["run_id"] / "telemetry.json").write_text(
            '{"altered":true}', encoding="utf-8"
        )
        verified = verifier.verify(self.manifest_path)
        self.assertEqual(verified["state"], "VERIFIED_COMPLETE")
        self.assertEqual(verified["artifact_hashes_rechecked"], 0)

    def test_artifact_path_can_escape_assigned_game_directory(self) -> None:
        external = self.root / "outside-assigned-game.bin"
        external.write_bytes(b"disposable external fixture")
        status_path, status = self._status()
        status["games"][0]["artifacts_sha256"]["..\\..\\outside-assigned-game.bin"] = _sha256(
            external
        )
        status_path.write_text(json.dumps(status), encoding="utf-8")
        verified = verifier.verify(self.manifest_path)
        self.assertEqual(verified["state"], "VERIFIED_COMPLETE")

    def test_tampered_authorization_grant_is_rejected(self) -> None:
        grant_path = Path(self.manifest["games"][0]["authorization_file"])
        grant = json.loads(grant_path.read_text(encoding="utf-8"))
        grant["seed"] += 1
        grant_path.write_text(json.dumps(grant), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "signature verification failed"):
            verifier.verify(self.manifest_path)

    def test_missing_consumption_record_is_rejected(self) -> None:
        nonce = "00000000000000000000000000000001"
        (self.ledger / f"{nonce}.used").unlink()
        with self.assertRaisesRegex(ValueError, "consumption record is missing or wrong"):
            verifier.verify(self.manifest_path)

    def test_altered_consumption_record_is_rejected(self) -> None:
        nonce = "00000000000000000000000000000001"
        (self.ledger / f"{nonce}.used").write_text("0" * 64 + "\n", encoding="ascii")
        with self.assertRaisesRegex(ValueError, "consumption record is missing or wrong"):
            verifier.verify(self.manifest_path)

