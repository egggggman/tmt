"""Run the immutable Baseline 003 matrix under the Chrome-Dome-capable runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402

BASE = "9eb8cb6d6a7afac2848877cdd1b8ae4ba6faa24a"
RUNTIME = "252f00317d8efbf552512768503d5f453ef9594ade48e27a94f95f05c7625982"
OLD_RUNTIME = "78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25"
SCHEDULE_SHA = "b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27"
EVIDENCE_ID = "OBL-BASELINE-003-RUNTIME-REFRESH-001"
MANIFEST = OBL / "baselines/OBL_BASELINE_003_MANIFEST.json"
HISTORICAL = OBL / "COMBINED_005_EVIDENCE.json"
CHECKPOINT = OBL / "BASELINE_003_RUNTIME_REFRESH_CHECKPOINT.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes().replace(b"\r\n", b"\n"))


def verify_deck(row: dict) -> None:
    relative = row["source_path"]
    local = (ROOT / relative).read_bytes()
    committed = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=ROOT)
    canonical = committed.replace(b"\r\n", b"\n")
    assert local.replace(b"\r\n", b"\n") == canonical, relative
    assert row["sha256"] in {
        sha(local),
        sha(committed),
        sha(canonical),
        sha(canonical.replace(b"\n", b"\r\n")),
    }, relative


def preflight() -> tuple[dict, list[dict], dict, dict]:
    assert (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE, "HEAD"], cwd=ROOT, check=False
        ).returncode
        == 0
    )
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    old = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    runtime = identity(BASE)
    assert (
        identity()["aggregate_semantic_runtime_sha256"]
        == runtime["aggregate_semantic_runtime_sha256"]
        == RUNTIME
        != OLD_RUNTIME
    )
    assert manifest["environment_id"] == "OBL-BASELINE-003"
    assert manifest["semantic_runtime_sha256"] == old["semantic_runtime_sha256"] == OLD_RUNTIME
    assert manifest["schedule_identity"] == old["schedule_sha256"] == SCHEDULE_SHA
    assert len(manifest["decks"]) == 10
    assert {row["deck_key"] for row in manifest["decks"]} == set(r1.DECKS)
    cards = r1.catalog()
    paths = {}
    for row in manifest["decks"]:
        verify_deck(row)
        assert sum(r1.validate_deck(ROOT / row["source_path"], cards)["cards"].values()) == 60
        paths[row["deck_key"]] = row["source_path"]
    schedule = r1.schedule()
    assert len(schedule) == 4500 and r5.digest(schedule) == SCHEDULE_SHA
    assert Counter(item["orientation"] for item in schedule) == {
        "canonical": 2250,
        "reversed": 2250,
    }
    return manifest, schedule, paths, runtime


def checkpoint_template(manifest: dict, runtime: dict) -> dict:
    return {
        "schema": "obl-baseline-003-runtime-refresh-checkpoint-v1",
        "environment_id": "OBL-BASELINE-003",
        "evidence_id": EVIDENCE_ID,
        "state": "BASELINE_EVIDENCE_REFRESH",
        "repository_sha": BASE,
        "semantic_runtime_sha256": RUNTIME,
        "old_semantic_runtime_sha256": OLD_RUNTIME,
        "semantic_runtime_identity": runtime,
        "baseline_manifest_path": MANIFEST.relative_to(ROOT).as_posix(),
        "baseline_manifest_sha256": file_sha(MANIFEST),
        "historical_evidence_path": HISTORICAL.relative_to(ROOT).as_posix(),
        "historical_evidence_sha256": file_sha(HISTORICAL),
        "schedule_sha256": SCHEDULE_SHA,
        "deck_manifest": manifest["decks"],
        "results": [],
        "cell_fingerprints": [],
        "counts": {"completed_games": 0, "runtime_errors": 0},
    }


def original_cell_fingerprint(records: list[dict]) -> str:
    """Reconstruct the in-memory integer turn keys before checking stored hashes.

    ``game_metrics`` keys battlefield turns by integer. JSON round-trips those
    keys as strings; restoring them authenticates the original execution hash
    without rewriting any checkpointed game or fingerprint.
    """
    canonical = []
    for game in records:
        restored = dict(game)
        restored["battlefield_presence"] = {
            deck: {int(turn): count for turn, count in turns.items()}
            for deck, turns in game["battlefield_presence"].items()
        }
        canonical.append(restored)
    return r5.digest(canonical)


def verify_checkpoint(checkpoint: dict, expected: dict, schedule: list[dict]) -> None:
    for key, value in expected.items():
        if key not in {"results", "cell_fingerprints", "counts"}:
            assert checkpoint[key] == value, key
    games = checkpoint["results"]
    assert len(games) <= 4500 and len(games) % 100 == 0
    assert checkpoint["counts"] == {
        "completed_games": len(games),
        "runtime_errors": 0,
    }
    assert len(checkpoint["cell_fingerprints"]) == len(games) // 100
    for index, game in enumerate(games):
        assert game["schedule"] == schedule[index], index
        assert game["seats"] == schedule[index]["decks"], index
        assert game["runtime_error"] is None and game["runtime_fingerprint"], index
    for index, cell in enumerate(checkpoint["cell_fingerprints"]):
        records = games[index * 100 : (index + 1) * 100]
        assert cell["decks"] == schedule[index * 100]["pair"]
        assert cell["fingerprint"] == original_cell_fingerprint(records)
        assert Counter(game["schedule"]["orientation"] for game in records) == {
            "canonical": 50,
            "reversed": 50,
        }


def save(checkpoint: dict) -> None:
    temporary = CHECKPOINT.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(checkpoint, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(CHECKPOINT)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="execute missing frozen matchup cells")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    manifest, schedule, paths, runtime = preflight()
    expected = checkpoint_template(manifest, runtime)
    checkpoint = (
        json.loads(CHECKPOINT.read_text(encoding="utf-8")) if CHECKPOINT.exists() else expected
    )
    verify_checkpoint(checkpoint, expected, schedule)
    if not args.run:
        print(json.dumps({"status": "PREFLIGHT_PASS", "completed": len(checkpoint["results"])}))
        return 0
    assert 1 <= args.workers <= 16
    cards = r1.catalog()
    with ProcessPoolExecutor(
        max_workers=args.workers, initializer=r1._init_worker, initargs=(cards,)
    ) as executor:
        for offset in range(len(checkpoint["results"]), len(schedule), 100):
            items = [(index + 1, paths, schedule[index]) for index in range(offset, offset + 100)]
            records = list(executor.map(r1._run_one, items, chunksize=1))
            assert all(row["runtime_error"] is None for row in records), (
                schedule[offset]["pair"],
                [row["runtime_error"] for row in records if row["runtime_error"]],
            )
            assert all(row["runtime_fingerprint"] for row in records)
            assert [row["schedule"] for row in records] == schedule[offset : offset + 100]
            checkpoint["results"].extend(records)
            checkpoint["cell_fingerprints"].append(
                {"decks": schedule[offset]["pair"], "fingerprint": r5.digest(records)}
            )
            checkpoint["counts"]["completed_games"] += 100
            save(checkpoint)
            print(f"completed {offset + 100}/4500", flush=True)
    verify_checkpoint(checkpoint, expected, schedule)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
