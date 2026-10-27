"""Read-only status monitor; no checkpoint argument, no policy override."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tmnt_design_studio.resume_status import read_status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--authorization", required=True)
    args = parser.parse_args()
    print(json.dumps(read_status(args.status, authorization=args.authorization), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
