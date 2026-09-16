"""Protocol V1 execution ledger infrastructure; no scoring or balance analysis."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class ProtocolMember:
    member_id: str
    block: int
    pair_index: int
    orientation: str
    seed: int
    decks: tuple[str, str]


class ProtocolViolation(RuntimeError):
    pass


def load_members(
    seed_table: Path, *, strict: bool = False, expected_sha256: str | None = None
) -> tuple[ProtocolMember, ...]:
    checkout_bytes = seed_table.read_bytes()
    data = json.loads(checkout_bytes)
    if expected_sha256 is not None:
        try:
            repo_root_raw = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], text=True
            )
            if isinstance(repo_root_raw, bytes):
                repo_root_raw = repo_root_raw.decode()
            repo_root = Path(repo_root_raw.strip())
            relative = seed_table.resolve().relative_to(repo_root).as_posix()
            committed_bytes = subprocess.check_output(
                ["git", "show", f"HEAD:{relative}"], cwd=repo_root
            )
        except ValueError as exc:
            raise ProtocolViolation("seed table is outside the repository") from exc
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ProtocolViolation("unable to read authoritative seed table blob") from exc
        if hashlib.sha256(committed_bytes).hexdigest() != expected_sha256.lower():
            raise ProtocolViolation("seed table hash mismatch")
        if data != json.loads(committed_bytes):
            raise ProtocolViolation("seed table checkout diverges from committed artifact")
    rows = data.get("rows")
    if not isinstance(rows, list):
        raise ProtocolViolation("seed table rows missing")
    members = []
    seen = set()
    for row in rows:
        try:
            block = int(row["block"])
            pair = int(row["pair_index"])
            orientation = row["orientation"]
            seed = int(row["seed"])
            decks = tuple(row["decks"])
        except (KeyError, TypeError, ValueError) as e:
            raise ProtocolViolation("malformed seed row") from e
        if orientation not in ("canonical", "reversed") or len(decks) != 2:
            raise ProtocolViolation("invalid seed row")
        member_id = f"b{block:04d}-p{pair:02d}-{orientation}"
        if member_id in seen:
            raise ProtocolViolation("duplicate member id")
        seen.add(member_id)
        members.append(
            ProtocolMember(
                member_id, block, pair, orientation, seed, (str(decks[0]), str(decks[1]))
            )
        )
    if strict:
        if (
            data.get("blocks") != 2048
            or data.get("pairs") != 45
            or data.get("orientations") != ["canonical", "reversed"]
        ):
            raise ProtocolViolation("seed table dimensions mismatch")
        if len(members) != 184320:
            raise ProtocolViolation("incomplete V1 schedule")
        expected = {
            (b, p, o) for b in range(2048) for p in range(45) for o in ("canonical", "reversed")
        }
        actual = {(m.block, m.pair_index, m.orientation) for m in members}
        if actual != expected:
            raise ProtocolViolation("seed table pair/orientation membership mismatch")
    return tuple(members)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _write_heartbeat(
    output: Path, run_id: str, member_id: str, phase: str, completed: int, returned: int
) -> None:
    payload = {
        "run_id": run_id,
        "active_member_id": member_id,
        "phase": phase,
        "completed_member_count": completed,
        "returned_execution_count": returned,
        "utc_timestamp": datetime.now(UTC).isoformat(),
        "diagnostic_only": True,
        "resumability_authority": False,
        "completion_authority": False,
        "statistical_evidence": False,
    }
    _atomic_write(
        output / "RUN_HEARTBEAT.json", json.dumps(payload, sort_keys=True, indent=2).encode()
    )


def execute_protocol(
    seed_table: Path,
    output: Path,
    executor: Callable[[ProtocolMember, int], dict],
    *,
    max_members: int | None = None,
    strict: bool = False,
    expected_seed_table_sha256: str | None = None,
) -> dict:
    members = load_members(seed_table, strict=strict, expected_sha256=expected_seed_table_sha256)
    if strict and max_members is not None:
        raise ProtocolViolation("max_members is forbidden in strict mode")
    if max_members is not None:
        members = members[:max_members]
    ledger = []
    completed = 0
    returned = 0
    run_id = output.name
    for member in members:
        try:
            _write_heartbeat(output, run_id, member.member_id, "member_start", completed, returned)
            first = executor(member, 0)
            returned += 1
            _write_heartbeat(
                output, run_id, member.member_id, "duplicate_1_returned", completed, returned
            )
            second = executor(member, 1)
            returned += 1
            _write_heartbeat(
                output, run_id, member.member_id, "duplicate_2_returned", completed, returned
            )
            if strict:
                for result in (first, second):
                    if not result.get("terminal", False):
                        raise ProtocolViolation("execution did not reach terminal state")
                    if result.get("turns_started", 0) >= 120:
                        raise ProtocolViolation("attempted to begin turn 120")
            a = json.dumps(
                first, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
            b = json.dumps(
                second, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
            h1 = hashlib.sha256(a).hexdigest()
            h2 = hashlib.sha256(b).hexdigest()
            if h1 != h2 or a != b:
                raise ProtocolViolation(f"duplicate mismatch: {member.member_id}")
            record = {
                "member_id": member.member_id,
                "block": member.block,
                "pair_index": member.pair_index,
                "orientation": member.orientation,
                "seed": member.seed,
                "decks": list(member.decks),
                "duplicate_equal": True,
                "primary_sha256": h1,
                "raw": first,
            }
            _atomic_write(
                output / f"{member.member_id}.json",
                json.dumps(record, sort_keys=True, indent=2).encode(),
            )
            _write_heartbeat(
                output, run_id, member.member_id, "member_evidence_written", completed + 1, returned
            )
            ledger.append(
                {
                    "member_id": member.member_id,
                    "status": "complete",
                    "primary_sha256": h1,
                    "duplicate_sha256": h2,
                }
            )
            completed += 1
        except Exception as exc:
            ledger.append(
                {
                    "member_id": member.member_id,
                    "status": "failed",
                    "error": str(exc),
                    "completed_before": completed,
                }
            )
            _atomic_write(
                output / "EXECUTION_LEDGER.json",
                json.dumps(
                    {
                        "status": "FAIL_CLOSED_STOP",
                        "completed_members": completed,
                        "failed_member": member.member_id,
                        "ledger": ledger,
                    },
                    indent=2,
                ).encode(),
            )
            raise ProtocolViolation(f"fail-closed at {member.member_id}: {exc}") from exc
    result = {
        "status": "COMPLETE_PENDING_AUDIT",
        "completed_members": completed,
        "total_members": len(members),
        "ledger": ledger,
        "calibration_observations": 0,
    }
    _atomic_write(output / "EXECUTION_LEDGER.json", json.dumps(result, indent=2).encode())
    return result
