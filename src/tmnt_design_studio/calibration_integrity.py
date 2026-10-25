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
from pathlib import Path
from typing import Any

_MAX_CHECKPOINT_LINE_BYTES = 8 * 1024 * 1024
_MAX_CHECKPOINT_RECORD_BYTES = 64 * 1024 * 1024


class CheckpointIntegrityError(ValueError):
    """Raised when a schedule, result set, writer, or checkpoint is invalid."""


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

    def restore_stream(self, path: Path) -> None:
        """Restore the writer's canonical JSON format one record at a time.

        The schema emitted by ``write`` has a stable four-field envelope and
        pretty-printed record boundaries. Parsing one record at a time avoids
        retaining a second, whole-file Unicode string alongside the decoded
        event trees. Any deviation from that canonical envelope fails closed.
        """
        path = Path(path)
        expected_order = {game_id: index for index, game_id in enumerate(self._expected)}
        restored: dict[str, dict[str, Any]] = {}
        last_index = -1

        def read_line(handle) -> bytes:
            line = handle.readline(_MAX_CHECKPOINT_LINE_BYTES + 1)
            if len(line) > _MAX_CHECKPOINT_LINE_BYTES:
                raise CheckpointIntegrityError("checkpoint line exceeds the streaming limit")
            if line and not line.endswith(b"\n"):
                raise CheckpointIntegrityError("checkpoint line is truncated or too long")
            return line

        def field_value(handle, name: str, *, comma: bool) -> Any:
            line = read_line(handle)
            prefix = f'  "{name}": '.encode("ascii")
            suffix = b",\n" if comma else b"\n"
            if not line.startswith(prefix) or not line.endswith(suffix):
                raise CheckpointIntegrityError(f"checkpoint {name} field is malformed")
            raw = line[len(prefix) : -len(suffix)]
            try:
                return json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CheckpointIntegrityError(f"checkpoint {name} field is invalid JSON") from exc

        try:
            with path.open("rb", buffering=1024 * 1024) as handle:
                if read_line(handle) != b"{\n":
                    raise CheckpointIntegrityError("checkpoint root object is malformed")
                completed = field_value(handle, "completed_games", comma=True)
                if type(completed) is not int or not 0 <= completed <= len(self._schedule):
                    raise CheckpointIntegrityError("checkpoint completed count is invalid")

                records_header = read_line(handle)
                if records_header == b'  "records": [],\n':
                    record_count = 0
                elif records_header == b'  "records": [\n':
                    record_count = 0
                    while True:
                        boundary = read_line(handle)
                        if boundary == b"  ],\n":
                            break
                        if boundary != b"    {\n":
                            raise CheckpointIntegrityError(
                                "checkpoint record boundary is malformed"
                            )
                        record_bytes = bytearray(boundary)
                        while True:
                            part = read_line(handle)
                            if not part:
                                raise CheckpointIntegrityError("checkpoint record is truncated")
                            if part in (b"    },\n", b"    }\n"):
                                break
                            record_bytes.extend(part)
                            if len(record_bytes) > _MAX_CHECKPOINT_RECORD_BYTES:
                                raise CheckpointIntegrityError(
                                    "checkpoint record exceeds the streaming limit"
                                )
                        if part == b"    },\n":
                            record_bytes.extend(b"    }\n")
                        else:
                            record_bytes.extend(part)
                        try:
                            record = json.loads(record_bytes)
                        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                            raise CheckpointIntegrityError(
                                f"checkpoint record {record_count} is invalid JSON"
                            ) from exc
                        if not isinstance(record, dict):
                            raise CheckpointIntegrityError(
                                f"checkpoint record {record_count} is not an object"
                            )
                        game_id = record.get("game_id")
                        if not isinstance(game_id, str) or game_id not in expected_order:
                            raise CheckpointIntegrityError(
                                f"checkpoint contains an unauthorized game ID: {game_id!r}"
                            )
                        if game_id in restored:
                            raise CheckpointIntegrityError(
                                f"checkpoint contains a duplicate game ID: {game_id}"
                            )
                        index = expected_order[game_id]
                        if index <= last_index:
                            raise CheckpointIntegrityError(
                                "checkpoint records are out of schedule order"
                            )
                        last_index = index
                        restored[game_id] = record
                        record_count += 1
                        if record_count > len(self._schedule):
                            raise CheckpointIntegrityError(
                                "checkpoint has more records than the schedule"
                            )
                else:
                    raise CheckpointIntegrityError("checkpoint records array is malformed")

                if field_value(handle, "schedule_digest", comma=True) != self._schedule_digest:
                    raise CheckpointIntegrityError("checkpoint schedule identity does not match")
                schedule_games = field_value(handle, "schedule_games", comma=False)
                if type(schedule_games) is not int or schedule_games != len(self._schedule):
                    raise CheckpointIntegrityError("checkpoint schedule count does not match")
                if read_line(handle) != b"}\n" or handle.read(1):
                    raise CheckpointIntegrityError("checkpoint has malformed or trailing data")
                if completed != record_count:
                    raise CheckpointIntegrityError(
                        "checkpoint completed count does not match its records"
                    )
        except OSError as exc:
            raise CheckpointIntegrityError(f"unable to read checkpoint: {exc}") from exc

        if self._records.keys() & restored.keys():
            raise CheckpointIntegrityError("checkpoint duplicates an already restored game ID")
        self._records.update(restored)

    @property
    def completed_ids(self) -> set[str]:
        return set(self._records)

    def assert_complete(self) -> None:
        if set(self._records) != set(self._expected):
            missing = sorted(set(self._expected) - set(self._records))
            raise CheckpointIntegrityError(
                f"checkpoint is incomplete; missing {len(missing)} games"
            )

    def write(self, path: Path, *, writer_id: str, return_snapshot: bool = True) -> dict[str, Any]:
        self.claim(writer_id)
        records = [self._records[game_id] for game_id in self._expected if game_id in self._records]
        payload = {
            "schedule_digest": self._schedule_digest,
            "schedule_games": len(self._schedule),
            "completed_games": len(records),
            "records": records,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, sort_keys=True, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            _replace_with_retry(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        if return_snapshot:
            return self.snapshot()
        return {key: value for key, value in payload.items() if key != "records"}


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
