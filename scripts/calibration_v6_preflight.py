"""Structural preflight for the accepted Calibration V6 release packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REQUIRED = {
    "scheme",
    "execution_authorized",
    "main_commit",
    "accepted_runtime",
    "protocol_identity",
    "seed_table_v2",
}


def load_v6_seed_identity(path: Path) -> dict[str, Any]:
    """Validate V6 structure and return the authoritative seed identities."""
    packet = json.loads(path.read_bytes())
    if not isinstance(packet, dict) or not packet.keys() >= _REQUIRED:
        raise ValueError("V6 release packet missing required fields")
    if packet["scheme"] != "calibration-release-baseline-refresh-v6":
        raise ValueError("unexpected V6 release packet scheme")
    if packet["execution_authorized"] is not False:
        raise ValueError("V6 packet must remain unauthorized during preflight")
    seed = packet["seed_table_v2"]
    if not isinstance(seed, dict):
        raise ValueError("seed_table_v2 must be an object")
    for field in (
        "path",
        "accepted_sha256",
        "accepted_entropy_sha256",
        "rows",
        "orientation_pairs",
    ):
        if field not in seed:
            raise ValueError(f"seed_table_v2 missing {field}")
    if not isinstance(seed["accepted_sha256"], str) or len(seed["accepted_sha256"]) != 64:
        raise ValueError("seed_table_v2.accepted_sha256 must be a SHA-256 hex string")
    if (
        not isinstance(seed["accepted_entropy_sha256"], str)
        or len(seed["accepted_entropy_sha256"]) != 64
    ):
        raise ValueError("seed_table_v2.accepted_entropy_sha256 must be a SHA-256 hex string")
    if seed["rows"] != 184320 or seed["orientation_pairs"] != 92160:
        raise ValueError("V2 workload dimensions are inconsistent")
    return {
        "seed_table_sha256": seed["accepted_sha256"],
        "entropy_sha256": seed["accepted_entropy_sha256"],
        "seed_table_path": seed["path"],
    }
