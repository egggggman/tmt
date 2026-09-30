"""Compose OBL-COMBINED-002 and execute only its new April/Krang pairing."""

# The evidence tables intentionally retain compact long expressions.
# ruff: noqa: E501, I001

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402

OBL = ROOT / "docs/objective-balance-lab"
BASELINE_MANIFEST = OBL / "baselines/OBL_BASELINE_001_MANIFEST.json"
COMBINED_001 = OBL / "COMBINED_001_EVIDENCE.json"
ROUND_3 = OBL / "ROUND_3_EVIDENCE.json"
NEW_PAIR = OBL / "COMBINED_002_NEW_PAIRING.json"
NEW_CHECKPOINT = OBL / "COMBINED_002_NEW_PAIRING.checkpoint.json"
APRIL_ID = "OBL-R3-APRIL_ONEIL-A"
KRANG_ID = "OBL-R3-KRANG-A"
APRIL = "april_oneil"
KRANG = "krang"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def committed_sha(path: Path) -> str:
    """Hash canonical repository bytes, independent of Windows checkout CRLF."""
    relative = path.relative_to(ROOT).as_posix()
    try:
        data = subprocess.check_output(["git", "show", f"HEAD:{relative}"])
    except subprocess.CalledProcessError:
        data = path.read_bytes()
    return sha_bytes(data)


def committed_bytes(commit: str, relative: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{relative}"])


def canonical_runtime_identity(commit: str) -> str:
    names = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", commit, "src", "cardcade"], text=True
    ).splitlines()
    names = [name for name in names if name.endswith((".py", ".json", ".toml"))]
    digest = hashlib.sha256()
    for name in names:
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(subprocess.check_output(["git", "show", f"{commit}:{name}"]))
        digest.update(b"\0")
    return digest.hexdigest()


def cell_key(pair: list[str] | tuple[str, str]) -> tuple[str, str]:
    return tuple(sorted(pair))


def schedule_by_cell(schedule: list[dict]) -> dict[tuple[str, str], list[dict]]:
    result: dict[tuple[str, str], list[dict]] = {}
    for item in schedule:
        result.setdefault(cell_key(item["pair"]), []).append(item)
    return result


def game_schedule(game: dict) -> dict:
    return game["schedule"]


def fingerprint(games: list[dict]) -> str:
    return sha_bytes(json.dumps(games, sort_keys=True, ensure_ascii=False).encode())


def verify_source_games(games: list[dict], expected: list[dict], label: str) -> None:
    assert len(games) == 100, (label, len(games))
    assert [game_schedule(game) for game in games] == expected, label
    assert not any(game.get("runtime_error") for game in games), label
    assert sum(game_schedule(game)["orientation"] == "canonical" for game in games) == 50, label
    assert sum(game_schedule(game)["orientation"] == "reversed" for game in games) == 50, label
    assert all(game.get("runtime_fingerprint") for game in games), label


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    baseline_manifest = json.loads(BASELINE_MANIFEST.read_text(encoding="utf-8"))
    combined001 = json.loads(COMBINED_001.read_text(encoding="utf-8"))
    round3 = json.loads(ROUND_3.read_text(encoding="utf-8"))
    schedule = r1.schedule()
    expected_cells = schedule_by_cell(schedule)
    assert len(schedule) == 4500 and len(expected_cells) == 45
    assert combined001["schedule_sha256"] == round3["schedule_sha256"]
    assert len(combined001["combined_results"]) == 4500
    assert round3["counts"] == {
        "expected_candidates": 8,
        "expected_games": 7200,
        "completed_games": 7200,
        "runtime_errors": 0,
    }
    runtime_ids = {
        "combined_001": canonical_runtime_identity(combined001["repository_sha"]),
        "round_3": canonical_runtime_identity(round3["repository_sha"]),
        "current": canonical_runtime_identity("HEAD"),
    }
    assert len(set(runtime_ids.values())) == 1, runtime_ids
    cards = r1.catalog()
    baseline_by_key = {item["deck_key"]: item for item in baseline_manifest["decks"]}
    baseline_source_commit = combined001["repository_sha"]
    deck_identity = {}
    for item in baseline_by_key.values():
        path = ROOT / item["source_path"]
        relative = item["source_path"]
        current_bytes = committed_bytes("HEAD", relative)
        source_bytes = committed_bytes(baseline_source_commit, relative)
        assert current_bytes == source_bytes, ("baseline deck drift", relative)
        deck_identity[item["deck_key"]] = {
            "source_path": relative,
            "declared_lineage_sha256": item["sha256"],
            "resolved_sha256": sha_bytes(current_bytes),
            "source_commit": baseline_source_commit,
        }
        r1.validate_deck(path, cards)
    r3_manifests = round3["candidate_manifests"]
    for experiment_id in (APRIL_ID, KRANG_ID):
        assert experiment_id in r3_manifests
        candidate = r3_manifests[experiment_id]
        relative = candidate["candidate_path"]
        current_bytes = committed_bytes("HEAD", relative)
        candidate_source_commit = subprocess.check_output(
            ["git", "log", "--format=%H", "--all", "-n", "1", "--", relative], text=True
        ).strip()
        source_bytes = committed_bytes(candidate_source_commit, relative)
        assert current_bytes == source_bytes, ("candidate deck drift", relative)
        deck_identity[candidate["deck_key"]] = {
            "source_path": relative,
            "declared_lineage_sha256": candidate["candidate_sha256"],
            "resolved_sha256": sha_bytes(current_bytes),
            "source_commit": candidate_source_commit,
        }
        r1.validate_deck(ROOT / candidate["candidate_path"], cards)

    source_combined = {
        cell_key(game["schedule"]["pair"]): [] for game in combined001["combined_results"]
    }
    for game in combined001["combined_results"]:
        source_combined[cell_key(game["schedule"]["pair"])].append(game)
    source_april = {
        cell_key(game["schedule"]["pair"]): [] for game in round3["candidate_results"][APRIL_ID]
    }
    for game in round3["candidate_results"][APRIL_ID]:
        source_april[cell_key(game["schedule"]["pair"])].append(game)
    source_krang = {
        cell_key(game["schedule"]["pair"]): [] for game in round3["candidate_results"][KRANG_ID]
    }
    for game in round3["candidate_results"][KRANG_ID]:
        source_krang[cell_key(game["schedule"]["pair"])].append(game)

    new_games: list[dict]
    if NEW_PAIR.exists():
        existing = json.loads(NEW_PAIR.read_text(encoding="utf-8"))
        new_games = existing["games"]
        assert existing["schedule_sha256"] == round3["schedule_sha256"]
    else:
        paths = {key: value["source_path"] for key, value in baseline_by_key.items()}
        paths[APRIL] = r3_manifests[APRIL_ID]["candidate_path"]
        paths[KRANG] = r3_manifests[KRANG_ID]["candidate_path"]
        new_games = r1.run_set(paths, expected_cells[cell_key((APRIL, KRANG))], cards, args.workers)
        NEW_CHECKPOINT.write_text(
            json.dumps(
                {
                    "schema": "obl-combined-002-new-pairing-v1",
                    "schedule_sha256": round3["schedule_sha256"],
                    "games": new_games,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        NEW_PAIR.write_text(
            json.dumps(
                {
                    "schema": "obl-combined-002-new-pairing-v1",
                    "schedule_sha256": round3["schedule_sha256"],
                    "runtime_identity": runtime_ids,
                    "games": new_games,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
    verify_source_games(
        new_games, expected_cells[cell_key((APRIL, KRANG))], "new April/Krang pairing"
    )

    cells = []
    composed_results = []
    provenance_counts = {
        "BASELINE_001_REUSED": 0,
        "ROUND_3_APRIL_REUSED": 0,
        "ROUND_3_KRANG_REUSED": 0,
        "COMBINED_002_NEW_PAIRING": 0,
    }
    for key in sorted(expected_cells):
        if key == cell_key((APRIL, KRANG)):
            provenance = "COMBINED_002_NEW_PAIRING"
            source_id = None
            games = new_games
            source_path = "docs/objective-balance-lab/COMBINED_002_NEW_PAIRING.json"
        elif APRIL in key:
            provenance = "ROUND_3_APRIL_REUSED"
            source_id = APRIL_ID
            games = source_april[key]
            source_path = "docs/objective-balance-lab/ROUND_3_EVIDENCE.json"
        elif KRANG in key:
            provenance = "ROUND_3_KRANG_REUSED"
            source_id = KRANG_ID
            games = source_krang[key]
            source_path = "docs/objective-balance-lab/ROUND_3_EVIDENCE.json"
        else:
            provenance = "BASELINE_001_REUSED"
            source_id = None
            games = source_combined[key]
            source_path = "docs/objective-balance-lab/COMBINED_001_EVIDENCE.json"
        verify_source_games(games, expected_cells[key], f"{provenance}:{key}")
        tagged_games = []
        for game in games:
            tagged = dict(game)
            tagged["provenance"] = provenance
            tagged["source_experiment_id"] = source_id
            composed_results.append(tagged)
            tagged_games.append(tagged)
        provenance_counts[provenance] += 1
        cells.append(
            {
                "matchup": list(key),
                "game_count": len(games),
                "provenance": provenance,
                "source_artifact": source_path,
                "source_experiment_id": source_id,
                "seed_identity": round3["schedule_sha256"],
                "orientation_counts": {"canonical": 50, "reversed": 50},
                "source_matchup_fingerprint": fingerprint(games),
                "matchup_fingerprint": fingerprint(tagged_games),
                "games": tagged_games,
            }
        )
    assert len(cells) == 45 and len(composed_results) == 4500
    assert provenance_counts == {
        "BASELINE_001_REUSED": 28,
        "ROUND_3_APRIL_REUSED": 8,
        "ROUND_3_KRANG_REUSED": 8,
        "COMBINED_002_NEW_PAIRING": 1,
    }
    output = {
        "schema": "objective-balance-lab-combined-environment-v2",
        "environment_id": "OBL-COMBINED-002",
        "state": "EXPERIMENTAL_COMBINED_ENVIRONMENT",
        "repository_sha": "ca3b6b83f59f449091f103d1e94c117ddb9ff5fa",
        "parent_environment_id": "OBL-BASELINE-001",
        "schedule_sha256": round3["schedule_sha256"],
        "schedule_games": 4500,
        "runtime_identity": runtime_ids,
        "pilot_identity": "tmnt_design_studio.pilot07.AcceptancePilot",
        "engine_identity": "tmnt_design_studio.stage002.run_game",
        "deck_identity": deck_identity,
        "provenance_counts": {
            **provenance_counts,
            "reused_games": 4400,
            "newly_executed_games": 100,
            "logical_games": 4500,
        },
        "cells": cells,
        "combined_results": composed_results,
        "source_artifacts": {
            "baseline_001": {
                "path": "docs/objective-balance-lab/COMBINED_001_EVIDENCE.json",
                "sha256": committed_sha(COMBINED_001),
            },
            "round_3": {
                "path": "docs/objective-balance-lab/ROUND_3_EVIDENCE.json",
                "sha256": committed_sha(ROUND_3),
            },
            "new_pairing": {
                "path": "docs/objective-balance-lab/COMBINED_002_NEW_PAIRING.json",
                "sha256": sha(NEW_PAIR),
            },
        },
    }
    (OBL / "COMBINED_002_EVIDENCE.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OBL / "COMBINED_002_EVIDENCE.checkpoint.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "logical_games": 4500,
                "new_games": 100,
                "reused_games": 4400,
                "cells": len(cells),
                "provenance": provenance_counts,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
