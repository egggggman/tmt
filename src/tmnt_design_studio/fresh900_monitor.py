"""Read-only, status-only observer. Never starts or supervises a child process."""

from __future__ import annotations

import json
import os
import stat
import time
from dataclasses import dataclass
from pathlib import Path

from tmnt_design_studio.fresh900 import PROTOCOL
from tmnt_design_studio.fresh900_identity import FreshRefused, disjoint, plain, require


@dataclass(frozen=True)
class MonitorLocation:
    root: Path
    identity: tuple[int, int]
    run_id: str
    protected: tuple[Path, ...]

    def validate(self) -> Path:
        root = plain(self.root)
        info = root.stat()
        require(stat.S_ISDIR(info.st_mode), "telemetry directory required")
        require((info.st_dev, info.st_ino) == self.identity, "telemetry root replaced")
        require(root.name == "telemetry", "separate telemetry role required")
        require(root.parent.name == self.run_id, "wrong telemetry run")
        require(bool(self.protected), "protected checkpoint role required")
        checkpoint_directory = root.parent / "checkpoints"
        require(checkpoint_directory in self.protected, "checkpoint role not protected")
        for protected in self.protected:
            require(disjoint(root, plain(protected)), "telemetry/protected overlap")
        return root / "status.json"


def read_status(location: MonitorLocation, *, max_age: float = 10) -> dict:
    """Small synchronous read; a blocked OS read has no hard deadline guarantee.

    An external observer is operational only, not a writer dependency. No caller
    can supply a checkpoint leaf path; file-role/link checks precede opening.
    """
    try:
        require(0 < max_age <= 60, "invalid freshness")
        path = plain(location.validate())
        before = path.stat()
        require(stat.S_ISREG(before.st_mode) and before.st_size <= 4096, "invalid status file")
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            require(
                (opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino),
                "status changed before open",
            )
            require(opened.st_nlink == 1, "aliased status file")
            payload = json.loads(stream.read(4097))
        location.validate()
        require(isinstance(payload, dict), "invalid status object")
        require(payload.get("protocol") == PROTOCOL, "unsupported monitor/status version")
        require(payload.get("run_id") == location.run_id, "foreign status")
        require(payload.get("synthetic") is True, "only synthetic status supported")
        require(payload.get("state") in ("RUNNING", "COMPLETE"), "invalid status state")
        require(
            type(payload.get("committed_games")) is int and 0 <= payload["committed_games"] <= 900,
            "invalid count",
        )
        stamp = payload.get("heartbeat")
        require(
            type(stamp) in (int, float) and 0 <= time.time() - stamp <= max_age,
            "stale or future telemetry",
        )
        return {**payload, "state": "REPORTED_ONLY"}
    except (OSError, ValueError, TypeError, KeyError, FreshRefused):
        return {"state": "UNKNOWN"}
