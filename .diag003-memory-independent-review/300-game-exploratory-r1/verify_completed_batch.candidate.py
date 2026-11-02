"""Read-only verification of a completed authorized ten-game batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

TOOLS = Path(r"C:\projects\tmt\.diag003-memory-independent-review\correction\tools")
sys.path.insert(0, str(TOOLS))

from stage002_authorization import canonical_claims, verify_claims  # noqa: E402
from stage002_batch import digest, entry_claims  # noqa: E402


OUTPUT_ROOT = Path(r"G:\cardcade\diagnostics")
PUBLIC_KEY_PATH = Path(
    r"C:\Users\cowabunga\AppData\Roaming\Cardcade\Stage002Diagnostic\hq-public-key.json"
)
USED_LEDGER = Path(
    r"C:\Users\cowabunga\AppData\Roaming\Cardcade\Stage002Diagnostic\used-authorizations"
)
EXPECTED_COMMIT = "32a80228714674327aca62f8b86b70c4c4afc929"
EXPECTED_MEMORY = 2_997_489_664
EXPECTED_RUNTIME = 600


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_sha = digest(manifest)
    status_path = OUTPUT_ROOT / f"{manifest['batch_id']}.status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if (
        status.get("state") != "COMPLETE"
        or status.get("completed_games") != 10
        or status.get("automatic_retries") != 0
        or status.get("manifest_sha256") != manifest_sha
        or len(status.get("games", [])) != 10
    ):
        raise ValueError("batch checkpoint is incomplete or inconsistent")
    public_key = json.loads(PUBLIC_KEY_PATH.read_text(encoding="utf-8"))
    nonces: set[str] = set()
    outcomes: list[dict[str, Any]] = []
    artifacts_checked = 0
    for index, (row, record) in enumerate(zip(manifest["games"], status["games"]), 1):
        if (
            record.get("index") != index
            or record.get("run_id") != row["run_id"]
            or record.get("state") != "RETURNED"
            or record.get("exit_code") != 0
        ):
            raise ValueError(f"game {index} did not return successfully")
        resource = record["resource_gate"]
        if (
            resource["available_physical_bytes"] < resource["minimum_each_bytes"]
            or resource["system_commit_headroom_bytes"] < resource["minimum_each_bytes"]
        ):
            raise ValueError(f"game {index} resource gate failed")
        storage = record["storage_gate"]
        if (
            storage["file_system"] != "NTFS"
            or storage["volume_label"] != "TMT"
            or storage["available_bytes"] < storage["required_free_bytes"]
        ):
            raise ValueError(f"game {index} storage gate failed")
        output = OUTPUT_ROOT / row["run_id"]
        for relative, expected in record["artifacts_sha256"].items():
            artifact = output.joinpath(*relative.split("\\"))
            if not artifact.is_file() or artifact.is_symlink() or sha256(artifact) != expected:
                raise ValueError(f"game {index} artifact mismatch: {relative}")
            artifacts_checked += 1
        run = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
        result = json.loads((output / "result.json").read_text(encoding="utf-8"))
        if (
            run.get("run_id") != row["run_id"]
            or run.get("batch_manifest_sha256") != manifest_sha
            or run.get("source_commit") != EXPECTED_COMMIT
            or run.get("process_memory_limit_bytes") != EXPECTED_MEMORY
            or run.get("runtime_seconds_limit") != EXPECTED_RUNTIME
            or result.get("run_id") != row["run_id"]
            or result.get("seed") != row["seed"]
            or result.get("completion_state") != "COMPLETE"
            or result["snapshot"].get("winner") not in {s["deck_key"] for s in row["seats"]}
        ):
            raise ValueError(f"game {index} result identity or completion is invalid")
        grant = json.loads(Path(row["authorization_file"]).read_text(encoding="utf-8"))
        nonce = verify_claims(grant, public_key, entry_claims(manifest, manifest_sha, index))
        if nonce in nonces:
            raise ValueError("batch reused a one-use authorization nonce")
        nonces.add(nonce)
        used = USED_LEDGER / f"{nonce}.used"
        expected_claim_digest = hashlib.sha256(canonical_claims(grant)).hexdigest()
        if not used.is_file() or used.read_text(encoding="ascii").strip() != expected_claim_digest:
            raise ValueError(f"game {index} authorization consumption record is missing or wrong")
        outcomes.append(
            {
                "seed": row["seed"],
                "seats": [s["deck_key"] for s in row["seats"]],
                "winner": result["snapshot"]["winner"],
                "turn": result["snapshot"].get("turn"),
                "run_id": row["run_id"],
            }
        )
    return {
        "state": "VERIFIED_COMPLETE",
        "batch_id": manifest["batch_id"],
        "manifest_sha256": manifest_sha,
        "games_verified": len(outcomes),
        "artifact_hashes_rechecked": artifacts_checked,
        "automatic_retries": 0,
        "outcomes": outcomes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.manifest.resolve(strict=True)), sort_keys=True))
    except Exception as exc:
        print(f"VERIFICATION_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
