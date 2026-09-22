"""Authenticate the explicitly promoted Calibration V1 release authority."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

AUTHORITY_REL = "docs/cardcade/CALIBRATION_RELEASE_AUTHORITY_V1.json"
V16_REL = "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V16.json"
CAPACITY_REL = "docs/cardcade/CALIBRATION_RELEASE_MANIFEST_CAPACITY_V1.json"
HEX64 = re.compile(r"^[0-9A-F]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class ReleaseAuthorityViolation(RuntimeError):
    """Raised when the promoted release authority is not authenticated."""


def _git_blob(root: Path, relative: str) -> bytes:
    try:
        return subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=root)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseAuthorityViolation(f"missing committed authority input: {relative}") from exc


def _equivalent(checkout: bytes, committed: bytes) -> bool:
    return checkout.replace(b"\r\n", b"\n") == committed.replace(b"\r\n", b"\n")


def _authenticated_json(root: Path, relative: str, sidecar_relative: str) -> tuple[dict, str]:
    committed = _git_blob(root, relative)
    committed_sidecar = _git_blob(root, sidecar_relative)
    try:
        checkout = (root / relative).read_bytes()
        checkout_sidecar = (root / sidecar_relative).read_bytes()
    except OSError as exc:
        raise ReleaseAuthorityViolation(f"missing checkout authority input: {relative}") from exc
    if not _equivalent(checkout, committed) or not _equivalent(checkout_sidecar, committed_sidecar):
        raise ReleaseAuthorityViolation(
            f"checkout differs from committed authority input: {relative}"
        )
    try:
        expected = committed_sidecar.decode("ascii").split()[0].upper()
        packet = json.loads(committed)
    except (IndexError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReleaseAuthorityViolation(f"malformed authority input: {relative}") from exc
    digest = hashlib.sha256(committed).hexdigest().upper()
    if not HEX64.fullmatch(expected) or expected != digest:
        raise ReleaseAuthorityViolation(f"authority sidecar does not authenticate: {relative}")
    if not isinstance(packet, dict):
        raise ReleaseAuthorityViolation(f"authority input is not an object: {relative}")
    return packet, digest


def authenticate_release_authority(repository_root: Path) -> dict[str, object]:
    root = repository_root.resolve()
    authority, authority_hash = _authenticated_json(root, AUTHORITY_REL, f"{AUTHORITY_REL}.sha256")
    if authority.get("scheme") != "calibration-release-authority-v1":
        raise ReleaseAuthorityViolation("unexpected release authority scheme")
    if authority.get("execution_authorized") is not False:
        raise ReleaseAuthorityViolation("release authority authorizes execution")

    selected = authority.get("selected_runtime_artifact")
    historical = authority.get("historical_v16_baseline")
    renderer = authority.get("renderer")
    decks = authority.get("frozen_deck_manifest")
    if not all(isinstance(item, dict) for item in (selected, historical, renderer, decks)):
        raise ReleaseAuthorityViolation("release authority has incomplete input identities")

    selected_packet, selected_hash = _authenticated_json(
        root, selected["rel"], f"{selected['rel']}.sha256"
    )
    if selected_hash != selected["sha256"]:
        raise ReleaseAuthorityViolation("selected runtime artifact hash disagrees with authority")
    if selected_packet.get("scheme") != "calibration-release-baseline-refresh-v17":
        raise ReleaseAuthorityViolation("selected runtime artifact is not V17")
    if selected_packet.get("execution_authorized") is not False:
        raise ReleaseAuthorityViolation("selected runtime artifact authorizes execution")
    if selected_packet.get("accepted_runtime") != authority.get("accepted_runtime"):
        raise ReleaseAuthorityViolation("selected runtime identity disagrees with authority")
    if not HEX40.fullmatch(str(authority.get("accepted_runtime"))):
        raise ReleaseAuthorityViolation("accepted runtime identity is malformed")
    for field in (
        "protocol",
        "protocol_identity",
        "seed_table_v2_sha256",
        "seed_table_v2_entropy_sha256",
    ):
        if selected_packet.get(field) != authority.get(field):
            raise ReleaseAuthorityViolation(f"selected runtime {field} disagrees with authority")

    v16, v16_hash = _authenticated_json(root, historical["rel"], f"{historical['rel']}.sha256")
    if v16_hash != historical["sha256"] or historical.get("immutable") is not True:
        raise ReleaseAuthorityViolation("historical V16 baseline identity is not immutable")
    if v16.get("execution_authorized") is not False or v16.get("protocol") != "V1":
        raise ReleaseAuthorityViolation(
            "historical V16 baseline is not a valid non-authorizing baseline"
        )

    renderer_bytes = _git_blob(root, renderer["rel"])
    renderer_hash = hashlib.sha256(renderer_bytes).hexdigest().upper()
    if renderer_hash != renderer["sha256"]:
        raise ReleaseAuthorityViolation("renderer identity disagrees with authority")
    if not _equivalent((root / renderer["rel"]).read_bytes(), renderer_bytes):
        raise ReleaseAuthorityViolation("renderer checkout differs from committed Git blob")

    capacity_bytes = _git_blob(root, decks["rel"])
    capacity_hash = hashlib.sha256(capacity_bytes).hexdigest().upper()
    if capacity_hash != decks["sha256"]:
        raise ReleaseAuthorityViolation("frozen deck manifest identity disagrees with authority")
    capacity = json.loads(capacity_bytes)
    if not isinstance(capacity.get("deck_hashes"), dict) or len(capacity["deck_hashes"]) != 10:
        raise ReleaseAuthorityViolation("frozen deck manifest is incomplete")

    return {
        "authority_rel": AUTHORITY_REL,
        "authority_sha256": authority_hash,
        "selected_runtime_rel": selected["rel"],
        "selected_runtime_sha256": selected_hash,
        "accepted_runtime": authority["accepted_runtime"],
        "protocol": authority["protocol"],
        "protocol_identity": authority["protocol_identity"],
        "seed_table_v2_sha256": authority["seed_table_v2_sha256"],
        "seed_table_v2_entropy_sha256": authority["seed_table_v2_entropy_sha256"],
        "v16_baseline_rel": historical["rel"],
        "v16_baseline_sha256": v16_hash,
        "renderer_rel": renderer["rel"],
        "renderer_sha256": renderer_hash,
        "frozen_deck_manifest_rel": decks["rel"],
        "frozen_deck_manifest_sha256": capacity_hash,
        "deck_hashes": capacity["deck_hashes"],
        "schedule": selected_packet["schedule"],
    }
