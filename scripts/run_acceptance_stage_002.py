"""Plan or explicitly execute the frozen Cardcade Acceptance Stage #002 matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tmnt_design_studio.stage002 import execute_stage, plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = execute_stage(root) if args.execute else plan(root)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
