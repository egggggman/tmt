"""Strict ten-entry manifest and sequential-dispatch contract for Stage 002.

This module contains no signing key and never starts a gameplay process on
import. The owner-controlled issuer signs its validated per-entry claims; the
existing supervisor remains responsible for each isolated one-game worker.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

SCHEMA = "cardcade-stage002-batch-v1"
ENTRY_SCHEMA = "cardcade-stage002-batch-entry-v1"
GAME_COUNT = 10
MEMORY_LIMIT_BYTES = 2_997_489_664
RUNTIME_LIMIT_SECONDS = 600
_BATCH_ID = re.compile(r"cardcade-smoke10-[A-Za-z0-9_-]{1,48}\Z")
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")
_DECKS: dict[str, tuple[str, str]] = {
    "leonardo": (
        "docs/objective-balance-lab/candidates/LEONARDO_OBL_R1.txt",
        "4d5db15f72595d5377c3cd2c6ee57374176fc211a1669ea99c74a8e75744a960",
    ),
    "raphael": (
        "docs/objective-balance-lab/baselines/RAPHAEL_OBL_BASELINE_002.txt",
        "e8d29b97e4fa52bd1a8ae0d8056b5217660b1367e0a386e811908e256dea711f",
    ),
    "donatello": (
        "docs/objective-balance-lab/candidates/DONATELLO_OBL_R2_A.txt",
        "d9baf095831d82d7fae01af75b61ecf0debefe04a14ad945e67e0db696aa09c6",
    ),
    "michelangelo": (
        "decks/michelangelo/PROTOTYPE_0.1.txt",
        "f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9",
    ),
    "splinter": (
        "decks/splinter/PROTOTYPE_0.1.txt",
        "74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a",
    ),
    "shredder": (
        "docs/objective-balance-lab/baselines/SHREDDER_OBL_BASELINE_003.txt",
        "1ce0828b6ac107bc8cdf2e0b965d919e83941316803880a71d11bbbb48902fc1",
    ),
    "krang": (
        "docs/objective-balance-lab/baselines/KRANG_OBL_BASELINE_004.txt",
        "2d598af2d05212ffb0f19fe5f315b7bf8f85501975155f394448b0a48fa81ab1",
    ),
    "bebop_rocksteady": (
        "docs/objective-balance-lab/baselines/BEBOP_ROCKSTEADY_OBL_BASELINE_005.txt",
        "aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed",
    ),
    "april_oneil": (
        "docs/objective-balance-lab/baselines/APRIL_ONEIL_OBL_BASELINE_003.txt",
        "ebaff265d90b5cfbec4f7e9662a9d105f9ef8f58a17b06949626ed2ff898b8b7",
    ),
    "casey_jones": (
        "docs/objective-balance-lab/candidates/CASEY_JONES_OBL_R2_B.txt",
        "9cf8a038530dad01f4bc64bc9293889abe389cd043845cf6d538dd29865ad170",
    ),
}
_MATRIX = (
    ("raphael", "shredder", 8301, "canonical", "raphael--shredder"),
    ("shredder", "raphael", 8302, "reversed", "raphael--shredder"),
    ("donatello", "bebop_rocksteady", 8303, "canonical", "bebop_rocksteady--donatello"),
    ("bebop_rocksteady", "donatello", 8304, "reversed", "bebop_rocksteady--donatello"),
    ("krang", "michelangelo", 8305, "canonical", "krang--michelangelo"),
    ("michelangelo", "krang", 8306, "reversed", "krang--michelangelo"),
    ("april_oneil", "casey_jones", 8307, "canonical", "april_oneil--casey_jones"),
    ("casey_jones", "april_oneil", 8308, "reversed", "april_oneil--casey_jones"),
    ("leonardo", "splinter", 8309, "canonical", "leonardo--splinter"),
    ("splinter", "leonardo", 8310, "reversed", "leonardo--splinter"),
)


def create_manifest(
    *,
    source_commit: str,
    source_blobs: Mapping[str, str],
    baseline_manifest_sha256: str,
    card_data_sha256: str,
    runtime: Mapping[str, str],
    supervisor_sha256: str,
    batch_controller_sha256: str,
    issuer_sha256: str,
    output_root: str,
    authorization_root: str,
    baseline_input_root: str,
    batch_id: str = "cardcade-smoke10-20261031",
) -> dict[str, Any]:
    output = Path(output_root).resolve(strict=False)
    auth = Path(authorization_root).resolve(strict=False)
    games = []
    for index, (left, right, seed, orientation, pairing_id) in enumerate(_MATRIX, 1):
        run_id = f"{batch_id}-g{index:02d}"
        games.append(
            {
                "entry_schema": ENTRY_SCHEMA,
                "index": index,
                "run_id": run_id,
                "seed": seed,
                "orientation": orientation,
                "seats": [
                    {"deck_key": key, "source_path": _DECKS[key][0], "sha256": _DECKS[key][1]}
                    for key in (left, right)
                ],
                "pairing_id": pairing_id,
                "game_count": 1,
                "worker_invocations": 1,
                "automatic_retries": 0,
                "output_destination": str(output / run_id),
                "authorization_file": str(auth / batch_id / f"{run_id}.json"),
            }
        )
    return {
        "schema": SCHEMA,
        "batch_id": batch_id,
        "source_commit": source_commit,
        "source_blobs": dict(source_blobs),
        "baseline_manifest_sha256": baseline_manifest_sha256,
        "card_data_sha256": card_data_sha256,
        "runtime": dict(runtime),
        "supervisor_sha256": supervisor_sha256,
        "batch_controller_sha256": batch_controller_sha256,
        "issuer_sha256": issuer_sha256,
        "memory_accounting": "committed_memory",
        "process_memory_limit_bytes": MEMORY_LIMIT_BYTES,
        "job_memory_limit_bytes": MEMORY_LIMIT_BYTES,
        "runtime_seconds_limit": RUNTIME_LIMIT_SECONDS,
        "maximum_games": GAME_COUNT,
        "automatic_retries": 0,
        "output_root": str(output),
        "authorization_root": str(auth),
        "baseline_input_root": str(Path(baseline_input_root).resolve(strict=False)),
        "batch_status_path": str(output / f"{batch_id}.status.json"),
        "games": games,
    }


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _contained(path_value: str, root_value: str, label: str) -> Path:
    path = Path(path_value).resolve(strict=False)
    root = Path(root_value).resolve(strict=False)
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} is outside its assigned root") from exc
    lowered = tuple(part.casefold() for part in path.parts)
    if any("durable001" in part or "checkpoint" in part for part in lowered):
        raise ValueError(f"{label} uses a protected path")
    return path


def validate_manifest(
    manifest: Mapping[str, Any],
    *,
    source_commit: str,
    source_blobs: Mapping[str, str],
    card_data_sha256: str,
    runtime: Mapping[str, str],
    supervisor_sha256: str,
    batch_controller_sha256: str,
    issuer_sha256: str,
    baseline_manifest_sha256: str,
    output_root: str,
    authorization_root: str,
    baseline_input_root: str,
    batch_status_path: str,
    check_vacant: bool = False,
    require_authorizations: bool = False,
) -> str:
    """Validate every row and immutable execution identity before any signing."""
    required = {
        "schema",
        "batch_id",
        "source_commit",
        "source_blobs",
        "baseline_manifest_sha256",
        "card_data_sha256",
        "runtime",
        "supervisor_sha256",
        "batch_controller_sha256",
        "issuer_sha256",
        "memory_accounting",
        "process_memory_limit_bytes",
        "job_memory_limit_bytes",
        "runtime_seconds_limit",
        "maximum_games",
        "automatic_retries",
        "output_root",
        "authorization_root",
        "baseline_input_root",
        "batch_status_path",
        "games",
    }
    if set(manifest) != required:
        raise ValueError("batch manifest fields do not match the strict schema")
    if manifest["schema"] != SCHEMA:
        raise ValueError("unsupported batch manifest schema")
    if not isinstance(manifest["batch_id"], str) or not _BATCH_ID.fullmatch(manifest["batch_id"]):
        raise ValueError("batch identifier is invalid")
    for field in (
        "process_memory_limit_bytes",
        "job_memory_limit_bytes",
        "runtime_seconds_limit",
        "maximum_games",
        "automatic_retries",
    ):
        if type(manifest[field]) is not int:
            raise ValueError(f"batch manifest integer field is invalid: {field}")
    fixed = {
        "source_commit": source_commit,
        "source_blobs": dict(source_blobs),
        "baseline_manifest_sha256": baseline_manifest_sha256,
        "card_data_sha256": card_data_sha256,
        "runtime": dict(runtime),
        "supervisor_sha256": supervisor_sha256,
        "batch_controller_sha256": batch_controller_sha256,
        "issuer_sha256": issuer_sha256,
        "memory_accounting": "committed_memory",
        "process_memory_limit_bytes": MEMORY_LIMIT_BYTES,
        "job_memory_limit_bytes": MEMORY_LIMIT_BYTES,
        "runtime_seconds_limit": RUNTIME_LIMIT_SECONDS,
        "maximum_games": GAME_COUNT,
        "automatic_retries": 0,
    }
    for name, expected in fixed.items():
        if manifest[name] != expected:
            raise ValueError(f"batch manifest identity or limit mismatch: {name}")
    root = Path(str(manifest["output_root"])).resolve(strict=False)
    auth_root = Path(str(manifest["authorization_root"])).resolve(strict=False)
    status = _contained(str(manifest["batch_status_path"]), str(root), "batch status path")
    batch_lock = status.with_suffix(status.suffix + ".lock")
    if root != Path(output_root).resolve(strict=False):
        raise ValueError("batch output root differs from the approved diagnostic root")
    if auth_root != Path(authorization_root).resolve(strict=False):
        raise ValueError("batch authorization root differs from the protected issuer root")
    if Path(str(manifest["baseline_input_root"])).resolve(strict=False) != Path(
        baseline_input_root
    ).resolve(strict=False):
        raise ValueError("Baseline 005 input root differs from its authenticated assignment")
    if len(manifest["games"]) != GAME_COUNT:
        raise ValueError("manifest must contain exactly ten games")
    if check_vacant and require_authorizations:
        raise ValueError("authorization destination mode is ambiguous")
    if check_vacant and (status.exists() or batch_lock.exists()):
        raise FileExistsError("batch status or lock destination is already used")
    seen_ids: set[str] = set()
    seen_outputs: set[Path] = set()
    seen_auth: set[Path] = set()
    seen_decks: set[str] = set()
    seen_seeds: set[int] = set()
    seen_matchup_seed_orientation: set[tuple[tuple[str, str], int, str]] = set()
    for index, row in enumerate(manifest["games"], 1):
        if not isinstance(row, Mapping) or set(row) != {
            "entry_schema",
            "index",
            "run_id",
            "seed",
            "orientation",
            "seats",
            "pairing_id",
            "game_count",
            "worker_invocations",
            "automatic_retries",
            "output_destination",
            "authorization_file",
        }:
            raise ValueError(f"game row {index} fields do not match the strict schema")
        run_id = f"{manifest['batch_id']}-g{index:02d}"
        if type(row["index"]) is not int or row["index"] != index:
            raise ValueError(f"game row {index} index is invalid")
        if not _SAFE_ID.fullmatch(str(row["run_id"])) or row["run_id"] != run_id:
            raise ValueError(f"game row {index} run id is invalid")
        if type(row["seed"]) is not int or not 0 <= row["seed"] <= 0xFFFFFFFF:
            raise ValueError(f"game row {index} seed is invalid")
        if row["seed"] in seen_seeds:
            raise ValueError("batch seeds must be unique")
        if not isinstance(row["orientation"], str) or row["orientation"] not in {
            "canonical",
            "reversed",
        }:
            raise ValueError(f"game row {index} orientation is invalid")
        for field in ("game_count", "worker_invocations", "automatic_retries"):
            if type(row[field]) is not int:
                raise ValueError(f"game row {index} integer field is invalid: {field}")
        seats = row["seats"]
        if not isinstance(seats, list) or len(seats) != 2:
            raise ValueError(f"game row {index} must contain two Baseline 005 decks")
        expected_seats = []
        deck_keys = []
        for seat in seats:
            if not isinstance(seat, Mapping) or set(seat) != {"deck_key", "source_path", "sha256"}:
                raise ValueError(f"game row {index} deck identity fields are invalid")
            deck_key = seat["deck_key"]
            if not isinstance(deck_key, str) or deck_key not in _DECKS:
                raise ValueError(f"game row {index} selects an unapproved deck")
            expected_path, expected_sha = _DECKS[deck_key]
            expected_seats.append(
                {"deck_key": deck_key, "source_path": expected_path, "sha256": expected_sha}
            )
            deck_keys.append(deck_key)
        if deck_keys[0] == deck_keys[1] or list(seats) != expected_seats:
            raise ValueError(f"game row {index} deck order or identity is invalid")
        pairing_id = "--".join(sorted(deck_keys))
        matchup_key = (tuple(sorted(deck_keys)), row["seed"], row["orientation"])
        if matchup_key in seen_matchup_seed_orientation:
            raise ValueError(f"game row {index} repeats a matchup, seed and orientation")
        seen_matchup_seed_orientation.add(matchup_key)
        seen_seeds.add(row["seed"])
        expected_row = {
            "entry_schema": ENTRY_SCHEMA,
            "index": index,
            "run_id": run_id,
            "seed": row["seed"],
            "orientation": row["orientation"],
            "seats": expected_seats,
            "pairing_id": pairing_id,
            "game_count": 1,
            "worker_invocations": 1,
            "automatic_retries": 0,
            "output_destination": str(root / run_id),
            "authorization_file": str(auth_root / str(manifest["batch_id"]) / f"{run_id}.json"),
        }
        if dict(row) != expected_row:
            raise ValueError(f"game row {index} differs from the approved matrix or contract")
        if run_id in seen_ids:
            raise ValueError(f"game row {index} run id is invalid or repeated")
        output = _contained(str(row["output_destination"]), str(root), "game output")
        auth = _contained(str(row["authorization_file"]), str(auth_root), "authorization file")
        if output in seen_outputs or auth in seen_auth:
            raise ValueError("game output or authorization destination is repeated")
        if check_vacant and output.exists():
            raise FileExistsError(f"game row {index} output is already used")
        seen_ids.add(run_id)
        seen_outputs.add(output)
        seen_auth.add(auth)
        seen_decks.update(deck_keys)
    if seen_decks != set(_DECKS):
        raise ValueError("manifest does not cover the exact ten Baseline 005 decks")
    authorization_directory = auth_root / str(manifest["batch_id"])
    expected_authorizations = {path.name for path in seen_auth}
    if check_vacant and authorization_directory.exists():
        raise FileExistsError("batch authorization directory is already used")
    if require_authorizations:
        if not authorization_directory.is_dir() or authorization_directory.is_symlink():
            raise FileNotFoundError("expected batch authorization directory is missing or unsafe")
        entries = list(authorization_directory.iterdir())
        if {entry.name for entry in entries} != expected_authorizations:
            raise FileExistsError("batch authorization directory has missing or unexpected entries")
        if any(not entry.is_file() or entry.is_symlink() for entry in entries):
            raise FileExistsError("batch authorization entry is not a regular file")
        for row in manifest["games"]:
            if Path(row["output_destination"]).exists():
                raise FileExistsError(f"game row {row['index']} output is already used")
        if status.exists() or batch_lock.exists():
            raise FileExistsError("batch status or lock destination is already used")
    return hashlib.sha256(canonical_json(dict(manifest))).hexdigest()


def entry_claims(manifest: Mapping[str, Any], manifest_sha256: str, index: int) -> dict[str, Any]:
    if type(index) is not int or not 1 <= index <= GAME_COUNT:
        raise ValueError("batch entry index is outside the ten-game manifest")
    row = manifest["games"][index - 1]
    row_copy = dict(row)
    return {
        "batch_id": manifest["batch_id"],
        "batch_manifest_sha256": manifest_sha256,
        "batch_entry_sha256": digest(row_copy),
        **row_copy,
        "matchup": f"{row['pairing_id'].replace('--', '-vs-')}-baseline005",
        "deck_sha256": {seat["deck_key"]: seat["sha256"] for seat in row["seats"]},
        "source_commit": manifest["source_commit"],
        "source_blobs": manifest["source_blobs"],
        "baseline_manifest_sha256": manifest["baseline_manifest_sha256"],
        "card_data_sha256": manifest["card_data_sha256"],
        "runtime": manifest["runtime"],
        "supervisor_sha256": manifest["supervisor_sha256"],
        "batch_controller_sha256": manifest["batch_controller_sha256"],
        "issuer_sha256": manifest["issuer_sha256"],
        "memory_accounting": manifest["memory_accounting"],
        "process_memory_limit_bytes": manifest["process_memory_limit_bytes"],
        "job_memory_limit_bytes": manifest["job_memory_limit_bytes"],
        "runtime_seconds_limit": manifest["runtime_seconds_limit"],
        "maximum_games": 1,
        "game_count": 1,
        "worker_invocations": 1,
        "automatic_retries": 0,
        "allow_retry": False,
        "python_executable_sha256": manifest["runtime"]["python_executable_sha256"],
        "python_version": manifest["runtime"]["python_version"],
        "python_nuget_package_sha512": manifest["runtime"]["python_nuget_package_sha512"],
        "uv_lock_sha256": manifest["runtime"]["uv_lock_sha256"],
    }


def run_sequential_batch(
    manifest: Mapping[str, Any],
    manifest_sha256: str,
    *,
    consume_and_dispatch: Callable[[Mapping[str, Any], str], Mapping[str, Any]],
    persist: Callable[[Mapping[str, Any]], None],
    preflight_info: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run serially; persist every terminal row and never resume/retry."""
    state: dict[str, Any] = {
        "label": "DIAGNOSTIC",
        "batch_id": manifest["batch_id"],
        "manifest_sha256": manifest_sha256,
        "state": "RUNNING",
        "next_index": 1,
        "games": [],
        "completed_games": 0,
        "automatic_retries": 0,
    }
    if preflight_info is not None:
        state["preflight"] = dict(preflight_info)
    persist(state)
    for index, row in enumerate(manifest["games"], 1):
        state["active_index"] = index
        state["active_run_id"] = row["run_id"]
        persist(state)
        try:
            outcome = dict(consume_and_dispatch(row, manifest_sha256))
        except BaseException as exc:
            outcome = {
                "state": "SAFETY_BLOCKED",
                "failure_type": type(exc).__name__,
                "failure_message": str(exc),
            }
        if outcome.get("state") in {
            "SAFETY_BLOCKED",
            "PREFLIGHT_FAILED",
            "SUPERVISOR_FAILED",
            "TIMEOUT",
        }:
            state["games"].append({"index": index, "run_id": row["run_id"], **outcome})
            state["state"] = "STOPPED_SAFETY_FAILURE"
            state["next_index"] = index
            state["stopped_index"] = index
            persist(state)
            return state
        if outcome.get("state") not in {"RETURNED", "FAILED", "TIMEOUT"}:
            state["games"].append(
                {
                    "index": index,
                    "run_id": row["run_id"],
                    "state": "SAFETY_BLOCKED",
                    "failure_message": "invalid terminal outcome",
                }
            )
            state["state"] = "STOPPED_EVIDENCE_FAILURE"
            state["next_index"] = index
            state["stopped_index"] = index
            persist(state)
            return state
        if outcome["state"] == "RETURNED" and outcome.get("exit_code") != 0:
            outcome["state"] = "SAFETY_BLOCKED"
            outcome["failure_message"] = "RETURNED outcome has non-zero exit code"
            state["games"].append({"index": index, "run_id": row["run_id"], **outcome})
            state["state"] = "STOPPED_EVIDENCE_FAILURE"
            state["next_index"] = index
            state["stopped_index"] = index
            persist(state)
            return state
        state["games"].append({"index": index, "run_id": row["run_id"], **outcome})
        if outcome["state"] == "RETURNED":
            state["completed_games"] += 1
        state["next_index"] = index + 1
        state.pop("active_index", None)
        state.pop("active_run_id", None)
        persist(state)
    state["state"] = (
        "COMPLETE"
        if all(item["state"] == "RETURNED" for item in state["games"])
        else "COMPLETE_WITH_GAME_FAILURES"
    )
    persist(state)
    return state
