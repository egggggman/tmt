"""Deterministic trust-boundary tests for the corrected batch verifier."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

REVIEW_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = REVIEW_ROOT / "sources"
CORRECTED_ROOT = REVIEW_ROOT / "corrected"
SOURCE_HASHES = {
    "stage002_authorization.py": "1fd4db87131a0fef996fc2df7aee5f6634fdbc2d7b90f226c76217596fdb6540",
    "stage002_batch.py": "30720c8d720b52a9538b79063d785e57dc37762bf5099215b7ee05cef0a80293",
}
_P = int("d6521f405b968742231841635814364b169536d933e6cc9418036f2437b9aa23", 16)
_Q = int("f23ca1604718bd39318f3288806faa2add35cb82cf8ac728dfdb6371d4264ec5", 16)
_E = 65537
_N = _P * _Q
_D = pow(_E, -1, math.lcm(_P - 1, _Q - 1))
_DIGEST_INFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256(path.read_bytes())


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load test source {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sign(document: dict[str, Any], auth_module: Any) -> dict[str, Any]:
    signed = dict(document)
    digest_info = (
        _DIGEST_INFO_PREFIX + hashlib.sha256(auth_module.canonical_claims(signed)).digest()
    )
    key_size = (_N.bit_length() + 7) // 8
    padding_length = key_size - len(digest_info) - 3
    encoded = b"\x00\x01" + b"\xff" * padding_length + b"\x00" + digest_info
    signature = pow(int.from_bytes(encoded, "big"), _D, _N).to_bytes(key_size, "big")
    signed["signature_b64"] = base64.b64encode(signature).decode("ascii")
    return signed


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


for _name, _expected in SOURCE_HASHES.items():
    if _sha256_file(SOURCE_ROOT / _name) != _expected:
        raise RuntimeError(f"source-copy SHA-256 mismatch: {_name}")

auth = _load_module("test_pinned_stage002_authorization", SOURCE_ROOT / "stage002_authorization.py")
batch = _load_module("test_pinned_stage002_batch", SOURCE_ROOT / "stage002_batch.py")
verifier = _load_module("corrected_batch_verifier", CORRECTED_ROOT / "verify_completed_batch.py")


class CorrectedVerifierFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="cardcade-corrected-verifier-")
        self.root = Path(self.temporary.name)
        self.output_root = self.root / "diagnostics"
        self.output_root.mkdir()
        self.auth_root = self.root / "grants"
        self.used_ledger = self.root / "consumed"
        self.public_key_path = self.root / "mock-public-key.json"
        self.public_key = {"modulus_hex": format(_N, "x"), "public_exponent": _E}
        _write_json(self.public_key_path, self.public_key)
        self.public_key_hash = _sha256_file(self.public_key_path)
        self.dependencies = self.root / "dependencies"
        self.dependencies.mkdir()
        for name in SOURCE_HASHES:
            shutil.copyfile(SOURCE_ROOT / name, self.dependencies / name)
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
            batch_id="cardcade-smoke10-correctedtrust",
        )
        self.manifest_sha = batch.digest(self.manifest)
        self.manifest_path = self.root / "manifest.json"
        _write_json(self.manifest_path, self.manifest)
        self.status_path, self.status = self._create_batch()
        self.receipt_path = (
            self.output_root / f"{self.manifest['batch_id']}.completion-receipt.json"
        )
        self._write_receipt()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _create_batch(self) -> tuple[Path, dict[str, Any]]:
        issued = datetime.now(UTC) - timedelta(minutes=1)
        expires = datetime.now(UTC) + timedelta(hours=1)
        status_games = []
        for index, row in enumerate(self.manifest["games"], 1):
            output = self.output_root / row["run_id"]
            output.mkdir()
            per_game_status = {"label": "DIAGNOSTIC", "state": "RETURNED", "child_exit_code": 0}
            run = {
                "label": "DIAGNOSTIC",
                "run_id": row["run_id"],
                "batch_manifest_sha256": self.manifest_sha,
                "source_commit": verifier.EXPECTED_COMMIT,
                "process_memory_limit_bytes": verifier.EXPECTED_MEMORY,
                "runtime_seconds_limit": verifier.EXPECTED_RUNTIME,
                "seed": row["seed"],
                "orientation": row["orientation"],
                "deck_sha256": {seat["deck_key"]: seat["sha256"] for seat in row["seats"]},
            }
            result = {
                "label": "DIAGNOSTIC",
                "run_id": row["run_id"],
                "source_commit": verifier.EXPECTED_COMMIT,
                "source_blobs": self.manifest["source_blobs"],
                "pairing_id": row["pairing_id"],
                "seed": row["seed"],
                "orientation": row["orientation"],
                "seats": [seat["deck_key"] for seat in row["seats"]],
                "deck_sha256": {seat["deck_key"]: seat["sha256"] for seat in row["seats"]},
                "completion_state": "COMPLETE",
                "snapshot": {
                    "winner": row["seats"][0]["deck_key"],
                    "turn": 24,
                    "events": [],
                    "stage002_presence": [],
                },
            }
            _write_json(output / "status.json", per_game_status)
            _write_json(output / "run_manifest.json", run)
            _write_json(output / "result.json", result)
            (output / "stdout.log").write_bytes(b"mock worker stdout\n")
            (output / "stderr.log").write_bytes(b"")
            artifacts = {
                name: _sha256_file(output / name) for name in verifier.REQUIRED_COMPLETED_ARTIFACTS
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
                    "artifacts_sha256": artifacts,
                }
            )
            grant = {
                **batch.entry_claims(self.manifest, self.manifest_sha, index),
                "schema": "cardcade-stage002-one-game-v1",
                "nonce": f"{index:032x}",
                "issued_utc": issued.isoformat().replace("+00:00", "Z"),
                "expires_utc": expires.isoformat().replace("+00:00", "Z"),
            }
            signed_grant = _sign(grant, auth)
            grant_path = Path(row["authorization_file"])
            _write_json(grant_path, signed_grant)
            claim_digest = hashlib.sha256(auth.canonical_claims(signed_grant)).hexdigest()
            ledger_path = self.used_ledger / f"{signed_grant['nonce']}.used"
            ledger_path.parent.mkdir(parents=True, exist_ok=True)
            ledger_path.write_text(claim_digest + "\n", encoding="ascii")

        status = {
            "state": "COMPLETE",
            "completed_games": 10,
            "automatic_retries": 0,
            "manifest_sha256": self.manifest_sha,
            "games": status_games,
        }
        status_path = self.output_root / f"{self.manifest['batch_id']}.status.json"
        _write_json(status_path, status)
        return status_path, status

    def _write_receipt(self) -> None:
        receipt = {
            "schema": verifier.RECEIPT_SCHEMA,
            "batch_id": self.manifest["batch_id"],
            "manifest_sha256": self.manifest_sha,
            "status_sha256": _sha256_file(self.status_path),
            "completed_games": 10,
        }
        _write_json(self.receipt_path, _sign(receipt, auth))

    def _verify(self) -> dict[str, Any]:
        return verifier.verify(
            self.manifest_path,
            output_root=self.output_root,
            public_key_path=self.public_key_path,
            used_ledger=self.used_ledger,
            dependency_root=self.dependencies,
            expected_dependency_hashes=SOURCE_HASHES,
            expected_public_key_sha256=self.public_key_hash,
            expected_public_key_bits=512,
        )

    def _resign_status(self) -> None:
        _write_json(self.status_path, self.status)
        self._write_receipt()

    def test_complete_untampered_batch_verifies(self) -> None:
        result = self._verify()
        self.assertEqual(result["state"], "VERIFIED_COMPLETE")
        self.assertEqual(result["games_verified"], 10)
        self.assertEqual(result["artifact_hashes_rechecked"], 50)

    def test_modified_result_with_unchanged_status_is_rejected(self) -> None:
        row = self.manifest["games"][0]
        path = self.output_root / row["run_id"] / "result.json"
        altered = json.loads(path.read_text(encoding="utf-8"))
        altered["seed"] += 5
        _write_json(path, altered)
        with self.assertRaisesRegex(verifier.VerificationError, "artifact hash mismatch"):
            self._verify()

    def test_modified_result_with_recomputed_unsigned_status_hash_is_rejected(self) -> None:
        row = self.manifest["games"][0]
        result_path = self.output_root / row["run_id"] / "result.json"
        altered = json.loads(result_path.read_text(encoding="utf-8"))
        altered["seed"] += 5
        _write_json(result_path, altered)
        record = self.status["games"][0]
        record["artifacts_sha256"]["result.json"] = _sha256_file(result_path)
        self._resign_status_without_signature()
        with self.assertRaisesRegex(verifier.VerificationError, "completion receipt"):
            self._verify()

    def _resign_status_without_signature(self) -> None:
        _write_json(self.status_path, self.status)

    def test_empty_artifact_inventory_is_rejected(self) -> None:
        self.status["games"][0]["artifacts_sha256"] = {}
        self._resign_status()
        with self.assertRaisesRegex(verifier.VerificationError, "no artifact inventory"):
            self._verify()

    def test_missing_required_artifact_is_rejected(self) -> None:
        row = self.manifest["games"][0]
        (self.output_root / row["run_id"] / "stderr.log").unlink()
        self.status["games"][0]["artifacts_sha256"].pop("stderr.log")
        self._resign_status()
        with self.assertRaises(verifier.VerificationError):
            self._verify()

    def test_path_traversal_is_rejected(self) -> None:
        outside = self.root / "outside.bin"
        outside.write_bytes(b"disposable only")
        self.status["games"][0]["artifacts_sha256"]["..\\..\\outside.bin"] = _sha256_file(outside)
        self._resign_status()
        with self.assertRaisesRegex(verifier.VerificationError, "traversal"):
            self._verify()

    def test_absolute_and_out_of_tree_paths_are_rejected(self) -> None:
        outside = self.root / "outside.bin"
        outside.write_bytes(b"disposable only")
        self.status["games"][0]["artifacts_sha256"][str(outside)] = _sha256_file(outside)
        self._resign_status()
        with self.assertRaisesRegex(verifier.VerificationError, "absolute artifact path"):
            self._verify()

        self.status["games"][0]["artifacts_sha256"].pop(str(outside))
        self.status["games"][0]["artifacts_sha256"]["nested\\missing.bin"] = "a" * 64
        self._resign_status()
        with self.assertRaises(verifier.VerificationError):
            self._verify()

    def test_symlink_escape_is_rejected(self) -> None:
        row = self.manifest["games"][0]
        output = self.output_root / row["run_id"]
        external = self.root / "outside-link-target.bin"
        external.write_bytes(b"disposable link target")
        link = output / "telemetry-link.bin"
        try:
            os.symlink(external, link)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"filesystem denied disposable symlink creation: {exc}")
        self.status["games"][0]["artifacts_sha256"]["telemetry-link.bin"] = _sha256_file(external)
        self._resign_status()
        with self.assertRaises(verifier.VerificationError):
            self._verify()

    @unittest.skipUnless(sys.platform == "win32", "junction creation uses Windows PowerShell")
    def test_windows_junction_escape_is_rejected(self) -> None:
        row = self.manifest["games"][0]
        output = self.output_root / row["run_id"]
        target = self.root / "junction-target"
        target.mkdir()
        (target / "escape.bin").write_bytes(b"disposable junction target")
        junction = output / "junction"
        command = (
            f"New-Item -ItemType Junction -Path '{junction}' -Target '{target}' "
            "-ErrorAction Stop | Out-Null"
        )
        created = subprocess.run(
            ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            check=False,
        )
        if created.returncode != 0:
            self.skipTest(f"could not create disposable Windows junction: {created.stderr}")
        self.status["games"][0]["artifacts_sha256"]["junction\\escape.bin"] = _sha256_file(
            target / "escape.bin"
        )
        self._resign_status()
        try:
            with self.assertRaises(verifier.VerificationError):
                self._verify()
        finally:
            os.rmdir(junction)

    def test_modified_dependency_is_rejected_before_import(self) -> None:
        dependency = self.dependencies / "stage002_batch.py"
        dependency.write_bytes(dependency.read_bytes() + b"\n# altered\n")
        with self.assertRaisesRegex(verifier.VerificationError, "dependency identity mismatch"):
            self._verify()

    def test_wrapper_pins_corrected_verifier_and_integrity_helper_before_issuance(self) -> None:
        batch_root = Path(__file__).resolve().parents[1] / "300-game-exploratory-r1"
        wrapper_path = batch_root / "execute_approved_batch.integrity-v3.ps1"
        helper_path = batch_root / "batch_integrity_validation.integrity-v2.py"
        wrapper = wrapper_path.read_text(encoding="utf-8")
        helper = helper_path.read_text(encoding="utf-8")
        verifier_path = CORRECTED_ROOT / "verify_completed_batch.py"
        verifier_source = verifier_path.read_text(encoding="utf-8")
        self.assertIn(f"$expectedVerifier = '{_sha256_file(verifier_path)}'", wrapper)
        self.assertIn(f"$expectedIntegrityHelper = '{_sha256_file(helper_path)}'", wrapper)
        self.assertIn(f'EXPECTED_VERIFIER_SHA256 = "{_sha256_file(verifier_path)}"', helper)
        self.assertIn(
            f'"stage002_authorization.py": "{SOURCE_HASHES["stage002_authorization.py"]}"',
            verifier_source,
        )
        self.assertIn(
            f'"stage002_batch.py": "{SOURCE_HASHES["stage002_batch.py"]}"', verifier_source
        )
        integrity_gate = wrapper.index("Schedule/repository integrity preflight failed")
        first_grant = wrapper.index("--issue-batch")
        self.assertLess(integrity_gate, first_grant)

    def test_unexpected_public_key_is_rejected(self) -> None:
        self.public_key_path.write_bytes(self.public_key_path.read_bytes() + b"\n")
        with self.assertRaisesRegex(verifier.VerificationError, "public-key identity mismatch"):
            self._verify()

    def test_tampered_authorization_grant_is_rejected(self) -> None:
        grant_path = Path(self.manifest["games"][0]["authorization_file"])
        grant = json.loads(grant_path.read_text(encoding="utf-8"))
        grant["seed"] += 7
        _write_json(grant_path, grant)
        with self.assertRaisesRegex(ValueError, "signature verification failed"):
            self._verify()

    def test_missing_consumption_record_is_rejected(self) -> None:
        (self.used_ledger / f"{1:032x}.used").unlink()
        with self.assertRaises(verifier.VerificationError):
            self._verify()

    def test_modified_consumption_record_is_rejected(self) -> None:
        (self.used_ledger / f"{1:032x}.used").write_text("0" * 64, encoding="ascii")
        with self.assertRaisesRegex(verifier.VerificationError, "consumption record"):
            self._verify()


if __name__ == "__main__":
    unittest.main()
