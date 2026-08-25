"""Plan or explicitly execute Coverage-Aware Engine Validation Stage 0.2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tmnt_design_studio.stage02 import execute_stage02, plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--failure-output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.execute:
        if args.output is None or args.failure_output is None:
            parser.error("--execute requires --output and --failure-output")
        execute_stage02(root, output=args.output, failure_output=args.failure_output)
        return
    rendered = json.dumps(plan(root), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
