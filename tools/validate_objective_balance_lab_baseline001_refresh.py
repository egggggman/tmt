"""Fail-closed validator for the Baseline 001 semantic runtime refresh."""

# Validation output includes compact evidence assertions; wide lines are intentional.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    evidence = json.loads(
        (OBL / "BASELINE_001_RUNTIME_REFRESH_EVIDENCE.json").read_text(encoding="utf-8")
    )
    checkpoint = json.loads(
        (OBL / "BASELINE_001_RUNTIME_REFRESH_CHECKPOINT.json").read_text(encoding="utf-8")
    )
    identity = json.loads((OBL / "SEMANTIC_RUNTIME_IDENTITY.json").read_text(encoding="utf-8"))
    assert evidence["environment_id"] == "OBL-BASELINE-001"
    assert evidence["evidence_id"] == "OBL-BASELINE-001-RUNTIME-REFRESH-001"
    games = evidence["games"]
    assert len(games) == 4500 == len(checkpoint["results"])
    assert evidence["runtime_errors"] == 0
    cells = Counter(
        (
            tuple(sorted(row["seats"])),
            row["schedule"]["pair_index"],
            row["schedule"]["block"],
            row["schedule"]["orientation"],
        )
        for row in games
    )
    assert len(cells) == 4500 and set(cells.values()) == {1}
    pair_counts = Counter(tuple(sorted(row["seats"])) for row in games)
    assert len(pair_counts) == 45 and set(pair_counts.values()) == {100}
    orientations = Counter(row["schedule"]["orientation"] for row in games)
    assert orientations == {"canonical": 2250, "reversed": 2250}
    assert (
        evidence["semantic_runtime_sha256"]
        == identity["current"]["aggregate_semantic_runtime_sha256"]
    )
    assert identity["comparisons"]["r4c_equals_current"] is True
    assert evidence["r4c_compatibility"]["status"] == "REUSE_ELIGIBLE_FOR_COMBINED_003"
    original = OBL / "ROUND_1_EVIDENCE.json"
    assert sha(original) == evidence["original_evidence_sha256"]
    assert not subprocess.check_output(
        ["git", "diff", "--name-only", "--", "decks"], cwd=ROOT, text=True
    ).strip()
    print(
        json.dumps(
            {
                "status": "PASS",
                "games": len(games),
                "matchups": len(pair_counts),
                "orientations": orientations,
                "runtime_errors": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
