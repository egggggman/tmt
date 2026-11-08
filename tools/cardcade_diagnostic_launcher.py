"""One-shot Acceptance Match #001 diagnostic launcher.

The CLI is intentionally fixed to the committed April-vs-Casey canonical seed. Tests may
inject an executor, but the command-line entry point never exposes that seam.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import traceback
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tmnt_design_studio import stage002

SUPPORTED_SOURCE_BASE = "6612ba7ee36d7eeeb2b090a3a7664662d6fcdeac"
ACCEPTED_MAIN = "10d2ac80ef5b81b3a209a3133eb0a84633a1f944"
EXPECTED_GAME_ID = "april-casey:canonical:7231"
EXPECTED_PAIRING_ID = "april-casey"
EXPECTED_ORIENTATION = "canonical"
EXPECTED_SEED = 7231
INPUT_PATHS = (
    "src/tmnt_design_studio/stage002.py",
    "decks/april_oneil/PROTOTYPE_0.1.txt",
    "decks/casey_jones/PROTOTYPE_0.1.txt",
    "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
    "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json",
)
TRACE_EVENTS = {
    "priority_granted",
    "priority_passed",
    "priority_window_closed",
    "stack_resolution_permitted",
    "trigger_stacked",
    "trigger_resolved",
    "attack_declared",
    "attackers_declared",
    "block_declared",
    "blockers_declared",
    "sneak",
    "combat_damage",
    "step_changed",
}


class DiagnosticLauncherError(RuntimeError):
    """Raised when launcher preflight or evidence validation cannot complete."""


class EvidencePersistenceError(DiagnosticLauncherError):
    """Raised when a successful synthetic/real invocation cannot be fully persisted."""


class OneShotDiagnosticLauncher:
    """Run one exact committed match and persist its evidence into a new directory."""

    def __init__(self, root: Path, output_directory: Path) -> None:
        self.root = root.resolve()
        self.output_directory = output_directory.resolve()
        self._consumed = False
        self._run_game_call_count = 0
        self._storage_error: str | None = None

    @staticmethod
    def _git(root: Path, *args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()

    def _verify_source(self) -> dict[str, str]:
        head = self._git(self.root, "rev-parse", "HEAD")
        branch = self._git(self.root, "branch", "--show-current") or "(detached HEAD)"
        status = self._git(self.root, "status", "--porcelain=v1")
        main = self._git(self.root, "rev-parse", "refs/remotes/origin/main")
        if status:
            raise DiagnosticLauncherError(f"launcher worktree is not clean: {status}")
        if main != ACCEPTED_MAIN:
            raise DiagnosticLauncherError(f"accepted main changed: {main}")
        try:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.root),
                    "merge-base",
                    "--is-ancestor",
                    SUPPORTED_SOURCE_BASE,
                    head,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as error:
            raise DiagnosticLauncherError(
                f"source HEAD {head} does not descend from accepted capture base"
            ) from error
        return {"head": head, "branch": branch, "accepted_main": main}

    def _match_spec(self) -> stage002.GameSpec:
        matches = [game for game in stage002.stage_games() if game.game_id == EXPECTED_GAME_ID]
        if len(matches) != 1:
            raise DiagnosticLauncherError(
                f"expected exactly one committed spec for {EXPECTED_GAME_ID}, found {len(matches)}"
            )
        spec = matches[0]
        if (
            spec.pairing_id != EXPECTED_PAIRING_ID
            or spec.orientation != EXPECTED_ORIENTATION
            or spec.seed != EXPECTED_SEED
            or tuple(seat.display_id for seat in spec.seats)
            != ("april-oneil-p0.1", "casey-jones-p0.1")
        ):
            raise DiagnosticLauncherError("committed Acceptance Match #001 spec changed")
        return spec

    def _prepare_output(self) -> None:
        allowed_root = (self.root / ".cardcade-diagnostic-runs").resolve()
        try:
            self.output_directory.relative_to(allowed_root)
        except ValueError as error:
            raise DiagnosticLauncherError(
                "output directory must be inside .cardcade-diagnostic-runs"
            ) from error
        if self.output_directory == allowed_root:
            raise DiagnosticLauncherError("output directory must be a new child directory")
        if not self.output_directory.name.startswith("diagnostic-game-"):
            raise DiagnosticLauncherError("output directory must start with diagnostic-game-")
        self.output_directory.mkdir(parents=True, exist_ok=False)
        probe = self.output_directory / ".write-probe"
        try:
            with probe.open("xb") as stream:
                stream.write(b"diagnostic evidence preflight\n")
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            if probe.exists():
                probe.unlink()

    @staticmethod
    def _write_json(directory: Path, filename: str, value: object) -> None:
        destination = directory / filename
        temporary = directory / f".{filename}.tmp"
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _persist_hashes(self) -> dict[str, str]:
        hashes = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(self.output_directory.iterdir())
            if path.is_file() and path.name != "artifact_sha256.json"
        }
        self._write_json(self.output_directory, "artifact_sha256.json", hashes)
        return hashes

    @staticmethod
    def _safe_error(error: BaseException) -> dict[str, str]:
        try:
            message = str(error)
        except BaseException as formatting_error:
            message = f"<message unavailable: {type(formatting_error).__name__}>"
        try:
            rendered = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        except BaseException as formatting_error:
            rendered = f"<traceback unavailable: {type(formatting_error).__name__}>"
        return {"type": type(error).__name__, "message": message, "traceback": rendered}

    def _serialize_snapshot(
        self,
        snapshot: dict[str, Any],
        spec: stage002.GameSpec,
        manifest: dict[str, object],
    ) -> tuple[dict[str, object] | None, dict[str, object] | None]:
        self._write_json(self.output_directory, "snapshot.json", snapshot)
        events = snapshot.get("events", [])
        if not isinstance(events, list):
            raise DiagnosticLauncherError("snapshot event stream is not a list")
        self._write_json(self.output_directory, "events.json", events)
        self._write_json(
            self.output_directory,
            "priority_stack_combat_trace.json",
            [event for event in events if event.get("event") in TRACE_EVENTS],
        )
        try:
            reconciliation = stage002.reconcile_snapshot(spec, snapshot, manifest)
        except BaseException as error:
            return None, self._safe_error(error)
        self._write_json(self.output_directory, "reconciliation.json", reconciliation)
        return reconciliation, None

    def run_once(
        self,
        executor: Callable[..., dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Run the fixed match once. `executor` is a synthetic-test injection seam only."""
        if self._consumed:
            raise DiagnosticLauncherError("this launcher instance has already been consumed")
        self._consumed = True
        spec = self._match_spec()
        source = self._verify_source()
        self._prepare_output()
        manifest = stage002.build_stage_manifest(self.root)
        input_hashes = {
            relative: hashlib.sha256((self.root / relative).read_bytes()).hexdigest()
            for relative in INPUT_PATHS
        }
        metadata: dict[str, object] = {
            "run_id": "cardcade-diagnostic-launcher-once",
            "authorized_source_base": SUPPORTED_SOURCE_BASE,
            "observed_head": source["head"],
            "accepted_main": source["accepted_main"],
            "branch": source["branch"],
            "worktree": str(self.root),
            "output_directory": str(self.output_directory),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
            "game_id": spec.game_id,
            "pairing_id": spec.pairing_id,
            "orientation": spec.orientation,
            "seed": spec.seed,
            "seats": [
                {"display_id": seat.display_id, "deck_path": seat.relative_path}
                for seat in spec.seats
            ],
            "stage_manifest_digest": manifest["manifest_digest"],
            "input_sha256": input_hashes,
            "invocation": "stage002.run_game(root, committed_spec, AcceptancePilot())",
            "run_game_call_count": 0,
            "retry_count": 0,
            "additional_seeds": 0,
            "batch_or_calibration": False,
            "runner_control_flow": (
                "one launcher instance; one executor call; run_game constructs one Game; "
                "no outer pairing loop, retry, or seed expansion"
            ),
            "started_utc": datetime.now(UTC).isoformat(),
        }
        self._write_json(self.output_directory, "stage_manifest.json", manifest)
        self._write_json(self.output_directory, "run_metadata.json", metadata)
        capture = stage002.DiagnosticExecutionCapture()
        invoke = executor or stage002.run_game

        def call_once() -> dict[str, Any]:
            if self._run_game_call_count:
                raise DiagnosticLauncherError("executor call limit exceeded")
            self._run_game_call_count += 1
            return invoke(self.root, spec, diagnostic_capture=capture)

        try:
            snapshot = stage002.capture_diagnostic_call(capture, call_once)
        except BaseException as original_error:
            metadata["run_game_call_count"] = self._run_game_call_count
            metadata["finished_utc"] = datetime.now(UTC).isoformat()
            failure = capture.failure or self._safe_error(original_error)
            failure_without_snapshot = {
                key: value for key, value in failure.items() if key != "snapshot"
            }
            persist_error: BaseException | None = None
            try:
                self._write_json(self.output_directory, "exception.json", failure_without_snapshot)
                captured_snapshot = failure.get("snapshot")
                if isinstance(captured_snapshot, dict):
                    _reconciliation, reconciliation_error = self._serialize_snapshot(
                        captured_snapshot, spec, manifest
                    )
                    if reconciliation_error is not None:
                        self._write_json(
                            self.output_directory,
                            "reconciliation_error.json",
                            reconciliation_error,
                        )
                self._write_json(self.output_directory, "run_metadata.json", metadata)
                status = {
                    "run_returned_normally": False,
                    "reconciliation_completed": (
                        self.output_directory / "reconciliation.json"
                    ).exists(),
                    "run_game_call_count": self._run_game_call_count,
                    "retry_count": 0,
                    "snapshot_captured": isinstance(captured_snapshot, dict),
                    "winner": captured_snapshot.get("winner")
                    if isinstance(captured_snapshot, dict)
                    else None,
                    "terminal": captured_snapshot.get("terminal")
                    if isinstance(captured_snapshot, dict)
                    else None,
                }
                self._write_json(self.output_directory, "run_status.json", status)
                self._persist_hashes()
            except BaseException as error:
                persist_error = error
                self._storage_error = self._safe_error(error)["message"]
            if persist_error is not None and hasattr(original_error, "add_note"):
                original_error.add_note(
                    f"diagnostic evidence persistence failed: {self._storage_error}"
                )
            raise

        metadata["run_game_call_count"] = self._run_game_call_count
        metadata["finished_utc"] = datetime.now(UTC).isoformat()
        try:
            self._write_json(self.output_directory, "run_metadata.json", metadata)
            reconciliation, reconciliation_error = self._serialize_snapshot(
                snapshot, spec, manifest
            )
            if reconciliation_error is not None:
                self._write_json(
                    self.output_directory, "reconciliation_error.json", reconciliation_error
                )
            events = snapshot.get("events", [])
            counts = Counter(str(event.get("event")) for event in events)
            status = {
                "run_returned_normally": True,
                "reconciliation_completed": reconciliation is not None,
                "winner": snapshot.get("winner"),
                "terminal": snapshot.get("terminal"),
                "turn": snapshot.get("turn"),
                "step": snapshot.get("step"),
                "event_count": len(events),
                "event_counts": dict(sorted(counts.items())),
                "run_game_call_count": self._run_game_call_count,
                "retry_count": 0,
                "invariant_violation_count": counts.get("invariant_violation", 0),
                "acceptance_incomplete_count": counts.get("acceptance_incomplete", 0),
                "reconciliation_stop_records": reconciliation.get("stop_records", [])
                if reconciliation is not None
                else None,
            }
            self._write_json(self.output_directory, "run_status.json", status)
            self._persist_hashes()
        except BaseException as error:
            self._storage_error = self._safe_error(error)["message"]
            raise EvidencePersistenceError(
                "executor completed once, but complete diagnostic evidence could not be persisted; "
                "do not retry this launcher"
            ) from error
        return snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-directory",
        type=Path,
        help="new isolated directory; defaults to .cardcade-diagnostic-runs/<UTC run id>",
    )
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    run_id = datetime.now(UTC).strftime("diagnostic-game-%Y%m%dT%H%M%SZ")
    output = args.output_directory or root / ".cardcade-diagnostic-runs" / run_id
    launcher = OneShotDiagnosticLauncher(root, output)
    try:
        launcher.run_once()
    except BaseException as error:
        print(f"diagnostic launcher stopped: {error}", file=sys.stderr)
        print(f"evidence directory: {output}", file=sys.stderr)
        return 2
    print(f"diagnostic evidence: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
