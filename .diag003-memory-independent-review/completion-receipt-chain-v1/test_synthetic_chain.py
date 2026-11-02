"""Deterministic end-to-end proof for the non-production receipt-chain model."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import math
import random
import re
import sys
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType
from typing import Any

from synthetic_candidate import (
    ATTESTATION_PURPOSE,
    RECEIPT_PURPOSE,
    CompletionReceiptIssuer,
    EvidenceSnapshot,
    TrustValidationError,
    create_execution_attestation,
    verify_completion_receipt,
)

ROOT = Path(__file__).resolve().parents[1] / "verifier-trust-review"
SOURCE = ROOT / "sources"
EXPECTED = {
    "stage002_authorization.py": "1fd4db87131a0fef996fc2df7aee5f6634fdbc2d7b90f226c76217596fdb6540",
    "stage002_batch.py": "30720c8d720b52a9538b79063d785e57dc37762bf5099215b7ee05cef0a80293",
}
_SHA_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")
_NOW = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned test dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


for _filename, _expected in EXPECTED.items():
    if _sha((SOURCE / _filename).read_bytes()) != _expected:
        raise RuntimeError(f"test dependency identity mismatch: {_filename}")
auth = _load("receipt_chain_test_auth", SOURCE / "stage002_authorization.py")
batch = _load("receipt_chain_test_batch", SOURCE / "stage002_batch.py")


def _probable_prime(candidate: int, rng: random.Random) -> bool:
    if candidate % 2 == 0:
        return False
    d = candidate - 1
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2
    for base in (
        2,
        3,
        5,
        7,
        11,
        13,
        17,
        19,
        23,
        29,
        31,
        37,
        *[rng.randrange(2, candidate - 2) for _ in range(8)],
    ):
        value = pow(base, d, candidate)
        if value in (1, candidate - 1):
            continue
        for _ in range(s - 1):
            value = pow(value, 2, candidate)
            if value == candidate - 1:
                break
        else:
            return False
    return True


def _test_rsa(seed: int) -> tuple[dict[str, Any], int]:
    rng = random.Random(seed)
    factors = []
    for _ in range(2):
        while True:
            candidate = rng.getrandbits(256) | (1 << 255) | 1
            if _probable_prime(candidate, rng):
                factors.append(candidate)
                break
    p, q = factors
    e = 65537
    n = p * q
    d = pow(e, -1, math.lcm(p - 1, q - 1))
    return {"modulus_hex": format(n, "x"), "public_exponent": e}, d


def _rsa_sign(payload: bytes, private: int, public: dict[str, Any]) -> str:
    modulus = int(public["modulus_hex"], 16)
    size = (modulus.bit_length() + 7) // 8
    digest_info = _SHA_PREFIX + hashlib.sha256(payload).digest()
    pad = size - len(digest_info) - 3
    encoded = b"\x00\x01" + b"\xff" * pad + b"\x00" + digest_info
    return base64.b64encode(
        pow(int.from_bytes(encoded, "big"), private, modulus).to_bytes(size, "big")
    ).decode("ascii")


def _sign_document(
    document: dict[str, Any],
    private: int,
    public: dict[str, Any] | None = None,
    module: Any = auth,
) -> dict[str, Any]:
    signed = dict(document)
    signed["signature_b64"] = _rsa_sign(
        module.canonical_claims(signed), private, public or AUTH_PUB
    )
    return signed


AUTH_PUB, AUTH_D = _test_rsa(37001)
ATTEST_PUB, ATTEST_D = _test_rsa(37002)
RECEIPT_PUB, RECEIPT_D = _test_rsa(37003)


class TestSigner:
    def __init__(self, public: dict[str, Any], private: int, key_id: str, purpose: str) -> None:
        self.public = public
        self.private = private
        self.key_id = key_id
        self.purpose = purpose
        self.public_key_sha256 = _sha(
            json.dumps(public, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
        self.sign_calls = 0

    def sign(self, payload: bytes) -> str:
        self.sign_calls += 1
        return _rsa_sign(payload, self.private, self.public)


class NoReplacePublisher:
    """Test-only atomic-publication model with failure injection."""

    def __init__(self, *, existing: bytes | None = None, interrupt: bool = False) -> None:
        self.final = existing
        self.temporary: bytes | None = None
        self.interrupt = interrupt
        self.reserved = False

    def reserve_no_replace(self) -> None:
        if self.final is not None or self.reserved:
            raise FileExistsError("receipt destination already exists or is reserved")
        self.reserved = True

    def publish_no_replace(self, payload: bytes) -> None:
        if self.final is not None or not self.reserved:
            raise FileExistsError("receipt destination is occupied or not reserved")
        self.temporary = payload
        if self.interrupt:
            raise OSError("injected interruption before atomic rename")
        self.final = self.temporary
        self.temporary = None


class UnavailableTestSigner(TestSigner):
    def sign(self, payload: bytes) -> str:
        self.sign_calls += 1
        raise OSError("injected test-key unavailability")


class SyntheticChain(unittest.TestCase):
    def setUp(self) -> None:
        self.base = Path(__file__).resolve().parent
        self.manifest = batch.create_manifest(
            source_commit="32a80228714674327aca62f8b86b70c4c4afc929",
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
            output_root=str(self.base / "synthetic-output"),
            authorization_root=str(self.base / "synthetic-grants"),
            baseline_input_root=str(self.base / "synthetic-inputs"),
            batch_id="cardcade-smoke10-trust-chain-test",
        )
        self.manifest_sha = batch.digest(self.manifest)
        self.snapshot = self._build_snapshot()
        self.receipt_signer = TestSigner(
            RECEIPT_PUB, RECEIPT_D, "test-receipt-key-003", RECEIPT_PURPOSE
        )

    def _build_snapshot(self) -> EvidenceSnapshot:
        attestor = TestSigner(ATTEST_PUB, ATTEST_D, "test-supervisor-key-002", ATTESTATION_PURPOSE)
        games: dict[str, MappingProxyType] = {}
        attestations: dict[str, bytes] = {}
        grants: dict[str, bytes] = {}
        ledger: dict[str, bytes] = {}
        records = []
        issued = (_NOW - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
        expires = (_NOW + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        for index, row in enumerate(self.manifest["games"], start=1):
            run_id = row["run_id"]
            deck_hashes = {seat["deck_key"]: seat["sha256"] for seat in row["seats"]}
            result = {
                "label": "DIAGNOSTIC",
                "run_id": run_id,
                "source_commit": self.manifest["source_commit"],
                "source_blobs": self.manifest["source_blobs"],
                "pairing_id": row["pairing_id"],
                "seed": row["seed"],
                "orientation": row["orientation"],
                "seats": [seat["deck_key"] for seat in row["seats"]],
                "deck_sha256": deck_hashes,
                "completion_state": "COMPLETE",
                "snapshot": {
                    "winner": row["seats"][0]["deck_key"],
                    "turn": 25,
                    "events": [],
                    "stage002_presence": [],
                },
            }
            run_manifest = {
                "run_id": run_id,
                "batch_manifest_sha256": self.manifest_sha,
                "source_commit": self.manifest["source_commit"],
                "process_memory_limit_bytes": 2_997_489_664,
                "runtime_seconds_limit": 600,
                "seed": row["seed"],
                "orientation": row["orientation"],
                "deck_sha256": deck_hashes,
            }
            files = {
                "status.json": json.dumps(
                    {"label": "DIAGNOSTIC", "state": "RETURNED", "child_exit_code": 0},
                    sort_keys=True,
                ).encode(),
                "run_manifest.json": json.dumps(run_manifest, sort_keys=True).encode(),
                "result.json": json.dumps(result, sort_keys=True).encode(),
                "stdout.log": b"test-only worker output\n",
                "stderr.log": b"",
                "telemetry.json": b'{"events":[]}\n',
            }
            inventory = {name: _sha(content) for name, content in files.items()}
            games[run_id] = MappingProxyType(files)
            grant = {
                **batch.entry_claims(self.manifest, self.manifest_sha, index),
                "schema": "cardcade-stage002-one-game-v1",
                "nonce": f"{index:032x}",
                "issued_utc": issued,
                "expires_utc": expires,
            }
            signed_grant = _sign_document(grant, AUTH_D)
            grants[run_id] = json.dumps(signed_grant, sort_keys=True).encode()
            grant_digest = _sha(auth.canonical_claims(signed_grant))
            ledger[signed_grant["nonce"]] = (grant_digest + "\n").encode("ascii")
            attestation = {
                "batch_id": self.manifest["batch_id"],
                "manifest_sha256": self.manifest_sha,
                "index": index,
                "run_id": run_id,
                "grant_sha256": grant_digest,
                "nonce": signed_grant["nonce"],
                "source_commit": self.manifest["source_commit"],
                "supervisor_sha256": self.manifest["supervisor_sha256"],
                "runtime_sha256": self.manifest["runtime"]["python_executable_sha256"],
                "exit_code": 0,
                "memory_limit_bytes": 2_997_489_664,
                "runtime_limit_seconds": 600,
                "artifacts_sha256": inventory,
            }
            attestations[run_id] = json.dumps(
                create_execution_attestation(attestation, attestor), sort_keys=True
            ).encode()
            records.append(
                {
                    "index": index,
                    "run_id": run_id,
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
                        "available_bytes": 50_000_000,
                        "required_free_bytes": 1_000_000,
                    },
                    "artifacts_sha256": inventory,
                }
            )
        status = {
            "label": "DIAGNOSTIC",
            "state": "COMPLETE",
            "completed_games": 10,
            "automatic_retries": 0,
            "manifest_sha256": self.manifest_sha,
            "games": records,
        }
        return EvidenceSnapshot(
            manifest_raw=json.dumps(self.manifest, sort_keys=True).encode(),
            status_raw=json.dumps(status, sort_keys=True).encode(),
            artifacts=MappingProxyType(games),
            attestations_raw=MappingProxyType(attestations),
            grants_raw=MappingProxyType(grants),
            consumption_raw=MappingProxyType(ledger),
        )

    def _issuer(self, signer: TestSigner | None = None) -> CompletionReceiptIssuer:
        def verify(document: dict[str, Any], key: Mapping[str, Any]) -> None:
            auth.verify_rsa_sha256(document, dict(key))

        def verify_grant(document: dict[str, Any], expected: dict[str, Any]) -> str:
            return auth.verify_claims(document, AUTH_PUB, expected, now=_NOW)

        return CompletionReceiptIssuer(
            approved_manifest_sha256=self.manifest_sha,
            expected_source_commit=self.manifest["source_commit"],
            expected_supervisor_sha256=self.manifest["supervisor_sha256"],
            expected_runtime_sha256=self.manifest["runtime"]["python_executable_sha256"],
            authorization_public_key=AUTH_PUB,
            attestation_public_key=ATTEST_PUB,
            authorization_key_id="test-authorization-key-001",
            attestation_key_id="test-supervisor-key-002",
            expected_receipt_public_key_sha256=_key_sha(RECEIPT_PUB),
            receipt_signer=signer or self.receipt_signer,
            verify_signature=verify,
            verify_grant_claims=verify_grant,
            canonical_claims=auth.canonical_claims,
            digest_manifest=batch.digest,
            entry_claims=batch.entry_claims,
        )

    def _replace_status(self, status: dict[str, Any]) -> EvidenceSnapshot:
        return replace(self.snapshot, status_raw=json.dumps(status, sort_keys=True).encode())

    def _status(self) -> dict[str, Any]:
        return json.loads(self.snapshot.status_raw)

    def test_complete_ten_game_chain_issues_distinctly_signed_receipt(self) -> None:
        publisher = NoReplacePublisher()
        receipt = self._issuer().issue_and_publish(self.snapshot, publisher)
        self.assertEqual(receipt["completed_games"], 10)
        self.assertIsNotNone(publisher.final)
        self.assertEqual(json.loads(publisher.final), receipt)
        verify_completion_receipt(
            receipt,
            batch_id=self.manifest["batch_id"],
            manifest_sha256=self.manifest_sha,
            status_raw=self.snapshot.status_raw,
            completed_games=10,
            receipt_public_key=RECEIPT_PUB,
            expected_receipt_key_sha256=_key_sha(RECEIPT_PUB),
            verify_signature=lambda doc, key: auth.verify_rsa_sha256(doc, dict(key)),
        )
        self.assertEqual(self.receipt_signer.sign_calls, 1)
        self.assertNotEqual(self.receipt_signer.public_key_sha256, _key_sha(AUTH_PUB))
        self.assertNotEqual(self.receipt_signer.public_key_sha256, _key_sha(ATTEST_PUB))

    def test_modified_result_and_recomputed_unsigned_hashes_fail_before_signing(self) -> None:
        run_id = self.manifest["games"][0]["run_id"]
        files = dict(self.snapshot.artifacts[run_id])
        result = json.loads(files["result.json"])
        result["snapshot"]["winner"] = self.manifest["games"][0]["seats"][1]["deck_key"]
        files["result.json"] = json.dumps(result, sort_keys=True).encode()
        inventory = {name: _sha(content) for name, content in files.items()}
        artifacts = dict(self.snapshot.artifacts)
        artifacts[run_id] = MappingProxyType(files)
        status = self._status()
        status["games"][0]["artifacts_sha256"] = inventory
        snapshot = replace(
            self.snapshot,
            artifacts=MappingProxyType(artifacts),
            status_raw=json.dumps(status, sort_keys=True).encode(),
        )
        signer = self.receipt_signer
        with self.assertRaises(TrustValidationError):
            self._issuer(signer).issue(snapshot)
        self.assertEqual(signer.sign_calls, 0)

    def test_incomplete_batch_fails_before_signing(self) -> None:
        status = self._status()
        status["completed_games"] = 9
        status["games"] = status["games"][:-1]
        signer = self.receipt_signer
        with self.assertRaises(TrustValidationError):
            self._issuer(signer).issue(self._replace_status(status))
        self.assertEqual(signer.sign_calls, 0)

    def test_missing_required_artifact_fails_before_signing(self) -> None:
        run_id = self.manifest["games"][0]["run_id"]
        artifacts = dict(self.snapshot.artifacts)
        files = dict(artifacts[run_id])
        del files["result.json"]
        artifacts[run_id] = MappingProxyType(files)
        signer = self.receipt_signer
        with self.assertRaises(TrustValidationError):
            self._issuer(signer).issue(
                replace(self.snapshot, artifacts=MappingProxyType(artifacts))
            )
        self.assertEqual(signer.sign_calls, 0)

    def test_bad_supervisor_attestation_signature_fails_before_signing(self) -> None:
        attestations = dict(self.snapshot.attestations_raw)
        run_id = self.manifest["games"][0]["run_id"]
        doc = json.loads(attestations[run_id])
        doc["exit_code"] = 1
        attestations[run_id] = json.dumps(doc, sort_keys=True).encode()
        signer = self.receipt_signer
        with self.assertRaises(ValueError):
            self._issuer(signer).issue(
                replace(self.snapshot, attestations_raw=MappingProxyType(attestations))
            )
        self.assertEqual(signer.sign_calls, 0)

    def test_tampered_grant_or_consumption_fails_before_signing(self) -> None:
        run_id = self.manifest["games"][0]["run_id"]
        grants = dict(self.snapshot.grants_raw)
        grant = json.loads(grants[run_id])
        grant["seed"] += 1
        grants[run_id] = json.dumps(grant).encode()
        signer = self.receipt_signer
        altered = replace(self.snapshot, grants_raw=MappingProxyType(grants))
        with self.assertRaises(ValueError):
            self._issuer(signer).issue(altered)
        self.assertEqual(signer.sign_calls, 0)
        nonce = f"{1:032x}"
        ledger = dict(self.snapshot.consumption_raw)
        ledger[nonce] = b"0" * 64 + b"\n"
        with self.assertRaises(TrustValidationError):
            self._issuer(signer).issue(
                replace(self.snapshot, consumption_raw=MappingProxyType(ledger))
            )
        self.assertEqual(signer.sign_calls, 0)

    def test_path_escape_fails_before_signing(self) -> None:
        run_id = self.manifest["games"][0]["run_id"]
        files = dict(self.snapshot.artifacts[run_id])
        files["..\\outside.bin"] = b"outside"
        artifacts = dict(self.snapshot.artifacts)
        artifacts[run_id] = MappingProxyType(files)
        signer = self.receipt_signer
        with self.assertRaises(TrustValidationError):
            self._issuer(signer).issue(
                replace(self.snapshot, artifacts=MappingProxyType(artifacts))
            )
        self.assertEqual(signer.sign_calls, 0)

    def test_receipt_key_substitution_fails_and_wrong_verifier_key_rejects(self) -> None:
        same_key_signer = TestSigner(
            AUTH_PUB, AUTH_D, "test-authorization-key-001", RECEIPT_PURPOSE
        )
        with self.assertRaisesRegex(TrustValidationError, "receipt signing key differs"):
            self._issuer(same_key_signer).issue(self.snapshot)
        self.assertEqual(same_key_signer.sign_calls, 0)
        receipt = self._issuer().issue(self.snapshot)
        with self.assertRaises(ValueError):
            verify_completion_receipt(
                receipt,
                batch_id=self.manifest["batch_id"],
                manifest_sha256=self.manifest_sha,
                status_raw=self.snapshot.status_raw,
                completed_games=10,
                receipt_public_key=AUTH_PUB,
                expected_receipt_key_sha256=_key_sha(AUTH_PUB),
                verify_signature=lambda doc, key: auth.verify_rsa_sha256(doc, dict(key)),
            )

    def test_existing_receipt_and_interrupted_publish_fail_without_final_receipt(self) -> None:
        existing = NoReplacePublisher(existing=b"existing receipt")
        signer = TestSigner(RECEIPT_PUB, RECEIPT_D, "test-receipt-key-003", RECEIPT_PURPOSE)
        with self.assertRaisesRegex(TrustValidationError, "cannot be reserved"):
            self._issuer(signer).issue_and_publish(self.snapshot, existing)
        self.assertEqual(existing.final, b"existing receipt")
        self.assertEqual(signer.sign_calls, 0)
        interrupted = NoReplacePublisher(interrupt=True)
        with self.assertRaisesRegex(OSError, "injected interruption"):
            self._issuer().issue_and_publish(self.snapshot, interrupted)
        self.assertIsNone(interrupted.final)
        self.assertIsNotNone(interrupted.temporary)

    def test_missing_signing_key_fails_without_publishing_receipt(self) -> None:
        signer = UnavailableTestSigner(
            RECEIPT_PUB, RECEIPT_D, "test-receipt-key-003", RECEIPT_PURPOSE
        )
        publisher = NoReplacePublisher()
        with self.assertRaisesRegex(OSError, "key unavailability"):
            self._issuer(signer).issue_and_publish(self.snapshot, publisher)
        self.assertEqual(signer.sign_calls, 1)
        self.assertIsNone(publisher.final)


def _key_sha(public: dict[str, Any]) -> str:
    return _sha(json.dumps(public, sort_keys=True, separators=(",", ":")).encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
