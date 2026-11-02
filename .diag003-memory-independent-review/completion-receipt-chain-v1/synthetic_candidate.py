"""Non-production model of the Stage 002 completion-receipt trust chain.

This module deliberately has no key loading, CNG access, filesystem snapshot,
Windows service, or production publication implementation. A caller must
provide an immutable evidence snapshot and purpose-separated signer provider.
It is a reviewable synthetic design candidate only.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

RECEIPT_SCHEMA = "cardcade-stage002-batch-completion-v1"
RECEIPT_PURPOSE = "cardcade-stage002-batch-completion-v1"
ATTESTATION_SCHEMA = "cardcade-stage002-game-execution-attestation-v1"
ATTESTATION_PURPOSE = "cardcade-stage002-game-execution-attestation-v1"
REQUIRED_ARTIFACTS = frozenset(
    {"status.json", "run_manifest.json", "result.json", "stdout.log", "stderr.log"}
)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class TrustValidationError(ValueError):
    """Fail-closed synthetic trust-chain validation error."""


class Signer(Protocol):
    purpose: str
    key_id: str
    public_key_sha256: str

    def sign(self, payload: bytes) -> str: ...


@dataclass(frozen=True)
class EvidenceSnapshot:
    """Caller-provided immutable byte snapshot; production capture is separate."""

    manifest_raw: bytes
    status_raw: bytes
    # Keyed by relative file path; each value is an exact captured byte string.
    artifacts: Mapping[str, Mapping[str, bytes]]
    attestations_raw: Mapping[str, bytes]
    grants_raw: Mapping[str, bytes]
    # Nonce -> ASCII hex digest record bytes, captured from protected ledger.
    consumption_raw: Mapping[str, bytes]


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _document(raw: bytes, label: str) -> dict[str, Any]:
    try:
        obj = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TrustValidationError(f"{label} is invalid JSON") from exc
    if not isinstance(obj, dict):
        raise TrustValidationError(f"{label} must be a JSON object")
    return obj


def _safe_path(relative: str) -> None:
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise TrustValidationError("artifact path is malformed")
    # Reject both POSIX and Windows absolute/drive forms and normalize both
    # separator styles before checking traversal components.
    if relative.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", relative):
        raise TrustValidationError("absolute or drive-qualified artifact path")
    parts = relative.replace("/", "\\").split("\\")
    if any(part in {"", ".", ".."} or ":" in part for part in parts):
        raise TrustValidationError("artifact traversal or alternate stream path")


def _unsigned(document: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in document.items() if k != "signature_b64"}


class CompletionReceiptIssuer:
    """Validate a captured batch before asking a dedicated signer to sign it."""

    def __init__(
        self,
        *,
        approved_manifest_sha256: str,
        expected_source_commit: str,
        expected_supervisor_sha256: str,
        expected_runtime_sha256: str,
        authorization_public_key: Mapping[str, Any],
        attestation_public_key: Mapping[str, Any],
        authorization_key_id: str,
        attestation_key_id: str,
        expected_receipt_public_key_sha256: str,
        receipt_signer: Signer,
        verify_signature: Callable[[dict[str, Any], Mapping[str, Any]], None],
        verify_grant_claims: Callable[[dict[str, Any], dict[str, Any]], str],
        canonical_claims: Callable[[dict[str, Any]], bytes],
        digest_manifest: Callable[[dict[str, Any]], str],
        entry_claims: Callable[[dict[str, Any], str, int], dict[str, Any]],
        expected_games: int = 10,
        memory_limit_bytes: int = 2_997_489_664,
        runtime_limit_seconds: int = 600,
    ) -> None:
        self.approved_manifest_sha256 = approved_manifest_sha256
        self.expected_source_commit = expected_source_commit
        self.expected_supervisor_sha256 = expected_supervisor_sha256
        self.expected_runtime_sha256 = expected_runtime_sha256
        self.authorization_public_key = authorization_public_key
        self.attestation_public_key = attestation_public_key
        self.authorization_key_id = authorization_key_id
        self.attestation_key_id = attestation_key_id
        self.expected_receipt_public_key_sha256 = expected_receipt_public_key_sha256
        self.receipt_signer = receipt_signer
        self.verify_signature = verify_signature
        self.verify_grant_claims = verify_grant_claims
        self.canonical_claims = canonical_claims
        self.digest_manifest = digest_manifest
        self.entry_claims = entry_claims
        self.expected_games = expected_games
        self.memory_limit_bytes = memory_limit_bytes
        self.runtime_limit_seconds = runtime_limit_seconds

    def issue(self, snapshot: EvidenceSnapshot) -> dict[str, Any]:
        signer = self.receipt_signer
        if signer.purpose != RECEIPT_PURPOSE or not signer.key_id:
            raise TrustValidationError("receipt signer identity or purpose is invalid")
        if signer.public_key_sha256 != self.expected_receipt_public_key_sha256:
            raise TrustValidationError("receipt signing key differs from independent pin")
        if signer.key_id in {self.authorization_key_id, self.attestation_key_id}:
            raise TrustValidationError("signing identities must be separate by purpose")
        if signer.public_key_sha256 in {
            _sha(_canonical(self.authorization_public_key)),
            _sha(_canonical(self.attestation_public_key)),
        }:
            raise TrustValidationError("receipt signing key is not independent")

        manifest = _document(snapshot.manifest_raw, "approved manifest")
        status = _document(snapshot.status_raw, "batch status")
        manifest_sha = self.digest_manifest(manifest)
        if manifest_sha != self.approved_manifest_sha256:
            raise TrustValidationError("manifest differs from independently approved digest")
        batch_id = manifest.get("batch_id")
        rows = manifest.get("games")
        if (
            not isinstance(batch_id, str)
            or not isinstance(rows, list)
            or len(rows) != self.expected_games
        ):
            raise TrustValidationError("approved schedule is incomplete")
        runtime = manifest.get("runtime")
        if (
            manifest.get("source_commit") != self.expected_source_commit
            or manifest.get("supervisor_sha256") != self.expected_supervisor_sha256
            or not isinstance(runtime, dict)
            or runtime.get("python_executable_sha256") != self.expected_runtime_sha256
            or type(manifest.get("job_memory_limit_bytes")) is not int
            or manifest.get("job_memory_limit_bytes") != self.memory_limit_bytes
            or type(manifest.get("process_memory_limit_bytes")) is not int
            or manifest.get("process_memory_limit_bytes") != self.memory_limit_bytes
            or type(manifest.get("runtime_seconds_limit")) is not int
            or manifest.get("runtime_seconds_limit") != self.runtime_limit_seconds
            or type(manifest.get("maximum_games")) is not int
            or manifest.get("maximum_games") != self.expected_games
            or type(manifest.get("automatic_retries")) is not int
            or manifest.get("automatic_retries") != 0
        ):
            raise TrustValidationError("manifest source, runtime, or resource contract mismatch")
        if (
            status.get("state") != "COMPLETE"
            or type(status.get("completed_games")) is not int
            or status["completed_games"] != self.expected_games
            or type(status.get("automatic_retries")) is not int
            or status["automatic_retries"] != 0
            or status.get("manifest_sha256") != manifest_sha
        ):
            raise TrustValidationError("batch status is incomplete or mismatched")
        records = status.get("games")
        if not isinstance(records, list) or len(records) != self.expected_games:
            raise TrustValidationError("batch status does not contain every scheduled game")
        if set(snapshot.artifacts) != {row.get("run_id") for row in rows}:
            raise TrustValidationError("snapshot game directories differ from approved schedule")
        if set(snapshot.attestations_raw) != {row.get("run_id") for row in rows}:
            raise TrustValidationError("supervisor attestations are missing or extra")
        if set(snapshot.grants_raw) != {row.get("run_id") for row in rows}:
            raise TrustValidationError("authorization grants are missing or extra")

        seen_nonces: set[str] = set()
        output_root = Path(manifest["output_root"]).resolve(strict=False)
        authorization_root = Path(manifest["authorization_root"]).resolve(strict=False)
        for index, (row, record) in enumerate(zip(rows, records, strict=True), start=1):
            if not isinstance(row, dict) or not isinstance(record, dict):
                raise TrustValidationError(f"game {index} record is malformed")
            run_id = row.get("run_id")
            if (
                not isinstance(run_id, str)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", run_id)
                or record.get("run_id") != run_id
            ):
                raise TrustValidationError(f"game {index} identity differs from schedule")
            expected_output = (output_root / run_id).resolve(strict=False)
            expected_authorization = (authorization_root / batch_id / f"{run_id}.json").resolve(
                strict=False
            )
            if (
                Path(row.get("output_destination", "")).resolve(strict=False) != expected_output
                or Path(row.get("authorization_file", "")).resolve(strict=False)
                != expected_authorization
            ):
                raise TrustValidationError(
                    f"game {index} output or grant path differs from contract"
                )
            if (
                type(record.get("index")) is not int
                or record.get("index") != index
                or record.get("state") != "RETURNED"
                or type(record.get("exit_code")) is not int
                or record.get("exit_code") != 0
            ):
                raise TrustValidationError(f"game {index} did not complete successfully")
            attestation = _document(snapshot.attestations_raw[run_id], f"game {index} attestation")
            if (
                attestation.get("schema") != ATTESTATION_SCHEMA
                or attestation.get("key_id") != self.attestation_key_id
                or attestation.get("key_purpose") != ATTESTATION_PURPOSE
            ):
                raise TrustValidationError(f"game {index} attestation schema is invalid")
            self.verify_signature(attestation, self.attestation_public_key)
            grant = _document(snapshot.grants_raw[run_id], f"game {index} grant")
            expected = self.entry_claims(manifest, manifest_sha, index)
            nonce = self.verify_grant_claims(grant, expected)
            if nonce in seen_nonces:
                raise TrustValidationError("duplicate one-use authorization nonce")
            seen_nonces.add(nonce)
            ledger_raw = snapshot.consumption_raw.get(nonce)
            expected_grant_digest = _sha(self.canonical_claims(grant))
            if ledger_raw != (expected_grant_digest + "\n").encode("ascii"):
                raise TrustValidationError(
                    f"game {index} grant consumption is absent or inconsistent"
                )

            if (
                attestation.get("batch_id") != batch_id
                or attestation.get("manifest_sha256") != manifest_sha
                or attestation.get("index") != index
                or attestation.get("run_id") != run_id
                or attestation.get("grant_sha256") != expected_grant_digest
                or attestation.get("nonce") != nonce
                or attestation.get("source_commit") != self.expected_source_commit
                or attestation.get("supervisor_sha256") != self.expected_supervisor_sha256
                or attestation.get("runtime_sha256") != self.expected_runtime_sha256
                or attestation.get("exit_code") != 0
                or attestation.get("memory_limit_bytes") != self.memory_limit_bytes
                or attestation.get("runtime_limit_seconds") != self.runtime_limit_seconds
            ):
                raise TrustValidationError(f"game {index} supervisor attestation claims mismatch")
            if record.get("artifacts_sha256") != attestation.get("artifacts_sha256"):
                raise TrustValidationError(
                    f"game {index} status inventory differs from attestation"
                )
            resource = record.get("resource_gate")
            if not isinstance(resource, dict):
                raise TrustValidationError(f"game {index} resource evidence is missing")
            for field in (
                "available_physical_bytes",
                "system_commit_headroom_bytes",
                "minimum_each_bytes",
            ):
                if type(resource.get(field)) is not int:
                    raise TrustValidationError(f"game {index} resource evidence is malformed")
            if (
                resource["available_physical_bytes"] < resource["minimum_each_bytes"]
                or resource["system_commit_headroom_bytes"] < resource["minimum_each_bytes"]
            ):
                raise TrustValidationError(f"game {index} resource preflight failed")
            storage = record.get("storage_gate")
            if (
                not isinstance(storage, dict)
                or storage.get("file_system") != "NTFS"
                or storage.get("volume_label") != "TMT"
                or type(storage.get("available_bytes")) is not int
                or type(storage.get("required_free_bytes")) is not int
                or storage["available_bytes"] < storage["required_free_bytes"]
            ):
                raise TrustValidationError(f"game {index} storage preflight failed")
            files = snapshot.artifacts[run_id]
            actual_names = set(files)
            if not REQUIRED_ARTIFACTS.issubset(actual_names):
                raise TrustValidationError(f"game {index} is missing required artifacts")
            inventory = attestation.get("artifacts_sha256")
            if not isinstance(inventory, dict) or set(inventory) != actual_names:
                raise TrustValidationError(
                    f"game {index} artifact inventory is incomplete or extra"
                )
            folded_names = [name.casefold() for name in inventory]
            if len(folded_names) != len(set(folded_names)):
                raise TrustValidationError(f"game {index} inventory has a Windows path collision")
            for name, content in files.items():
                _safe_path(name)
                if not isinstance(content, bytes) or inventory.get(name) != _sha(content):
                    raise TrustValidationError(
                        f"game {index} artifact differs from attested snapshot"
                    )
            self._validate_game_documents(manifest, row, manifest_sha, files, index)

        receipt = {
            "schema": RECEIPT_SCHEMA,
            "batch_id": batch_id,
            "manifest_sha256": manifest_sha,
            "status_sha256": _sha(snapshot.status_raw),
            "completed_games": self.expected_games,
        }
        # Signing is deliberately the final operation after all trust checks.
        receipt["signature_b64"] = signer.sign(self.canonical_claims(receipt))
        return receipt

    def issue_and_publish(self, snapshot: EvidenceSnapshot, publisher: Any) -> dict[str, Any]:
        """Reserve the unique destination before validation/signing, then publish once."""
        try:
            publisher.reserve_no_replace()
        except Exception as exc:
            raise TrustValidationError(
                "receipt destination is occupied or cannot be reserved"
            ) from exc
        receipt = self.issue(snapshot)
        publish_no_replace(publisher, receipt)
        return receipt

    def _validate_game_documents(
        self,
        manifest: dict[str, Any],
        row: dict[str, Any],
        manifest_sha: str,
        files: Mapping[str, bytes],
        index: int,
    ) -> None:
        run = _document(files["run_manifest.json"], f"game {index} run manifest")
        result = _document(files["result.json"], f"game {index} result")
        run_id = row["run_id"]
        expected_decks = {seat["deck_key"]: seat["sha256"] for seat in row["seats"]}
        expected = {
            "run_id": run_id,
            "batch_manifest_sha256": manifest_sha,
            "source_commit": self.expected_source_commit,
            "process_memory_limit_bytes": self.memory_limit_bytes,
            "runtime_seconds_limit": self.runtime_limit_seconds,
            "seed": row["seed"],
            "orientation": row["orientation"],
            "deck_sha256": expected_decks,
        }
        if any(run.get(key) != value for key, value in expected.items()):
            raise TrustValidationError(f"game {index} run manifest differs from approved contract")
        if (
            result.get("label") != "DIAGNOSTIC"
            or result.get("run_id") != run_id
            or result.get("source_commit") != self.expected_source_commit
            or result.get("source_blobs") != manifest.get("source_blobs")
            or result.get("pairing_id") != row.get("pairing_id")
            or type(result.get("seed")) is not int
            or result.get("seed") != row.get("seed")
            or result.get("orientation") != row.get("orientation")
            or result.get("seats") != [seat["deck_key"] for seat in row["seats"]]
            or result.get("deck_sha256") != expected_decks
            or result.get("completion_state") != "COMPLETE"
            or not isinstance(result.get("snapshot"), dict)
            or result["snapshot"].get("winner") not in expected_decks
            or type(result["snapshot"].get("turn")) is not int
            or not isinstance(result["snapshot"].get("events"), list)
            or not isinstance(result["snapshot"].get("stage002_presence"), list)
        ):
            raise TrustValidationError(f"game {index} result differs from approved contract")
        per_game_status = _document(files["status.json"], f"game {index} status")
        if (
            per_game_status.get("label") != "DIAGNOSTIC"
            or per_game_status.get("state") != "RETURNED"
            or per_game_status.get("child_exit_code") != 0
        ):
            raise TrustValidationError(f"game {index} per-game status is incomplete")


def publish_no_replace(publisher: Any, receipt: dict[str, Any]) -> None:
    """Delegate publication to an injected atomic no-replace storage adapter."""
    payload = _canonical(receipt)
    publisher.publish_no_replace(payload)


def create_execution_attestation(observed: Mapping[str, Any], signer: Signer) -> dict[str, Any]:
    """Create a synthetic attestation from supervisor-observed terminal facts.

    A production caller must obtain ``observed`` directly from its terminated
    Job Object/process handles and locked output snapshot. This function does
    not establish those OS facts and deliberately does not load a private key.
    """
    if signer.purpose != ATTESTATION_PURPOSE or not signer.key_id:
        raise TrustValidationError("execution attestor identity or purpose is invalid")
    required = {
        "batch_id",
        "manifest_sha256",
        "index",
        "run_id",
        "grant_sha256",
        "nonce",
        "source_commit",
        "supervisor_sha256",
        "runtime_sha256",
        "exit_code",
        "memory_limit_bytes",
        "runtime_limit_seconds",
        "artifacts_sha256",
    }
    if set(observed) != required:
        raise TrustValidationError(
            "supervisor observation does not match strict attestation schema"
        )
    if (
        type(observed.get("index")) is not int
        or observed.get("index", 0) < 1
        or type(observed.get("exit_code")) is not int
        or observed.get("exit_code") != 0
        or type(observed.get("memory_limit_bytes")) is not int
        or type(observed.get("runtime_limit_seconds")) is not int
        or not isinstance(observed.get("artifacts_sha256"), dict)
        or not observed["artifacts_sha256"]
        or any(
            not isinstance(value, str) or not _SHA256.fullmatch(value)
            for value in observed["artifacts_sha256"].values()
        )
    ):
        raise TrustValidationError("supervisor observation is incomplete or not a successful game")
    document = {
        "schema": ATTESTATION_SCHEMA,
        "key_id": signer.key_id,
        "key_purpose": signer.purpose,
        **dict(observed),
    }
    document["signature_b64"] = signer.sign(_canonical(document))
    return document


def verify_completion_receipt(
    receipt: dict[str, Any],
    *,
    batch_id: str,
    manifest_sha256: str,
    status_raw: bytes,
    completed_games: int,
    receipt_public_key: Mapping[str, Any],
    expected_receipt_key_sha256: str,
    verify_signature: Callable[[dict[str, Any], Mapping[str, Any]], None],
) -> None:
    """Independently check receipt key pin, exact schema, bindings, and signature."""
    actual_key_sha = _sha(_canonical(dict(receipt_public_key)))
    if actual_key_sha != expected_receipt_key_sha256:
        raise TrustValidationError("receipt public-key identity mismatch")
    if set(receipt) != {
        "schema",
        "batch_id",
        "manifest_sha256",
        "status_sha256",
        "completed_games",
        "signature_b64",
    }:
        raise TrustValidationError("receipt fields do not match the reviewed schema")
    if (
        receipt.get("schema") != RECEIPT_SCHEMA
        or receipt.get("batch_id") != batch_id
        or receipt.get("manifest_sha256") != manifest_sha256
        or receipt.get("status_sha256") != _sha(status_raw)
        or type(receipt.get("completed_games")) is not int
        or receipt.get("completed_games") != completed_games
    ):
        raise TrustValidationError("receipt does not bind the approved completed batch")
    verify_signature(receipt, receipt_public_key)

