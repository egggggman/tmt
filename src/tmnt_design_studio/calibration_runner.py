"""Protocol V1 execution ledger infrastructure; no scoring or balance analysis."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
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
    digest = hashlib.sha256(seed_table.read_bytes()).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ProtocolViolation("seed table hash mismatch")
    data = json.loads(seed_table.read_text(encoding="utf-8"))
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
    for member in members:
        try:
            first = executor(member, 0)
            second = executor(member, 1)
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
