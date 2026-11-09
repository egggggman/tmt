"""Synthetic Ed25519 trust anchor and signer; never used by the launcher CLI."""

from __future__ import annotations

import base64
import json
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

TEST_KEY_ID = "cardcade-synthetic-test-only"
OTHER_TEST_KEY_ID = "cardcade-synthetic-second-test-only"
_TEST_PRIVATE_KEY = Ed25519PrivateKey.generate()
_OTHER_TEST_PRIVATE_KEY = Ed25519PrivateKey.generate()
TEST_PUBLIC_KEY = _TEST_PRIVATE_KEY.public_key().public_bytes(
    serialization.Encoding.Raw,
    serialization.PublicFormat.Raw,
)
OTHER_TEST_PUBLIC_KEY = _OTHER_TEST_PRIVATE_KEY.public_key().public_bytes(
    serialization.Encoding.Raw,
    serialization.PublicFormat.Raw,
)


def install_test_trust_anchor(launcher_module: Any) -> None:
    launcher_module.TRUSTED_HQ_AUTHORIZATION_KEYS[TEST_KEY_ID] = TEST_PUBLIC_KEY
    launcher_module.TRUSTED_HQ_AUTHORIZATION_KEYS[OTHER_TEST_KEY_ID] = OTHER_TEST_PUBLIC_KEY


def signed_document(document: dict[str, Any], *, key_id: str = TEST_KEY_ID) -> dict[str, Any]:
    private_key = {
        TEST_KEY_ID: _TEST_PRIVATE_KEY,
        OTHER_TEST_KEY_ID: _OTHER_TEST_PRIVATE_KEY,
    }[key_id]
    signed = {**document, "signing_key_id": key_id}
    payload = json.dumps(
        signed,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    signed["signature"] = base64.b64encode(private_key.sign(payload)).decode("ascii")
    return signed
