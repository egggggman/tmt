"""Read-only integrity checks for the preserved 300-game schedule package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_REPO_ROOT = r"C:\projects\tmt"
EXPECTED_ORIGIN = "https://github.com/egggggman/tmt.git"
EXPECTED_SCHEDULE_SHA256 = "9206c4267027473218f18e9482abcccb8a64dcfc62a7511d39b711a427a2179c"
EXPECTED_SCHEDULE_FILE_SHA256 = "3f6c0a0ec56fc788ae14287d3333364cffa547e420fad92ee4272debabfc3166"
EXPECTED_CONTROLLER_SHA256 = "25d8bbba9adbde68d92b98b552d9603f05db3015ceb562023a12a8d013e1495b"
EXPECTED_ISSUER_SHA256 = "47d4adee5c4ff36f0117375777ae76d8c34217e40d63812f505ad202bb702e23"
EXPECTED_SUPERVISOR_SHA256 = "f23939f4bb656de73588ae9202437d093b38fc7cbaf4e92b7776cb542ee22b1d"
EXPECTED_RUNTIME_SHA256 = "85b71d8c6ec1905935f74be0c9869aae198d00e98f39df699ec66f9c5a84cecd"
EXPECTED_UV_LOCK_SHA256 = "0c9863fb82c65e8c457b6903b13ab978e1012dc9252e9cca3e95807ef3ded11a"
# Candidate copied byte-for-byte from the preserved 100-game preflight verifier.
# Its independent approval is a separate review gate; this constant is only a pin.
EXPECTED_VERIFIER_SHA256 = "259c5f18edbfe262778ba351651c28f845901f687764193afb2d0ef85402f39a"

SCHEMA = "cardcade-stage002-batch-v1"
ENTRY_SCHEMA = "cardcade-stage002-batch-entry-v1"
BLOCK_COUNT = 30
GAMES_PER_BLOCK = 10
TOTAL_GAMES = 300


class IntegrityError(ValueError):
    """Raised when any execution identity or schedule binding is invalid."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def verify_file_identity(path: Path, expected_sha256: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise IntegrityError(f"required regular file is missing or unsafe: {path}")
    actual = file_sha256(path)
    if actual != expected_sha256.lower():
        raise IntegrityError(f"file identity mismatch for {path}: {actual}")


def _normalized_path(value: str | Path) -> str:
    return os.path.normcase(os.path.realpath(os.fspath(value)))


def validate_repository_identity(
    *,
    repository_root: str | Path,
    working_directory: str | Path,
    git_top_level: str | Path,
    origin: str,
    expected_root: str | Path = EXPECTED_REPO_ROOT,
    expected_origin: str = EXPECTED_ORIGIN,
) -> None:
    if not str(repository_root).strip() or not str(working_directory).strip():
        raise IntegrityError("repository root or working directory identity is missing")
    if not str(git_top_level).strip() or not str(origin).strip():
        raise IntegrityError("Git repository identity is missing")
    expected = _normalized_path(expected_root)
    if _normalized_path(repository_root) != expected:
        raise IntegrityError("script-derived repository root is not the approved repository")
    if _normalized_path(working_directory) != expected:
        raise IntegrityError("caller working directory is not the approved repository root")
    if _normalized_path(git_top_level) != expected:
        raise IntegrityError("Git top-level does not identify the approved repository")
    if origin.rstrip("/").removesuffix(".git") != expected_origin.removesuffix(".git"):
        raise IntegrityError("Git origin does not identify eggggman/tmt")


def _expected_manifest(plan: dict[str, Any], block: dict[str, Any]) -> dict[str, Any]:
    batch_id = block["batch_id"]
    output_root = plan["output_root"]
    authorization_root = plan["authorization_root"]
    games = []
    for row in block["games"]:
        games.append(
            {
                "entry_schema": ENTRY_SCHEMA,
                "index": row["game_index_in_block"],
                "run_id": row["run_id"],
                "seed": row["seed"],
                "orientation": row["orientation"],
                "seats": row["seats"],
                "pairing_id": row["pairing_id"],
                "game_count": 1,
                "worker_invocations": 1,
                "automatic_retries": 0,
                "output_destination": row["output_destination"],
                "authorization_file": row["authorization_file"],
            }
        )
    return {
        "schema": SCHEMA,
        "source_commit": plan["source_commit"],
        "source_blobs": plan["source_blobs"],
        "baseline_manifest_sha256": plan["baseline_manifest_sha256"],
        "card_data_sha256": plan["card_data_sha256"],
        "runtime": plan["runtime"],
        "supervisor_sha256": plan["supervisor_sha256"],
        "batch_controller_sha256": plan["batch_controller_sha256"],
        "issuer_sha256": plan["issuer_sha256"],
        "memory_accounting": plan["memory_accounting"],
        "process_memory_limit_bytes": plan["process_memory_limit_bytes"],
        "job_memory_limit_bytes": plan["job_memory_limit_bytes"],
        "runtime_seconds_limit": plan["runtime_seconds_limit"],
        "maximum_games": GAMES_PER_BLOCK,
        "automatic_retries": 0,
        "output_root": output_root,
        "authorization_root": authorization_root,
        "baseline_input_root": plan["baseline_input_root"],
        "batch_id": batch_id,
        "batch_status_path": f"{output_root}\\{batch_id}.status.json",
        "games": games,
    }


def validate_manifest_projection(
    manifest: dict[str, Any], plan: dict[str, Any], block: dict[str, Any]
) -> None:
    """Require exact structural equality with one ordered schedule block."""
    expected = _expected_manifest(plan, block)
    # Dict equality in Python treats values such as ``True`` and ``1`` as
    # equal. Compare canonical JSON bytes so schema values remain type-exact.
    if canonical_bytes(manifest) != canonical_bytes(expected):
        raise IntegrityError(
            f"manifest does not exactly match scheduled block {block.get('block')}"
        )


def validate_schedule_manifest_set(
    *,
    root: Path,
    expected_schedule_sha256: str = EXPECTED_SCHEDULE_SHA256,
    expected_schedule_file_sha256: str = EXPECTED_SCHEDULE_FILE_SHA256,
) -> dict[str, Any]:
    """Verify the exact frozen schedule, all ordered manifests and preflight records."""
    schedule_dir = root / ".diag003-memory-independent-review" / "300-game-exploratory-r1"
    schedule_path = schedule_dir / "explore300r1.schedule.json"
    manifest_dir = schedule_dir / "manifests"
    preflight_dir = schedule_dir / "preflight-r1"
    raw = schedule_path.read_bytes()
    if sha256_bytes(raw) != expected_schedule_file_sha256:
        raise IntegrityError("approved schedule file bytes changed")
    plan = json.loads(raw)
    if sha256_bytes(canonical_bytes(plan)) != expected_schedule_sha256:
        raise IntegrityError("approved canonical schedule digest changed")
    blocks = plan.get("blocks")
    if (
        not isinstance(blocks, list)
        or len(blocks) != BLOCK_COUNT
        or plan.get("games_total") != TOTAL_GAMES
        or plan.get("seed_range") != [10001, 10300]
    ):
        raise IntegrityError("schedule dimensions or seed range changed")
    scheduled = [row for block in blocks for row in block.get("games", [])]
    if len(scheduled) != TOTAL_GAMES:
        raise IntegrityError("schedule does not contain exactly 300 rows")
    if [row.get("seed") for row in scheduled] != list(range(10001, 10301)):
        raise IntegrityError("schedule seed order is not the approved 10001-10300 sequence")

    expected_names: set[str] = set()
    verified: list[dict[str, Any]] = []
    for ordinal, block in enumerate(blocks, 1):
        if block.get("block") != ordinal or len(block.get("games", [])) != GAMES_PER_BLOCK:
            raise IntegrityError(f"schedule block {ordinal} is missing, duplicated, or malformed")
        batch_id = block["batch_id"]
        expected_name = f"{batch_id}.manifest.json"
        if expected_name in expected_names:
            raise IntegrityError("schedule repeats a block identifier")
        expected_names.add(expected_name)
        manifest_path = manifest_dir / expected_name
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        validate_manifest_projection(manifest, plan, block)

        canonical_sha256 = sha256_bytes(canonical_bytes(manifest))
        sidecar_path = manifest_dir / f"{batch_id}.manifest.sha256"
        sidecar_lines = sidecar_path.read_text(encoding="ascii").splitlines()
        if len(sidecar_lines) != 2:
            raise IntegrityError(f"manifest sidecar is incomplete: {batch_id}")
        if sidecar_lines[0].split()[0] != canonical_sha256:
            raise IntegrityError(f"manifest canonical digest mismatch: {batch_id}")
        if sidecar_lines[1].split()[0] != sha256_bytes(manifest_path.read_bytes()):
            raise IntegrityError(f"manifest file-byte digest mismatch: {batch_id}")

        log_path = preflight_dir / f"{batch_id}.manifest.log"
        exit_path = preflight_dir / f"{batch_id}.manifest.exitcode"
        preflight = json.loads(log_path.read_text(encoding="utf-8-sig"))
        if exit_path.read_text(encoding="ascii").strip() != "0":
            raise IntegrityError(f"preserved preflight exit code is not zero: {batch_id}")
        if (
            preflight.get("state") != "BATCH_PREFLIGHT_ONLY"
            or preflight.get("authorization_issued") is not False
            or preflight.get("manifest_sha256") != canonical_sha256
            or preflight.get("batch_controller_sha256") != EXPECTED_CONTROLLER_SHA256
            or preflight.get("issuer_sha256") != EXPECTED_ISSUER_SHA256
            or preflight.get("supervisor_sha256") != EXPECTED_SUPERVISOR_SHA256
            or preflight.get("runtime", {}).get("python_executable_sha256")
            != EXPECTED_RUNTIME_SHA256
            or preflight.get("runtime", {}).get("uv_lock_sha256") != EXPECTED_UV_LOCK_SHA256
        ):
            raise IntegrityError(f"preserved preflight identity mismatch: {batch_id}")
        verified.append(
            {
                "block": ordinal,
                "batch_id": batch_id,
                "manifest_sha256": canonical_sha256,
                "games": len(manifest["games"]),
            }
        )

    actual_names = {path.name for path in manifest_dir.glob("*.manifest.json")}
    if actual_names != expected_names:
        raise IntegrityError("manifest directory has missing or extra strict manifests")
    return {
        "state": "SCHEDULE_MANIFESTS_VERIFIED",
        "schedule_sha256": expected_schedule_sha256,
        "blocks_verified": len(verified),
        "games_verified": sum(row["games"] for row in verified),
        "blocks": verified,
    }


def _git_value(git_executable: Path, root: Path, *args: str) -> str:
    result = subprocess.run(
        [str(git_executable), "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise IntegrityError(f"Git repository identity query failed: {args[0]}")
    return result.stdout.strip()


def preflight(
    *, root: Path, current_directory: Path, expected_root: Path = Path(EXPECTED_REPO_ROOT)
) -> dict[str, Any]:
    root = root.resolve(strict=True)
    if not root.is_dir() or not (root / ".git").exists():
        raise IntegrityError("expected repository metadata is missing")
    git_executable = Path(r"C:\Program Files\Git\cmd\git.exe")
    if not git_executable.is_file():
        raise IntegrityError("qualified Git executable is missing")
    git_top = _git_value(git_executable, root, "rev-parse", "--show-toplevel")
    origin = _git_value(git_executable, root, "remote", "get-url", "origin")
    validate_repository_identity(
        repository_root=root,
        working_directory=current_directory,
        git_top_level=git_top,
        origin=origin,
        expected_root=expected_root,
    )

    required_files = (
        root
        / ".diag003-memory-independent-review"
        / "300-game-exploratory-r1"
        / "execute_approved_batch.integrity-v2.ps1",
        root
        / ".diag003-memory-independent-review"
        / "300-game-exploratory-r1"
        / "batch_integrity_validation.py",
        root
        / ".diag003-memory-independent-review"
        / "correction"
        / "issue_diag003_authorization.py",
        root
        / ".diag003-memory-independent-review"
        / "correction"
        / "tools"
        / "stage002_diagnostic_supervisor.py",
        root
        / ".diag003-memory-independent-review"
        / "300-game-exploratory-r1"
        / "verify_completed_batch.candidate.py",
        root / ".diag003-preparation" / "python-nuget-3.13.15" / "tools" / "python.exe",
        root / ".diag003-frozen-32a8022" / "uv.lock",
    )
    missing = [str(path) for path in required_files if not path.is_file()]
    if missing:
        raise IntegrityError("required execution dependency missing: " + ", ".join(missing))
    verify_file_identity(required_files[4], EXPECTED_VERIFIER_SHA256)
    return validate_schedule_manifest_set(root=root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--working-directory", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = preflight(root=args.repo_root, current_directory=args.working_directory)
    except (OSError, KeyError, TypeError, json.JSONDecodeError, IntegrityError) as exc:
        print(f"INTEGRITY_PREFLIGHT_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
