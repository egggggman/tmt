"""Validate Combined 002 composition provenance and the one new pairing."""

# Evidence-contract assertions intentionally retain compact long lines.
# ruff: noqa: E501, I001

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402

OBL = ROOT / "docs/objective-balance-lab"


def committed_bytes(commit: str, relative: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{relative}"])


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    evidence = json.loads((OBL / "COMBINED_002_EVIDENCE.json").read_text(encoding="utf-8"))
    checkpoint = json.loads(
        (OBL / "COMBINED_002_EVIDENCE.checkpoint.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (OBL / "combined/OBL_COMBINED_002_MANIFEST.json").read_text(encoding="utf-8")
    )
    assert evidence == checkpoint
    assert evidence["environment_id"] == manifest["environment_id"] == "OBL-COMBINED-002"
    assert evidence["state"] == manifest["state"] == "EXPERIMENTAL_COMBINED_ENVIRONMENT"
    assert evidence["provenance_counts"] == {
        "BASELINE_001_REUSED": 28,
        "ROUND_3_APRIL_REUSED": 8,
        "ROUND_3_KRANG_REUSED": 8,
        "COMBINED_002_NEW_PAIRING": 1,
        "reused_games": 4400,
        "newly_executed_games": 100,
        "logical_games": 4500,
    }
    assert (
        len(evidence["cells"]) == 45
        and len({tuple(cell["matchup"]) for cell in evidence["cells"]}) == 45
    )
    assert len(evidence["combined_results"]) == 4500
    assert len(manifest["selected_decks"]) == 10
    assert set(manifest["selection_experiment_ids"]) == {"OBL-R3-APRIL_ONEIL-A", "OBL-R3-KRANG-A"}
    for cell in evidence["cells"]:
        assert cell["game_count"] == 100
        assert cell["orientation_counts"] == {"canonical": 50, "reversed": 50}
        assert len(cell["games"]) == 100
        assert cell["provenance"] in {
            "BASELINE_001_REUSED",
            "ROUND_3_APRIL_REUSED",
            "ROUND_3_KRANG_REUSED",
            "COMBINED_002_NEW_PAIRING",
        }
        assert (
            sha(json.dumps(cell["games"], sort_keys=True, ensure_ascii=False).encode())
            == cell["matchup_fingerprint"]
        )
        assert all(game["provenance"] == cell["provenance"] for game in cell["games"])
    new_cell = next(
        cell for cell in evidence["cells"] if set(cell["matchup"]) == {"april_oneil", "krang"}
    )
    assert new_cell["provenance"] == "COMBINED_002_NEW_PAIRING"
    assert new_cell["source_experiment_id"] is None
    assert sum(game["schedule"]["orientation"] == "canonical" for game in new_cell["games"]) == 50
    assert sum(game["schedule"]["orientation"] == "reversed" for game in new_cell["games"]) == 50
    assert not any(game.get("runtime_error") for game in evidence["combined_results"])
    # Verify that the source schedule and runtime identities are frozen and equal.
    schedule = r1.schedule()
    assert (
        evidence["schedule_sha256"]
        == hashlib.sha256(json.dumps(schedule, sort_keys=True).encode()).hexdigest()
    )
    assert len(set(evidence["runtime_identity"].values())) == 1
    assert evidence["pilot_identity"] == "tmnt_design_studio.pilot07.AcceptancePilot"
    assert evidence["engine_identity"] == "tmnt_design_studio.stage002.run_game"
    for cell in evidence["cells"]:
        expected = [
            item
            for item in schedule
            if tuple(sorted(item["pair"])) == tuple(sorted(cell["matchup"]))
        ]
        assert [game["schedule"] for game in cell["games"]] == expected
    # Every candidate and baseline deck remains byte-identical to its authenticated source commit.
    for item in manifest["selected_decks"]:
        relative = item["source_path"]
        source_commit = evidence["deck_identity"][item["deck_key"]]["source_commit"]
        assert committed_bytes("HEAD", relative) == committed_bytes(source_commit, relative)
        assert evidence["deck_identity"][item["deck_key"]]["resolved_sha256"] == sha(
            committed_bytes("HEAD", relative)
        )
    # Re-run one game for each orientation of the only newly executed cell.
    paths = {item["deck_key"]: item["source_path"] for item in manifest["selected_decks"]}
    for orientation in ("canonical", "reversed"):
        original = next(
            game for game in new_cell["games"] if game["schedule"]["orientation"] == orientation
        )
        replay = r1._run_one((0, paths, original["schedule"]))
        assert replay["runtime_error"] is None
        assert replay["runtime_fingerprint"] == original["runtime_fingerprint"]
    assert not any(
        subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", item["source_path"]], check=False
        ).returncode
        for item in manifest["selected_decks"]
    )
    print(
        json.dumps(
            {
                "cells": 45,
                "logical_games": 4500,
                "new_games": 100,
                "reused_games": 4400,
                "replays": 2,
                "runtime_errors": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
