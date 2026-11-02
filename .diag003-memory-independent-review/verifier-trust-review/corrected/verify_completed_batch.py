"""Verify a completed ten-game batch against a signed completion receipt."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
from pathlib import Path, PureWindowsPath
from typing import Any

TOOLS = Path(r"C:\projects\tmt\.diag003-memory-independent-review\correction\tools")
OUTPUT_ROOT = Path(r"G:\cardcade\diagnostics")
PUBLIC_KEY_PATH = Path(
    r"C:\Users\cowabunga\AppData\Roaming\Cardcade\Stage002Diagnostic\hq-public-key.json"
)
USED_LEDGER = Path(
    r"C:\Users\cowabunga\AppData\Roaming\Cardcade\Stage002Diagnostic\used-authorizations"
)

EXPECTED_COMMIT = "32a80228714674327aca62f8b86b70c4c4afc929"
EXPECTED_MEMORY = 2_997_489_664
EXPECTED_RUNTIME = 600
EXPECTED_PUBLIC_KEY_SHA256 = "7cfe29b81f719601fd7c0a75925d6cdf4347d18e010df610745dc4d8642f3427"
EXPECTED_PUBLIC_KEY_BITS = 3072
EXPECTED_DEPENDENCY_SHA256 = {
    "stage002_authorization.py": "1fd4db87131a0fef996fc2df7aee5f6634fdbc2d7b90f226c76217596fdb6540",
    "stage002_batch.py": "30720c8d720b52a9538b79063d785e57dc37762bf5099215b7ee05cef0a80293",
}
REQUIRED_COMPLETED_ARTIFACTS = frozenset(
    {"status.json", "run_manifest.json", "result.json", "stdout.log", "stderr.log"}
)
RECEIPT_SCHEMA = "cardcade-stage002-batch-completion-v1"
_BATCH_ID = re.compile(r"cardcade-smoke10-[A-Za-z0-9_-]{1,48}\Z")
_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")
_SHA256 = re.compile(r"[a-f0-9]{64}\Z")
_REPARSE_POINT = 0x400


class VerificationError(ValueError):
    """Raised when the evidence or any identity fails verification."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_reparse(path: Path) -> bool:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode):
        return True
    if getattr(info, "st_file_attributes", 0) & _REPARSE_POINT:
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def _assert_no_reparse_chain(path: Path) -> None:
    absolute = Path(path.absolute())
    cursor = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        cursor = cursor / part
        try:
            if _is_reparse(cursor):
                raise VerificationError(f"reparse point is not allowed in evidence path: {cursor}")
        except FileNotFoundError as exc:
            raise VerificationError(f"required evidence path is missing: {cursor}") from exc


def _regular_file(path: Path) -> None:
    _assert_no_reparse_chain(path)
    if not path.is_file():
        raise VerificationError(f"required regular file is missing: {path}")


def load_pinned_dependencies(
    root: Path = TOOLS,
    *,
    expected_hashes: dict[str, str] = EXPECTED_DEPENDENCY_SHA256,
) -> tuple[Any, Any]:
    """Hash both dependencies before executing/importing either file."""
    modules: dict[str, Any] = {}
    for filename, expected in expected_hashes.items():
        path = root / filename
        _regular_file(path)
        actual = _sha256_file(path)
        if actual != expected:
            raise VerificationError(f"dependency identity mismatch for {filename}: {actual}")

    for filename, module_name in (
        ("stage002_authorization.py", "cardcade_pinned_stage002_authorization"),
        ("stage002_batch.py", "cardcade_pinned_stage002_batch"),
    ):
        path = root / filename
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise VerificationError(f"cannot load pinned dependency: {filename}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        modules[filename] = module
    return modules["stage002_authorization.py"], modules["stage002_batch.py"]


def load_pinned_public_key(
    path: Path = PUBLIC_KEY_PATH,
    *,
    expected_sha256: str = EXPECTED_PUBLIC_KEY_SHA256,
    expected_bits: int = EXPECTED_PUBLIC_KEY_BITS,
) -> dict[str, Any]:
    _regular_file(path)
    raw = path.read_bytes()
    actual = _sha256_bytes(raw)
    if actual != expected_sha256:
        raise VerificationError(f"public-key identity mismatch: {actual}")
    try:
        document = json.loads(raw)
        modulus = int(document["modulus_hex"], 16)
        exponent = document["public_exponent"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise VerificationError("pinned public key is malformed") from exc
    if modulus.bit_length() != expected_bits or type(exponent) is not int or exponent != 65537:
        raise VerificationError("pinned public-key parameters are outside the approved profile")
    return document


def _safe_relative_parts(relative: str) -> tuple[str, ...]:
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise VerificationError("artifact relative path is malformed")
    win = PureWindowsPath(relative)
    if win.is_absolute() or win.drive or relative.startswith(("/", "\\")):
        raise VerificationError(f"absolute artifact path is prohibited: {relative}")
    normalized = relative.replace("/", "\\")
    parts = tuple(normalized.split("\\"))
    if any(part in {"", ".", ".."} or ":" in part for part in parts):
        raise VerificationError(f"artifact traversal or drive syntax is prohibited: {relative}")
    return parts


def _contained_regular_file(root: Path, relative: str) -> Path:
    _assert_no_reparse_chain(root)
    root = root.resolve(strict=True)
    candidate = root.joinpath(*_safe_relative_parts(relative))
    _regular_file(candidate)
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise VerificationError(
            f"artifact resolves outside its assigned output: {relative}"
        ) from exc
    if not resolved.is_file():
        raise VerificationError(f"artifact is not a regular file: {relative}")
    return resolved


def _regular_files_below(root: Path) -> set[str]:
    _assert_no_reparse_chain(root)
    root = root.resolve(strict=True)
    _assert_no_reparse_chain(root)
    found: set[str] = set()
    for path in root.rglob("*"):
        _assert_no_reparse_chain(path)
        if path.is_file():
            found.add("\\".join(path.relative_to(root).parts))
    return found


def _validated_inventory(record: dict[str, Any], output: Path) -> dict[str, str]:
    inventory = record.get("artifacts_sha256")
    if not isinstance(inventory, dict) or not inventory:
        raise VerificationError("completed game has no artifact inventory")
    normalized: dict[str, str] = {}
    for relative, digest in inventory.items():
        parts = _safe_relative_parts(relative)
        key = "\\".join(parts)
        case_key = key.casefold()
        if case_key in normalized:
            raise VerificationError("artifact inventory contains a Windows case-fold collision")
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise VerificationError(f"artifact digest is malformed: {relative}")
        _contained_regular_file(output, relative)
        normalized[case_key] = digest
    required = {name.casefold() for name in REQUIRED_COMPLETED_ARTIFACTS}
    if not required.issubset(normalized):
        missing = sorted(REQUIRED_COMPLETED_ARTIFACTS - {key for key in normalized})
        raise VerificationError(f"required completed-game artifacts are missing: {missing}")
    actual = {name.casefold() for name in _regular_files_below(output)}
    if actual != set(normalized):
        raise VerificationError(
            "artifact inventory does not exactly cover the assigned game output"
        )
    for relative in inventory:
        path = _contained_regular_file(output, relative)
        if _sha256_file(path) != inventory[relative]:
            raise VerificationError(f"artifact hash mismatch: {relative}")
    return inventory


def _read_json_regular(path: Path) -> tuple[dict[str, Any], bytes]:
    _regular_file(path)
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"evidence JSON is malformed: {path.name}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"evidence JSON must be an object: {path.name}")
    return value, raw


def _verify_completion_receipt(
    receipt_path: Path,
    *,
    batch_id: str,
    manifest_sha: str,
    status_raw: bytes,
    public_key: dict[str, Any],
    authorization_module: Any,
) -> None:
    receipt, _raw = _read_json_regular(receipt_path)
    if set(receipt) != {
        "schema",
        "batch_id",
        "manifest_sha256",
        "status_sha256",
        "completed_games",
        "signature_b64",
    }:
        raise VerificationError("completion receipt fields do not match the strict schema")
    if (
        receipt.get("schema") != RECEIPT_SCHEMA
        or receipt.get("batch_id") != batch_id
        or receipt.get("manifest_sha256") != manifest_sha
        or receipt.get("status_sha256") != _sha256_bytes(status_raw)
        or type(receipt.get("completed_games")) is not int
        or receipt.get("completed_games") != 10
    ):
        raise VerificationError("completion receipt does not bind the exact completed batch")
    authorization_module.verify_rsa_sha256(receipt, public_key)


def _validate_batch_roots(manifest: dict[str, Any], output_root: Path) -> None:
    if not isinstance(manifest.get("batch_id"), str) or not _BATCH_ID.fullmatch(
        manifest["batch_id"]
    ):
        raise VerificationError("batch identifier is malformed")
    try:
        manifest_root = os.path.normcase(os.path.abspath(manifest["output_root"]))
        expected_root = os.path.normcase(os.path.abspath(output_root))
        if manifest_root != expected_root:
            raise VerificationError("manifest output root differs from the verifier output root")
    except (KeyError, OSError, TypeError) as exc:
        raise VerificationError("manifest output root is missing or invalid") from exc
    if len(manifest.get("games", [])) != 10:
        raise VerificationError("manifest must contain exactly ten games")


def verify(
    manifest_path: Path,
    *,
    output_root: Path = OUTPUT_ROOT,
    public_key_path: Path = PUBLIC_KEY_PATH,
    used_ledger: Path = USED_LEDGER,
    dependency_root: Path = TOOLS,
    expected_dependency_hashes: dict[str, str] = EXPECTED_DEPENDENCY_SHA256,
    expected_public_key_sha256: str = EXPECTED_PUBLIC_KEY_SHA256,
    expected_public_key_bits: int = EXPECTED_PUBLIC_KEY_BITS,
) -> dict[str, Any]:
    authorization_module, batch_module = load_pinned_dependencies(
        dependency_root, expected_hashes=expected_dependency_hashes
    )
    manifest, _manifest_raw = _read_json_regular(manifest_path)
    manifest_sha = batch_module.digest(manifest)
    _assert_no_reparse_chain(output_root)
    output_root = output_root.resolve(strict=True)
    _validate_batch_roots(manifest, output_root)
    public_key = load_pinned_public_key(
        public_key_path,
        expected_sha256=expected_public_key_sha256,
        expected_bits=expected_public_key_bits,
    )

    batch_id = manifest["batch_id"]
    status_path = _contained_regular_file(output_root, f"{batch_id}.status.json")
    receipt_path = _contained_regular_file(output_root, f"{batch_id}.completion-receipt.json")
    status, status_raw = _read_json_regular(status_path)
    _verify_completion_receipt(
        receipt_path,
        batch_id=batch_id,
        manifest_sha=manifest_sha,
        status_raw=status_raw,
        public_key=public_key,
        authorization_module=authorization_module,
    )
    status_games = status.get("games")
    if (
        status.get("state") != "COMPLETE"
        or type(status.get("completed_games")) is not int
        or status.get("completed_games") != 10
        or type(status.get("automatic_retries")) is not int
        or status.get("automatic_retries") != 0
        or status.get("manifest_sha256") != manifest_sha
        or not isinstance(status_games, list)
        or len(status_games) != 10
    ):
        raise VerificationError("batch checkpoint is incomplete or inconsistent")

    nonces: set[str] = set()
    outcomes: list[dict[str, Any]] = []
    artifacts_checked = 0
    for index, (row, record) in enumerate(zip(manifest["games"], status_games, strict=True), 1):
        if not isinstance(row, dict) or not isinstance(record, dict):
            raise VerificationError(f"game {index} evidence row is malformed")
        run_id = row.get("run_id")
        if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id):
            raise VerificationError(f"manifest game {index} run id is malformed")
        expected_output = output_root / run_id
        actual_output = os.path.normcase(os.path.abspath(row.get("output_destination", "")))
        approved_output = os.path.normcase(os.path.abspath(expected_output))
        if actual_output != approved_output:
            raise VerificationError(f"manifest game {index} output identity is inconsistent")
        if (
            type(record.get("index")) is not int
            or record.get("index") != index
            or record.get("run_id") != run_id
            or record.get("state") != "RETURNED"
            or type(record.get("exit_code")) is not int
            or record.get("exit_code") != 0
        ):
            raise VerificationError(f"game {index} did not return successfully")
        inventory = _validated_inventory(record, expected_output)
        artifacts_checked += len(inventory)

        resource = record.get("resource_gate", {})
        for field in (
            "available_physical_bytes",
            "system_commit_headroom_bytes",
            "minimum_each_bytes",
        ):
            if type(resource.get(field)) is not int:
                raise VerificationError(f"game {index} resource evidence is incomplete")
        if (
            resource["available_physical_bytes"] < resource["minimum_each_bytes"]
            or resource["system_commit_headroom_bytes"] < resource["minimum_each_bytes"]
        ):
            raise VerificationError(f"game {index} resource gate failed")
        storage = record.get("storage_gate", {})
        if (
            storage.get("file_system") != "NTFS"
            or storage.get("volume_label") != "TMT"
            or type(storage.get("available_bytes")) is not int
            or type(storage.get("required_free_bytes")) is not int
            or storage["available_bytes"] < storage["required_free_bytes"]
        ):
            raise VerificationError(f"game {index} storage gate failed")

        output = _contained_regular_file(output_root, run_id + "\\result.json").parent
        run, _ = _read_json_regular(output / "run_manifest.json")
        result, _ = _read_json_regular(output / "result.json")
        expected_decks = {seat["deck_key"]: seat["sha256"] for seat in row["seats"]}
        if (
            run.get("run_id") != run_id
            or run.get("batch_manifest_sha256") != manifest_sha
            or run.get("source_commit") != EXPECTED_COMMIT
            or run.get("process_memory_limit_bytes") != EXPECTED_MEMORY
            or run.get("runtime_seconds_limit") != EXPECTED_RUNTIME
            or run.get("seed") != row["seed"]
            or run.get("orientation") != row["orientation"]
            or run.get("deck_sha256") != expected_decks
            or result.get("label") != "DIAGNOSTIC"
            or result.get("run_id") != run_id
            or result.get("source_commit") != EXPECTED_COMMIT
            or result.get("source_blobs") != manifest.get("source_blobs")
            or result.get("pairing_id") != row["pairing_id"]
            or type(result.get("seed")) is not int
            or result.get("seed") != row["seed"]
            or result.get("orientation") != row["orientation"]
            or result.get("seats") != [seat["deck_key"] for seat in row["seats"]]
            or result.get("deck_sha256") != expected_decks
            or result.get("completion_state") != "COMPLETE"
            or not isinstance(result.get("snapshot"), dict)
            or type(result["snapshot"].get("turn")) is not int
            or not isinstance(result["snapshot"].get("events"), list)
            or not isinstance(result["snapshot"].get("stage002_presence"), list)
            or result["snapshot"].get("winner") not in set(expected_decks)
        ):
            raise VerificationError(f"game {index} result identity or completion is invalid")

        auth_root = Path(manifest["authorization_root"])
        _assert_no_reparse_chain(auth_root)
        auth_root = auth_root.resolve(strict=True)
        expected_auth = auth_root / batch_id / f"{run_id}.json"
        auth_path = Path(row.get("authorization_file", ""))
        _regular_file(auth_path)
        if auth_path.resolve(strict=True) != expected_auth.resolve(strict=True):
            raise VerificationError(f"game {index} authorization path differs from the contract")
        grant, _ = _read_json_regular(auth_path)
        nonce = authorization_module.verify_claims(
            grant, public_key, batch_module.entry_claims(manifest, manifest_sha, index)
        )
        if nonce in nonces:
            raise VerificationError("batch reused a one-use authorization nonce")
        nonces.add(nonce)
        used = _contained_regular_file(used_ledger, f"{nonce}.used")
        expected_claim_digest = hashlib.sha256(
            authorization_module.canonical_claims(grant)
        ).hexdigest()
        if used.read_text(encoding="ascii").strip() != expected_claim_digest:
            raise VerificationError(
                f"game {index} authorization consumption record is missing or wrong"
            )
        outcomes.append(
            {
                "seed": row["seed"],
                "seats": [seat["deck_key"] for seat in row["seats"]],
                "winner": result["snapshot"]["winner"],
                "turn": result["snapshot"].get("turn"),
                "run_id": run_id,
            }
        )
    return {
        "state": "VERIFIED_COMPLETE",
        "batch_id": batch_id,
        "manifest_sha256": manifest_sha,
        "games_verified": len(outcomes),
        "artifact_hashes_rechecked": artifacts_checked,
        "completion_receipt_sha256": _sha256_file(receipt_path),
        "outcomes": outcomes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.manifest.resolve(strict=True)), sort_keys=True))
    except Exception as exc:
        print(f"VERIFICATION_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
