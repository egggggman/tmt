"""Fail-closed checkpoint integrity for deterministic calibration runners.

This module owns only schedule/result persistence.  It does not execute games or
interpret gameplay results.
"""

from __future__ import annotations

import copy
import errno
import hashlib
import json
import os
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


class CheckpointIntegrityError(ValueError):
    """Raised when a schedule, result set, writer, or checkpoint is invalid."""


def note_cleanup(primary: BaseException, cleanup: BaseException, stage: str, resource: str) -> None:
    """Keep initiating exception identity; attach separate owned-cleanup evidence."""
    failures = getattr(primary, "cleanup_failures", [])
    failures.append((stage, resource, cleanup))
    primary.cleanup_failures = failures


class _HashingText:
    """Hash expected UTF-8 LF bytes from serialization, not altered disk bytes."""

    def __init__(self, stream):
        self.stream = stream
        self.digest = hashlib.sha256()
        self.bytes = 0

    def write(self, text: str) -> int:
        size = self.stream.write(text)
        if size != len(text):
            raise OSError("short checkpoint serialization write")
        raw = text.encode("utf-8")
        self.digest.update(raw)
        self.bytes += len(raw)
        return size


def _disk_digest(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def _replace_with_retry(source: str, destination: Path) -> None:
    """Retry only a transient Windows replacement denial of the same fsynced file."""
    first_error: PermissionError | None = None
    for attempt in range(8):
        try:
            os.replace(source, destination)
            return
        except PermissionError as exc:
            if getattr(exc, "winerror", None) not in (5, 32) and exc.errno not in (
                errno.EACCES,
                errno.EPERM,
            ):
                raise
            if first_error is None:
                first_error = exc
            if attempt == 7:
                if first_error is exc:
                    raise
                raise first_error from exc
            time.sleep(min(0.05 * (2**attempt), 1.0))


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

    def restore(self, payload: dict[str, Any], *, take_ownership: bool = False) -> None:
        """Restore validated records; transfer ownership only from a disposable payload."""
        validate_checkpoint(payload, self._schedule)
        for record in payload["records"]:
            game_id = record["game_id"]
            if game_id in self._records:
                raise CheckpointIntegrityError(f"duplicate restored game ID: {game_id}")
            self._records[game_id] = record if take_ownership else copy.deepcopy(record)

    @property
    def completed_ids(self) -> set[str]:
        return set(self._records)

    def assert_complete(self) -> None:
        if set(self._records) != set(self._expected):
            missing = sorted(set(self._expected) - set(self._records))
            raise CheckpointIntegrityError(
                f"checkpoint is incomplete; missing {len(missing)} games"
            )

    def write(
        self,
        path: Path,
        *,
        writer_id: str,
        return_snapshot: bool = True,
        verify_bytes: bool = False,
        before_create: Callable[[], None] | None = None,
        before_replace: Callable[[], None] | None = None,
    ) -> dict[str, Any]:
        self.claim(writer_id)
        records = [self._records[game_id] for game_id in self._expected if game_id in self._records]
        payload = {
            "schedule_digest": self._schedule_digest,
            "schedule_games": len(self._schedule),
            "completed_games": len(records),
            "records": records,
        }
        if before_create is not None:
            before_create()
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        failure = None
        timings = {}
        try:
            start = time.perf_counter()
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                sink = _HashingText(handle) if verify_bytes else handle
                json.dump(payload, sink, sort_keys=True, indent=2)
                sink.write("\n")
                timings["serialization_seconds"] = time.perf_counter() - start
                start = time.perf_counter()
                handle.flush()
                os.fsync(handle.fileno())
            timings["flush_fsync_seconds"] = time.perf_counter() - start
            if before_replace is not None:
                before_replace()
            start = time.perf_counter()
            _replace_with_retry(temporary, path)
            timings["replacement_seconds"] = time.perf_counter() - start
            if verify_bytes:
                if before_replace is not None:
                    before_replace()
                start = time.perf_counter()
                actual_hash, actual_bytes = _disk_digest(path)
                timings["readback_hash_seconds"] = time.perf_counter() - start
                if (actual_hash, actual_bytes) != (sink.digest.hexdigest(), sink.bytes):
                    raise CheckpointIntegrityError(
                        "persisted checkpoint differs from expected bytes"
                    )
        except BaseException as error:
            failure = error
            raise
        finally:
            try:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            except BaseException as cleanup:
                if failure is None:
                    raise
                note_cleanup(failure, cleanup, "TEMPORARY_CLEANUP", temporary)
        if return_snapshot:
            return self.snapshot()
        summary = {key: value for key, value in payload.items() if key != "records"}
        if verify_bytes:
            summary.update(
                checkpoint_sha256=actual_hash, checkpoint_bytes=actual_bytes, timings=timings
            )
        return summary


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
    if payload.get("schedule_games") != len(schedule):
        raise CheckpointIntegrityError("checkpoint schedule count does not match")
    records = payload.get("records")
    if not isinstance(records, list):
        raise CheckpointIntegrityError("checkpoint records must be a list")
    if payload.get("completed_games") != len(records):
        raise CheckpointIntegrityError("checkpoint completed count does not match")
    ids = [record.get("game_id") for record in records if isinstance(record, dict)]
    if len(ids) != len(records) or len(set(ids)) != len(ids):
        raise CheckpointIntegrityError("checkpoint contains missing or duplicate game IDs")
    id_set = set(ids)
    authorized = {row["game_id"] for row in schedule}
    if id_set - authorized:
        raise CheckpointIntegrityError("checkpoint contains unauthorized game IDs")
    if ids != [row["game_id"] for row in schedule if row["game_id"] in id_set]:
        raise CheckpointIntegrityError("checkpoint records are out of schedule order")


class WriterLock:
    """Exclusive process-level ownership marker for one checkpoint path."""

    def __init__(self, path: Path, writer_id: str):
        self.path = Path(f"{path}.lock")
        self.writer_id = writer_id
        self._held = False
        self._identity = None
        self.cleanup_failures: list[BaseException] = []

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise CheckpointIntegrityError("checkpoint writer ownership is already held") from exc
        self._held = True
        info = os.fstat(fd)
        self._identity = (info.st_dev, info.st_ino)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(self.writer_id + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def release(self) -> None:
        if self._held:
            info = self.path.lstat()
            if (info.st_dev, info.st_ino) != self._identity or info.st_nlink != 1:
                raise CheckpointIntegrityError("writer ownership marker changed")
            self.path.unlink()
            self._held = False

    def __enter__(self) -> WriterLock:
        self.acquire()
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        try:
            self.release()
            if self._held:
                raise CheckpointIntegrityError("writer release left ownership unresolved")
        except BaseException as cleanup:
            self.cleanup_failures.append(cleanup)
            if _value is None:
                raise
            note_cleanup(_value, cleanup, "LOCK_RELEASE", str(self.path))
