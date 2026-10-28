"""Read-only prospective identity/resources report. Never reserves or starts a run.

The emitted candidate inventory is NOT authorization. HQ independently reviews
and pins it before any separately authorized future execution preflight.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tmnt_design_studio.fresh900 import check_resources  # noqa: E402
from tmnt_design_studio.fresh900_identity import (  # noqa: E402
    FROZEN_INPUTS,
    file_hash,
    runtime_inventory,
    verify_inventory,
    verify_locked_wheels,
    verify_runtime,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--git", required=True)
    parser.add_argument("--wheelhouse", type=Path, required=True)
    parser.add_argument("--disposable-parent", type=Path, required=True)
    args = parser.parse_args()
    files = runtime_inventory(ROOT, Path(sys.prefix), Path(sys.base_prefix))
    # Include this explicit diagnostic entrypoint in the prospective inventory.
    files[str(Path(__file__).absolute())] = file_hash(Path(__file__))
    runtime = dict(
        version=sys.version,
        executable=sys.executable,
        base_executable=sys._base_executable,
        source=str(ROOT),
        git_executable=args.git,
        source_commit=subprocess.check_output(
            [
                args.git,
                "-c",
                f"safe.directory={ROOT.as_posix()}",
                "-C",
                str(ROOT),
                "rev-parse",
                "HEAD",
            ],
            text=True,
        ).strip(),
        files=files,
    )
    # Record exact input blobs, not the possibly CRLF-converted checkout.
    inputs = {}
    for relative, expected in FROZEN_INPUTS.items():
        data = subprocess.check_output(
            [
                args.git,
                "-c",
                f"safe.directory={ROOT.as_posix()}",
                "-C",
                str(ROOT),
                "show",
                f"HEAD:{relative}",
            ]
        )
        import hashlib

        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"frozen input Git blob mismatch: {relative}")
        inputs[relative] = expected
    verify_runtime(runtime)
    wheels = verify_locked_wheels(ROOT / "uv.lock", args.wheelhouse, Path(sys.prefix))
    verify_inventory(files)
    print(
        json.dumps(
            dict(
                protocol="fresh900-no-game-preflight-v1",
                candidate_only=True,
                runtime=runtime,
                inputs=inputs,
                dependencies=wheels,
                resources=check_resources(args.disposable_parent),
                games_executed=0,
                blockers=[
                    "No approved live adapter or launch authorization",
                    "Independent acceptance and execution preflight pending",
                    "Full target-volume and gameplay memory limits unproven",
                ],
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
