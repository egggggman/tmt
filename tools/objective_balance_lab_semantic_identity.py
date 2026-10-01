"""Compute the fail-closed semantic identity used by OBL evidence composition."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# These are the execution/runtime inputs, not reporting artifacts.  Keep this list
# explicit so a future semantic change cannot be hidden by a repository SHA.
SEMANTIC_PATHS = [
    *sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src/tmnt_design_studio").glob("*.py")
        if path.is_file()
    ),
    "tools/run_objective_balance_lab_round1.py",
    "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
    "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    "docs/cardcade/CALIBRATION_SEED_TABLE_V2.json",
]


def _git_bytes(commit: str, relative: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{relative}"], cwd=ROOT)


def _current_bytes(relative: str) -> bytes:
    # Git-authored text is compared by logical contents, not checkout newline mode.
    return (ROOT / relative).read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def identity(commit: str | None = None) -> dict[str, object]:
    records = []
    for relative in SEMANTIC_PATHS:
        content = _git_bytes(commit, relative) if commit else _current_bytes(relative)
        content = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        records.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
            }
        )
    canonical = json.dumps(
        [{"path": row["path"], "sha256": row["sha256"]} for row in records],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "identity_schema": "obl-semantic-runtime-v1",
        "repository_commit": commit
        or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "files": records,
        "aggregate_semantic_runtime_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = identity(args.commit)
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
