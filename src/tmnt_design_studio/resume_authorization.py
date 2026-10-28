"""Review-only Durable resume contracts. No authority or identity exception is minted here.

The caller must supply a trusted, single-use lease and receipt key independently
of checkpoint files. The live authority/ACL adapter is deliberately not enabled.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tmnt_design_studio.calibration_integrity import CheckpointIntegrityError


class ResumeRefused(CheckpointIntegrityError):
    """No dispatch is permitted after this error."""


def encoded(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ResumeRefused(message)


def strict_json(raw: bytes) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def constant(_value):
        raise ResumeRefused("non-finite JSON value")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def plain_path(path: Path) -> Path:
    """Reject redirected ancestors, including Windows junctions, before resolving."""
    path = path.absolute()
    for part in (path, *path.parents):
        require(not part.is_symlink() and not part.is_junction(), "redirected path")
    if path.exists() and path.is_file():
        require(path.stat().st_nlink == 1, "hardlinked path")
    return path.resolve()


@dataclass(frozen=True)
class RuntimeIdentity:
    """Exact current review payloads, not a claim of historical equivalence."""

    root: Path
    source_files: dict[str, str]
    input_files: dict[str, str]
    executable_sha256: str
    dependency_files: dict[str, str] | None = None
    dependency_origins: dict[str, str] | None = None
    interpreter_files: dict[str, str] | None = None

    def verify(self) -> None:
        require(
            bool(self.dependency_files) and bool(self.dependency_origins),
            "dependency manifest required",
        )
        require(bool(self.interpreter_files), "base interpreter manifest required")
        root = plain_path(self.root)
        require(not self.source_files.keys() & self.input_files.keys(), "overlapping identity maps")
        actual = {
            p.relative_to(root).as_posix() for p in (root / "src/tmnt_design_studio").rglob("*.py")
        }
        require(bool(actual) and actual <= self.source_files.keys(), "unsealed source file")
        for name in (
            "tools/run_bad_guys_initial_calibration.py",
            "tools/baseline005_provenance.py",
            "tools/validate_baseline005_provenance.py",
            "scripts/durable_status_monitor.py",
        ):
            require(not (root / name).exists() or name in self.source_files, "unsealed entrypoint")
        for name, expected in (self.source_files | self.input_files).items():
            path = plain_path(root / name)
            require(path.is_relative_to(root), "identity path escapes root")
            require(file_hash(path) == expected, f"identity mismatch: {name}")
        require(file_hash(Path(sys.executable)) == self.executable_sha256, "interpreter mismatch")
        base = str(Path(sys._base_executable).resolve())
        require(base in self.interpreter_files, "base interpreter is not pinned")
        checked = set()
        for name, expected in self.interpreter_files.items():
            require(file_hash(Path(name)) == expected, "interpreter payload mismatch")
            checked.add(name)
        for name, module in tuple(sys.modules.items()):
            if name == "tmnt_design_studio" or name.startswith("tmnt_design_studio."):
                origin = getattr(module, "__file__", None)
                require(origin is not None, "unresolved runtime import")
                path = plain_path(Path(origin))
                require(path.is_relative_to(root), f"foreign runtime import: {name}")
                relative = path.relative_to(root).as_posix()
                require(relative in self.source_files, f"unsealed import: {name}")
                require(file_hash(path) == self.source_files[relative], "import bytes changed")
            elif name not in ("__main__", "__mp_main__"):
                origin = getattr(module, "__file__", None)
                if not origin:
                    if name.split(".")[0] in sys.stdlib_module_names:
                        continue
                    paths = getattr(module, "__path__", None)
                    require(bool(paths), f"unverifiable dependency module: {name}")
                    actual = "namespace:" + str(sorted(str(Path(p).resolve()) for p in paths or []))
                    require(
                        self.dependency_origins.get(name) == actual, f"dependency origin: {name}"
                    )
                    continue
                path = str(Path(origin).resolve())
                if name.split(".")[0] in sys.stdlib_module_names:
                    require(path in self.interpreter_files, f"unsealed interpreter module: {name}")
                    continue
                require(self.dependency_origins.get(name) == path, f"dependency origin: {name}")
                require(path in self.dependency_files, f"dependency payload missing: {name}")
                spec_origin = getattr(getattr(module, "__spec__", None), "origin", None)
                if spec_origin not in (None, "built-in", "frozen"):
                    require(
                        str(Path(spec_origin).resolve()) == path,
                        f"dependency loader origin: {name}",
                    )
                if path not in checked:
                    require(
                        file_hash(Path(path)) == self.dependency_files[path],
                        f"dependency hash: {name}",
                    )
                    checked.add(path)


@dataclass
class ReviewLease:
    """Trusted test-process input. Never load this or its key from checkpoint/status.

    New processes need a new independently issued lease with the latest pinned
    receipt tip. A hash chain alone cannot authenticate deletion/rollback.
    """

    authorization_id: str
    checkpoint: Path
    reference: Path
    control: Path
    initial_sha256: str
    schedule_sha256: str
    identity: RuntimeIdentity
    receipt_key: bytes = field(repr=False)
    expected_tip: str | None = None
    action: str = "resume-only"
    initial_count: int = 732
    final_count: int = 900
    monitor_protocol: str = "durable-status-v1"
    synthetic_review: bool = True
    telemetry_root: Path | None = None
    telemetry_root_identity: tuple[int, int] | None = None
    used: bool = field(default=False, init=False)

    def claim(self, schedule: list[dict]) -> None:
        require(not self.used, "lease already consumed; renewed authority required")
        self.used = True
        require(self.synthetic_review, "live authority/identity policy is not approved")
        require(self.action == "resume-only", "explicit resume authorization required")
        require(bool(self.authorization_id) and len(self.receipt_key) >= 32, "missing authority")
        require(self.initial_count == 732 and self.final_count == 900, "wrong Durable boundary")
        require(self.monitor_protocol == "durable-status-v1", "unsupported monitor")
        require(len(schedule) == 900, "wrong full schedule size")
        require(sha256(encoded(schedule)) == self.schedule_sha256, "full schedule mismatch")
        require(all(row.get("synthetic_review") is True for row in schedule), "not synthetic")
        paths = [plain_path(p) for p in (self.checkpoint, self.reference, self.control)]
        require(len(set(paths)) == 3, "reference/working/control alias")
        checkpoint, reference, control = paths
        require(not checkpoint.is_relative_to(control), "checkpoint inside control store")
        require(not reference.is_relative_to(control), "reference inside control store")
        require(reference.parent != checkpoint.parent, "reference is not isolated")
        require(reference.is_file() and checkpoint.is_file(), "required checkpoint missing")
        require(file_hash(reference) == self.initial_sha256, "reference mismatch")
        self.identity.verify()

    def policy_digest(self) -> str:
        return sha256(
            encoded(
                {
                    "authorization": self.authorization_id,
                    "checkpoint": str(self.checkpoint.resolve()),
                    "reference": str(self.reference.resolve()),
                    "control": str(self.control.resolve()),
                    "source_root": str(self.identity.root.resolve()),
                    "monitor_protocol": self.monitor_protocol,
                    "initial": self.initial_sha256,
                    "schedule": self.schedule_sha256,
                    "source": self.identity.source_files,
                    "inputs": self.identity.input_files,
                    "interpreter": self.identity.executable_sha256,
                    "dependency_files": self.identity.dependency_files,
                    "dependency_origins": self.identity.dependency_origins,
                    "interpreter_files": self.identity.interpreter_files,
                    "telemetry_root": str(self.telemetry_root),
                    "telemetry_root_identity": self.telemetry_root_identity,
                }
            )
        )

    def validate_outputs(self, status: Path):
        from tmnt_design_studio.resume_paths import TelemetryGrant, disjoint

        require(
            self.telemetry_root is not None and self.telemetry_root_identity is not None,
            "separately authorized telemetry root required",
        )
        reference = plain_path(self.reference)
        checkpoint = plain_path(self.checkpoint)
        control = plain_path(self.control)
        roles = (reference.parent, checkpoint.parent, control)
        for index, left in enumerate(roles):
            for right in roles[index + 1 :]:
                require(disjoint(left, right), "unsafe output/reference directory overlap")
        protected = (*roles, plain_path(self.identity.root))
        # No writer or receipt artifact may be placed in the source/input tree.
        for output in (checkpoint, control):
            require(
                disjoint(output, plain_path(self.identity.root)), "output overlaps source identity"
            )
        grant = TelemetryGrant(
            self.telemetry_root, self.telemetry_root_identity, protected, self.authorization_id
        )
        grant.validate(status)
        return grant


class Receipts:
    """Exclusive append-only HMAC receipts; any partial transaction blocks entry."""

    def __init__(self, lease: ReviewLease):
        self.lease = lease
        self.events: list[dict] = []
        self.tip = lease.policy_digest()
        if lease.control.exists():
            names = sorted(lease.control.iterdir())
            require(bool(names), "empty existing control store")
            for index, path in enumerate(names):
                plain_path(path)
                require(path.name == f"{index:06d}.json", "missing/conflicting receipt")
                event = strict_json(path.read_bytes())
                require(isinstance(event, dict) and "mac" in event, "invalid receipt")
                mac = event.pop("mac")
                require(isinstance(mac, str), "invalid receipt MAC")
                require(hmac.compare_digest(self.sign(event), mac), "forged continuation receipt")
                require(event.get("parent") == self.tip, "receipt predecessor mismatch")
                require(event.get("policy") == lease.policy_digest(), "receipt policy mismatch")
                self.tip = sha256(encoded({**event, "mac": mac}))
                self.events.append(event)
            require(lease.expected_tip == self.tip, "stale/missing trusted receipt head")
            require(self.events[-1]["phase"] == "commit", "ambiguous interrupted transaction")
        else:
            require(lease.expected_tip is None, "missing continuation store")

    def sign(self, event: dict) -> str:
        return hmac.new(self.lease.receipt_key, encoded(event), hashlib.sha256).hexdigest()

    def append(self, phase: str, **fields: Any) -> None:
        require(self.lease.telemetry_root is not None, "telemetry root required")
        self.lease.validate_outputs(self.lease.telemetry_root / "durable-status.json")
        event = dict(phase=phase, parent=self.tip, policy=self.lease.policy_digest(), **fields)
        signed = {**event, "mac": self.sign(event)}
        self.lease.control.mkdir(exist_ok=True)
        path = self.lease.control / f"{len(self.events):06d}.json"
        # Exclusive creation, never replace or repair existing receipt evidence.
        with path.open("xb") as handle:
            handle.write(encoded(signed))
            handle.flush()
            os.fsync(handle.fileno())
        self.tip = sha256(encoded(signed))
        self.events.append(event)

    def restore(self, schedule: list[dict]) -> dict:
        lease = self.lease
        expected_hash, expected_count = lease.initial_sha256, lease.initial_count
        reference_raw = lease.reference.read_bytes()
        require(sha256(reference_raw) == lease.initial_sha256, "reference changed")
        reference = strict_json(reference_raw)
        original = reference["records"]
        self.validate(reference, schedule, lease.initial_count)
        # Validate every event, not just the final receipt.
        for index in range(0, len(self.events), 3):
            group = self.events[index : index + 3]
            require([e["phase"] for e in group] == ["start", "prepare", "commit"], "receipt phases")
            start, prepare, commit = group
            require(start["checkpoint_sha256"] == expected_hash, "stale predecessor")
            require(start["count"] == expected_count, "receipt count")
            require(start["game_id"] == schedule[expected_count]["game_id"], "receipt game ID")
            require(
                prepare["count"] == commit["count"] == expected_count + 1, "receipt progression"
            )
            require(prepare["checkpoint_sha256"] == commit["checkpoint_sha256"], "receipt conflict")
            expected_hash, expected_count = commit["checkpoint_sha256"], commit["count"]
        raw = lease.checkpoint.read_bytes()
        require(sha256(raw) == expected_hash, "working checkpoint hash mismatch")
        payload = strict_json(raw)
        self.validate(payload, schedule, expected_count)
        require(encoded(payload["records"][:732]) == encoded(original), "original records changed")
        for index, event in enumerate(self.events[2::3], start=732):
            require(
                sha256(encoded(payload["records"][index])) == event["record_sha256"],
                "record changed",
            )
        return payload

    def validate(self, payload: dict, schedule: list[dict], count: int) -> None:
        require(isinstance(payload, dict), "checkpoint object required")
        require(type(payload.get("completed_games")) is int, "invalid count type")
        require(payload["completed_games"] == count, "completed count mismatch")
        require(payload.get("schedule_games") == 900, "schedule size mismatch")
        require(payload.get("schedule_digest") == self.lease.schedule_sha256, "schedule digest")
        records = payload.get("records")
        require(isinstance(records, list) and len(records) == count, "invalid records")
        require(732 <= count <= 900, "unauthorized progress")
        require(all(isinstance(record, dict) for record in records), "invalid record")
        ids = [record.get("game_id") for record in records]
        require(ids == [row["game_id"] for row in schedule[:count]], "not exact schedule prefix")
        require(all(isinstance(i, str) for i in ids) and len(set(ids)) == count, "duplicate IDs")
