"""Validate the runtime-compatible, zero-new-game Combined 003 composition."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
RUNTIME = "78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25"


def fingerprint(games: list[dict[str, object]]) -> str:
    rendered = json.dumps(games, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(rendered).hexdigest()


def grouped(games: list[dict[str, object]]) -> dict[tuple[str, str], list[dict[str, object]]]:
    result: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for game in games:
        result[tuple(sorted(game["seats"]))].append(game)
    return dict(result)


def main() -> int:
    evidence = json.loads(
        (OBL / "COMBINED_003_RUNTIME_COMPATIBLE_EVIDENCE.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (OBL / "combined/OBL_COMBINED_003_RUNTIME_COMPATIBLE_MANIFEST.json").read_text(
            encoding="utf-8"
        )
    )
    baseline = json.loads(
        (OBL / "BASELINE_001_RUNTIME_REFRESH_EVIDENCE.json").read_text(encoding="utf-8")
    )
    r4b = json.loads((OBL / "ROUND_4B_RAPHAEL_EVIDENCE.json").read_text(encoding="utf-8"))
    identity = json.loads((OBL / "SEMANTIC_RUNTIME_IDENTITY.json").read_text(encoding="utf-8"))
    assert evidence["state"] == "EXPERIMENTAL_COMBINED_ENVIRONMENT"
    assert manifest["composition_authorized"] is True
    assert evidence["semantic_runtime_sha256"] == RUNTIME == baseline["semantic_runtime_sha256"]
    assert identity["current"]["aggregate_semantic_runtime_sha256"] == RUNTIME
    assert identity["r4c_evidence_runtime"]["aggregate_semantic_runtime_sha256"] == RUNTIME
    assert (
        evidence["schedule_sha256"]
        == baseline["deterministic_schedule_sha256"]
        == r4b["schedule_sha256"]
    )
    games = evidence["combined_games"]
    assert len(games) == evidence["logical_games"] == 4500
    assert evidence["reused_games"] == 4500 and evidence["newly_executed_games"] == 0
    source_groups = grouped(baseline["games"])
    r4c_groups = grouped(r4b["candidate_results"]["OBL-R4-RAPHAEL-C"])
    composed_groups = grouped(games)
    assert len(composed_groups) == 45 and all(len(rows) == 100 for rows in composed_groups.values())
    assert len(evidence["provenance"]) == 45
    assert Counter(row["provenance"] for row in evidence["provenance"]) == Counter(
        {"BASELINE_001_RUNTIME_REFRESH_REUSED": 36, "ROUND_4B_RAPHAEL_C_REUSED": 9}
    )
    for row in evidence["provenance"]:
        pair = tuple(row["decks"])
        source = (
            r4c_groups[pair]
            if row["provenance"] == "ROUND_4B_RAPHAEL_C_REUSED"
            else source_groups[pair]
        )
        assert row["semantic_runtime_sha256"] == RUNTIME
        assert row["games"] == 100
        assert row["orientation_counts"] == {"canonical": 50, "reversed": 50}
        assert row["fingerprint"] == fingerprint(source)
        assert fingerprint(composed_groups[pair]) == fingerprint(source)
    assert not subprocess.check_output(
        ["git", "diff", "--name-only", "--", "decks"], cwd=ROOT, text=True
    ).strip()
    print(
        json.dumps(
            {
                "status": "PASS",
                "cells": 45,
                "logical_games": 4500,
                "reused_games": 4500,
                "newly_executed_games": 0,
                "provenance": {"baseline": 36, "r4c": 9},
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
