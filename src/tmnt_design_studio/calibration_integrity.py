"""Fail-closed checkpoint integrity for deterministic calibration runners.

This module owns only schedule/result persistence.  It does not execute games or
interpret gameplay results.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class CheckpointIntegrityError(ValueError):
    """Raised when a schedule, result set, writer, or checkpoint is invalid."""


def canonical_digest(value: Any) -> str:
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def validate_schedule(
    schedule: list[dict[str, Any]],
    *,
    expected_games: int,
    expected_matchups: int,
    games_per_matchup: int,
    orientations: tuple[str, str] = ("candidate_first", "opponent_first"),
) -> dict[str, Any]:
    """Validate the complete immutable schedule before any execution begins."""
    if len(schedule) != expected_games:
        raise CheckpointIntegrityError(
            f"schedule has {len(schedule)} rows, expected {expected_games}"
        )
    ids = [row.get("game_id") for row in schedule]
    if any(not isinstance(game_id, str) or not game_id for game_id in ids):
        raise CheckpointIntegrityError("schedule contains a missing or invalid game_id")
    if len(set(ids)) != len(ids):
        raise CheckpointIntegrityError("schedule contains duplicate game IDs")
    by_matchup: dict[str, list[dict[str, Any]]] = {}
    for row in schedule:
        matchup = row.get("pairing_id")
        orientation = row.get("orientation")
        if not isinstance(matchup, str) or orientation not in orientations:
            raise CheckpointIntegrityError("schedule row has invalid matchup or orientation")
        by_matchup.setdefault(matchup, []).append(row)
    if len(by_matchup) != expected_matchups:
        raise CheckpointIntegrityError(
            f"schedule has {len(by_matchup)} matchups, expected {expected_matchups}"
        )
    required_per_orientation = games_per_matchup // len(orientations)
    for matchup, rows in by_matchup.items():
        if len(rows) != games_per_matchup:
            raise CheckpointIntegrityError(
                f"{matchup} has {len(rows)} games, expected {games_per_matchup}"
            )
        counts = {
            orientation: sum(r["orientation"] == orientation for r in rows)
            for orientation in orientations
        }
        if any(count != required_per_orientation for count in counts.values()):
            raise CheckpointIntegrityError(f"{matchup} has invalid orientation counts: {counts}")
    return {"schedule": copy.deepcopy(schedule), "schedule_digest": canonical_digest(schedule)}


class CheckpointAccumulator:
    """Single-writer, idempotent accumulator for completed game records."""

    def __init__(self, schedule: list[dict[str, Any]], *, writer_id: str):
        self._schedule = copy.deepcopy(schedule)
        self._expected = {row["game_id"]: row for row in self._schedule}
        self._records: dict[str, dict[str, Any]] = {}
        self._writer_id = writer_id
        self._claimed = False
        self._schedule_digest = canonical_digest(self._schedule)

    @property
    def schedule_digest(self) -> str:
        return self._schedule_digest

    def claim(self, writer_id: str) -> None:
        if self._claimed and writer_id != self._writer_id:
            raise CheckpointIntegrityError("checkpoint already has a different writer")
        if writer_id != self._writer_id:
            raise CheckpointIntegrityError("writer is not authorized for this checkpoint")
        self._claimed = True

    def append(self, record: dict[str, Any], *, writer_id: str) -> None:
        self.claim(writer_id)
        game_id = record.get("game_id")
        if game_id not in self._expected:
            raise CheckpointIntegrityError(f"record is not in the authorized schedule: {game_id!r}")
        if game_id in self._records:
            raise CheckpointIntegrityError(f"duplicate completed game ID: {game_id}")
        self._records[game_id] = copy.deepcopy(record)

    def snapshot(self) -> dict[str, Any]:
        records = [
            copy.deepcopy(self._records[game_id])
            for game_id in self._expected
            if game_id in self._records
        ]
        return {
            "schedule_digest": self._schedule_digest,
            "schedule_games": len(self._schedule),
            "completed_games": len(records),
            "records": records,
        }

    def restore(self, payload: dict[str, Any]) -> None:
        """Restore a validated partial checkpoint without replaying completed IDs."""
        validate_checkpoint(payload, self._schedule)
        for record in payload["records"]:
            game_id = record["game_id"]
            if game_id in self._records:
                raise CheckpointIntegrityError(f"duplicate restored game ID: {game_id}")
            self._records[game_id] = copy.deepcopy(record)

    def assert_complete(self) -> None:
        if set(self._records) != set(self._expected):
            missing = sorted(set(self._expected) - set(self._records))
            raise CheckpointIntegrityError(
                f"checkpoint is incomplete; missing {len(missing)} games"
            )

    def write(self, path: Path, *, writer_id: str) -> dict[str, Any]:
        self.claim(writer_id)
        payload = self.snapshot()
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, sort_keys=True, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return copy.deepcopy(payload)


def validate_checkpoint(payload: dict[str, Any], schedule: list[dict[str, Any]]) -> None:
    """Validate a checkpoint against the exact schedule; incomplete is allowed only as recovery."""
    expected = validate_schedule(
        schedule,
        expected_games=len(schedule),
        expected_matchups=len({row["pairing_id"] for row in schedule}),
        games_per_matchup=len(schedule) // len({row["pairing_id"] for row in schedule}),
    )
    if payload.get("schedule_digest") != expected["schedule_digest"]:
        raise CheckpointIntegrityError("checkpoint schedule identity does not match")
    records = payload.get("records")
    if not isinstance(records, list):
        raise CheckpointIntegrityError("checkpoint records must be a list")
    ids = [record.get("game_id") for record in records if isinstance(record, dict)]
    if len(ids) != len(records) or len(set(ids)) != len(ids):
        raise CheckpointIntegrityError("checkpoint contains missing or duplicate game IDs")
    authorized = {row["game_id"] for row in schedule}
    if set(ids) - authorized:
        raise CheckpointIntegrityError("checkpoint contains unauthorized game IDs")


class WriterLock:
    """Exclusive process-level ownership marker for one checkpoint path."""

    def __init__(self, path: Path, writer_id: str):
        self.path = Path(f"{path}.lock")
        self.writer_id = writer_id
        self._held = False

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise CheckpointIntegrityError("checkpoint writer ownership is already held") from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(self.writer_id + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self._held = True

    def release(self) -> None:
        if self._held:
            self.path.unlink(missing_ok=True)
            self._held = False

    def __enter__(self) -> WriterLock:
        self.acquire()
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.release()
