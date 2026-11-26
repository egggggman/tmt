"""Verification and one-use consumption for HQ-signed diagnostic claims.

This module intentionally contains no token-issuance or private-key code.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_SHA256_DER_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")
_NONCE = re.compile(r"[a-f0-9]{32}")


def canonical_claims(document: dict[str, Any]) -> bytes:
    unsigned = {key: value for key, value in document.items() if key != "signature_b64"}
    return json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def verify_rsa_sha256(document: dict[str, Any], public_key: dict[str, Any]) -> None:
    """Verify RSA PKCS#1 v1.5 SHA-256 using only the pinned public modulus/exponent."""
    try:
        modulus = int(public_key["modulus_hex"], 16)
        exponent = int(public_key["public_exponent"])
        signature = base64.b64decode(document["signature_b64"], validate=True)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("authorization signature or public key is malformed") from exc
    size = (modulus.bit_length() + 7) // 8
    if size < 62 or len(signature) != size:
        raise ValueError("authorization signature has an invalid size")
    signature_value = int.from_bytes(signature, "big")
    if signature_value >= modulus:
        raise ValueError("authorization signature is outside the RSA modulus")
    encoded = pow(signature_value, exponent, modulus).to_bytes(size, "big")
    digest_info = _SHA256_DER_PREFIX + hashlib.sha256(canonical_claims(document)).digest()
    padding_size = size - len(digest_info) - 3
    expected = b"\x00\x01" + b"\xff" * padding_size + b"\x00" + digest_info
    if padding_size < 8 or not hmac.compare_digest(encoded, expected):
        raise ValueError("authorization signature verification failed")


def verify_claims(
    document: dict[str, Any],
    public_key: dict[str, Any],
    expected: dict[str, Any],
    *,
    now: datetime | None = None,
) -> str:
    verify_rsa_sha256(document, public_key)
    if document.get("schema") != "cardcade-stage002-one-game-v1":
        raise ValueError("unsupported authorization schema")
    for name, required in expected.items():
        actual = document.get(name)
        if isinstance(required, bool):
            matches = actual is required
        elif isinstance(required, int):
            matches = type(actual) is int and actual == required
        else:
            matches = actual == required
        if not matches:
            raise ValueError(f"authorization binding mismatch: {name}")
    nonce = document.get("nonce")
    if not isinstance(nonce, str) or not _NONCE.fullmatch(nonce):
        raise ValueError("authorization nonce is malformed")
    try:
        issued = datetime.fromisoformat(document["issued_utc"].replace("Z", "+00:00"))
        expires = datetime.fromisoformat(document["expires_utc"].replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("authorization timestamps are malformed") from exc
    if issued.tzinfo is None or expires.tzinfo is None:
        raise ValueError("authorization timestamps must include a timezone")
    current = now or datetime.now(UTC)
    if current.tzinfo is None or issued > current or expires <= current or expires <= issued:
        raise ValueError("authorization is not currently valid")
    return nonce


def consume_nonce(nonce: str, ledger_directory: Path, claim_digest: str) -> Path:
    """Atomically burn a validated nonce. O_EXCL makes concurrent reuse fail closed."""
    if not _NONCE.fullmatch(nonce):
        raise ValueError("authorization nonce is malformed")
    ledger_directory.mkdir(parents=True, exist_ok=True)
    record = ledger_directory / f"{nonce}.used"
    try:
        descriptor = os.open(record, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError("authorization has already been consumed") from exc
    with os.fdopen(descriptor, "wb") as stream:
        stream.write((claim_digest + "\n").encode("ascii"))
        stream.flush()
        os.fsync(stream.fileno())
    return record


def consume_authorization(
    document: dict[str, Any],
    public_key: dict[str, Any],
    expected: dict[str, Any],
    ledger_directory: Path,
    *,
    now: datetime | None = None,
) -> Path:
    nonce = verify_claims(document, public_key, expected, now=now)
    digest = hashlib.sha256(canonical_claims(document)).hexdigest()
    return consume_nonce(nonce, ledger_directory, digest)
