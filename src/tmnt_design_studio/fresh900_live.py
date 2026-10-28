"""Explicitly authorized library adapter; no CLI, defaults, resume or launch issuer."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import types
from functools import lru_cache
from pathlib import Path

from tmnt_design_studio import fresh900 as persistence
from tmnt_design_studio.calibration_integrity import note_cleanup
from tmnt_design_studio.fresh900_identity import digest, encoded, file_hash, plain, require
from tmnt_design_studio.fresh900_native import validate_native, validate_reconciliation

VERSION = "fresh900-live-adapter-v1"
FROZEN_SOURCE = "fd28f68915c4e7cb6af3444bf41b96608dee712c"


class AdapterGameFailure(RuntimeError):
    """Retain the frozen exception as cause and its complete partial snapshot."""

    def __init__(self, error: Exception):
        super().__init__(str(error))
        self.original_error_type = type(error).__name__
        self.partial_snapshot = None
        self.snapshot_capture_state = "UNAVAILABLE"
        try:
            self.capture(getattr(error, "snapshot", None))
        except BaseException as cleanup:
            note_cleanup(self, cleanup, "SNAPSHOT_ACCESS", "gameplay exception snapshot")

    def capture(self, snapshot):
        if snapshot is None:
            return
        # Establish the primary exception and a reference before allocating a copy.
        self.partial_snapshot = snapshot
        self.snapshot_capture_state = "REFERENCE_ONLY_COPY_FAILED"
        try:
            self.partial_snapshot = copy.deepcopy(snapshot)
            self.snapshot_capture_state = "COPIED"
        except BaseException as cleanup:
            note_cleanup(self, cleanup, "SNAPSHOT_COPY", "partial native snapshot")


def authenticate_source(plan: dict) -> None:
    """The approved runtime is an integration head; gameplay must still equal fd28."""
    root = plain(Path(plan["runtime"]["source"]))
    git = plan["runtime"]["git_executable"]
    changed = subprocess.check_output(
        [
            git,
            "-c",
            f"safe.directory={root.as_posix()}",
            "-C",
            str(root),
            "diff",
            "--name-only",
            FROZEN_SOURCE,
            plan["runtime"]["source_commit"],
            "--",
            "src",
            "tools",
        ],
        text=True,
    ).splitlines()
    allowed = {
        "src/tmnt_design_studio/calibration_integrity.py",
        "src/tmnt_design_studio/fresh900.py",
        "src/tmnt_design_studio/fresh900_identity.py",
        "src/tmnt_design_studio/fresh900_monitor.py",
        "src/tmnt_design_studio/fresh900_live.py",
        "src/tmnt_design_studio/fresh900_native.py",
        "tools/preflight_fresh900.py",
        "tools/profile_fresh900_synthetic.py",
    }
    require(set(changed) <= allowed, "frozen gameplay source differs")
    committed_adapter = subprocess.check_output(
        [
            git,
            "-c",
            f"safe.directory={root.as_posix()}",
            "-C",
            str(root),
            "show",
            f"{plan['runtime']['source_commit']}:src/tmnt_design_studio/fresh900_live.py",
        ]
    )
    require(
        hashlib.sha256(committed_adapter).hexdigest()
        == file_hash(root / "src/tmnt_design_studio/fresh900_live.py"),
        "adapter differs from approved commit",
    )
    require(
        plan["adapter"]
        == {
            "version": VERSION,
            "frozen_source": FROZEN_SOURCE,
            "source_sha256": file_hash(root / "src/tmnt_design_studio/fresh900_live.py"),
        },
        "adapter identity mismatch",
    )


def bindings():
    """Imports do not instantiate a game. Tests replace this entire boundary."""
    from tmnt_design_studio import smoke01, stage002
    from tools.run_bad_guys_initial_calibration import _candidate_text

    return smoke01, stage002, _candidate_text


@lru_cache(maxsize=8)
def _executor_code(root: str, git: str, filename: str, optimize: int):
    source = subprocess.check_output(
        [
            git,
            "-c",
            f"safe.directory={Path(root).as_posix()}",
            "-C",
            root,
            "show",
            f"{FROZEN_SOURCE}:src/tmnt_design_studio/smoke01.py",
        ]
    )
    # Compile only. Executing module/game code is neither necessary nor allowed
    # for this identity check. Python is pinned by the enclosing runtime gate.
    module = compile(source, filename, "exec", dont_inherit=True, optimize=optimize)
    codes = [
        c
        for c in module.co_consts
        if isinstance(c, types.CodeType) and c.co_name == "run_smoke_game"
    ]
    require(len(codes) == 1, "ambiguous frozen gameplay entrypoint")
    return codes[0]


def _bind_executor(smoke, root: Path, git: str):
    path = plain(root / "src/tmnt_design_studio/smoke01.py")
    require(plain(Path(smoke.__file__)) == path, "wrong frozen executor module")
    function = smoke.run_smoke_game
    require(type(function) is types.FunctionType, "substituted gameplay callable")
    require(
        function.__module__ == "tmnt_design_studio.smoke01"
        and function.__name__ == function.__qualname__ == "run_smoke_game"
        and function.__globals__ is vars(smoke)
        and function.__defaults__ == (None,)
        and function.__kwdefaults__ is None
        and function.__closure__ is None,
        "wrapped or altered gameplay callable",
    )
    require(plain(Path(function.__code__.co_filename)) == path, "foreign executor code origin")
    expected = _executor_code(str(root), git, function.__code__.co_filename, sys.flags.optimize)
    require(function.__code__ == expected, "gameplay callable differs from frozen implementation")
    return function


def game_spec(stage, row: dict, candidate: Path, opponent_path: str):
    """Exact mapping used by the frozen launcher; no game construction here."""
    seats = (
        stage.DeckSpec("bad_guys_cronies_sandbox_0_2", str(candidate)),
        stage.DeckSpec(row["opponent"], opponent_path),
    )
    if row["orientation"] == "opponent_first":
        seats = tuple(reversed(seats))
    require([seat.display_id for seat in seats] == row["seats"], "spec seat identity mismatch")
    return stage.GameSpec(row["game_id"], row["pairing_id"], row["seed"], row["orientation"], seats)


def run_authorized_live(
    plan: dict, authorization: dict, *, expected_authorization_sha256: str
) -> dict:
    """Future live API: caller must supply an independently trusted approval pin.

    This is not an authorization issuer. The pin must not originate in the plan,
    checkpoint or CLI. No actual call is authorized by implementation approval.
    Tests mock the frozen gameplay function; there is no executor CLI argument.
    """
    plan, authorization = copy.deepcopy(plan), copy.deepcopy(authorization)
    require(digest(authorization) == expected_authorization_sha256, "execution approval mismatch")
    require(authorization.get("action") == "fresh900-live-execution", "live authority required")
    require(authorization.get("plan_sha256") == digest(plan), "execution plan mismatch")
    require(authorization.get("approved_by"), "external execution issuer required")
    for gate in ("independent_review_sha256", "design_approval_sha256", "preflight_sha256"):
        require(
            bool(re.fullmatch(r"[0-9a-f]{64}", authorization.get(gate, ""))),
            f"missing approved gate: {gate}",
        )
    require(sys.version_info[:3] == (3, 13, 15), "Python 3.13.15 required")
    authenticate_source(plan)
    smoke, stage, candidate_text = bindings()
    root = plain(Path(plan["runtime"]["source"]))
    # Authenticate actual imports, inputs and the entire schedule BEFORE reserving
    # output. _run_fresh repeats this and the resource checks before each dispatch.
    persistence.verify_plan(plan)
    for module in (smoke, stage):
        require(
            plain(Path(module.__file__)).is_relative_to(root / "src"),
            "gameplay import outside frozen source",
        )
    executor = _bind_executor(smoke, root, plan["runtime"]["git_executable"])
    candidate = Path(plan["output"]) / "inputs/bad_guys_0_2.txt"
    candidate_bytes = candidate_text(root).encode("utf-8")
    manifest = None

    def execute(row):
        nonlocal manifest
        # Reservation, lock, runtime/input/resource gates have already succeeded.
        path = plain(candidate)
        require(
            path.is_relative_to(plain(Path(plan["output"]) / "inputs")),
            "candidate path escaped input role",
        )
        if not path.exists():
            with path.open("xb") as stream:
                stream.write(candidate_bytes)
                stream.flush()
                os.fsync(stream.fileno())
        require(path.read_bytes() == candidate_bytes, "derived candidate changed")
        deck_manifest = json.loads(
            (
                root / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
            ).read_bytes()
        )
        opponent = next(d for d in deck_manifest["decks"] if d["deck_key"] == row["opponent"])
        candidate_spec = stage.DeckSpec("bad_guys_cronies_sandbox_0_2", str(path))
        opponent_spec = stage.DeckSpec(row["opponent"], opponent["source_path"])
        spec = game_spec(stage, row, path, opponent_spec.relative_path)
        try:
            if manifest is None:
                catalog = stage.load_catalog(root)
                # Read-only evidence preparation, not gameplay execution.
                all_decks = [
                    candidate_spec,
                    *[
                        stage.DeckSpec(d["deck_key"], d["source_path"])
                        for d in deck_manifest["decks"]
                        if d["deck_key"] != "bebop_rocksteady"
                    ],
                ]
                manifest = {
                    "decks": [stage.build_deck_manifest(root, d, catalog) for d in all_decks]
                }
            require(
                _bind_executor(smoke, root, plan["runtime"]["git_executable"]) is executor,
                "gameplay callable changed after binding",
            )
            raw = executor(root, spec)
            require(isinstance(raw, dict), "game snapshot object required")
            validate_native(raw, spec)
            native_digest = digest(raw)
            report = stage.reconcile_snapshot(spec, raw, manifest)
            require(digest(raw) == native_digest, "reconciler modified native snapshot")
            validate_reconciliation(raw, spec, report)
            result = copy.deepcopy(raw)
            derived = dict(
                game_id=row["game_id"],
                synthetic=False,
                stop_records=report["stop_records"],
                invariant_violations=report["invariant_violations"],
            )
            for key, value in derived.items():
                if key in result:
                    require(encoded(result[key]) == encoded(value), f"conflicting native {key}")
                else:
                    result[key] = value
            require("adapter_reconciliation" not in result, "reserved adapter evidence field")
            result["adapter_reconciliation"] = report
            # Original native fields remain unchanged; common accepted validation
            # checks terminal/winner/turn, all redundant identity and full evidence.
            return result
        except Exception as error:
            # SmokeGameFailure is a frozen dataclass. Wrap it rather than mutating
            # it during shared cleanup/reporting; retain original cause and bytes.
            wrapped = AdapterGameFailure(error)
            if wrapped.partial_snapshot is None and "raw" in locals():
                wrapped.capture(raw)
            raise wrapped from error

    return persistence._run_fresh(
        plan,
        authorization,
        expected_authorization_sha256=expected_authorization_sha256,
        executor=execute,
        measure=persistence.resources,
        synthetic=False,
    )
