"""Validate the fail-closed Combined 003 composition gate."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs" / "objective-balance-lab"


def main() -> None:
    evidence = json.loads((OBL / "COMBINED_003_EVIDENCE.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (OBL / "combined/OBL_COMBINED_003_MANIFEST.json").read_text(encoding="utf-8")
    )
    assert evidence["state"] == "BLOCKED_BY_RUNTIME_INCOMPATIBILITY"
    assert manifest["composition_authorized"] is False
    assert evidence["newly_executed_games"] == 0
    assert evidence["accepted_reused_games"] == 0
    assert evidence["provenance_counts"] == {
        "BASELINE_001_REUSED": 0,
        "ROUND_4B_RAPHAEL_C_REUSED": 0,
        "incompatible_baseline_cells": 36,
        "incompatible_raphael_cells": 9,
    }
    assert (
        evidence["source_artifacts"]["baseline_combined_evidence"]["repository_sha"]
        != evidence["source_artifacts"]["round4b_evidence"]["repository_sha"]
    )
    assert (
        evidence["source_artifacts"]["baseline_combined_evidence"]["schedule_sha256"]
        == evidence["source_artifacts"]["round4b_evidence"]["schedule_sha256"]
    )
    print("Combined 003 composition correctly failed closed: zero games executed or accepted.")


if __name__ == "__main__":
    main()
