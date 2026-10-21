"""Run the frozen Splinter R9-A isolated probe with fail-closed evidence."""

from __future__ import annotations

import gzip
import hashlib
import json
import statistics
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402
from artifact_integrity import write_validated_artifact  # noqa: E402
from objective_balance_lab_semantic_identity import identity  # noqa: E402

RUNTIME = "defefdce8a716ceef6dcedad1a6f50e2abc367bd3cb772a369853506d2f5398d"
CONTROL_ID = "OBL-BASELINE-005-LTB-REPAIR-CONTROL-ATTEMPT-009"
EXPERIMENT_ID = "OBL-R9-SPLINTER-A"
CANDIDATE = OBL / "candidates/SPLINTER_OBL_R9_A.txt"
OUTPUT = OBL / "ROUND_9_A_SPLINTER_EVIDENCE.json.gz"
REPORT = OBL / "ROUND_9_A_SPLINTER_RESULTS.md"
SCHEDULE_SHA = "b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27"


def digest(value: object) -> str:
    normalized = json.loads(json.dumps(value, ensure_ascii=False))
    return hashlib.sha256(
        json.dumps(normalized, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deck_paths() -> dict[str, str]:
    manifest = json.loads((OBL / "baselines/OBL_BASELINE_005_MANIFEST.json").read_text())
    paths = {row["deck_key"]: row["source_path"] for row in manifest["decks"]}
    paths["splinter"] = CANDIDATE.relative_to(ROOT).as_posix()
    return paths


def preflight() -> tuple[list[dict], dict[str, str], dict]:
    assert identity()["aggregate_semantic_runtime_sha256"] == RUNTIME
    manifest = json.loads((OBL / "baselines/OBL_BASELINE_005_MANIFEST.json").read_text())
    assert manifest["environment_id"] == "OBL-BASELINE-005"
    assert len(manifest["decks"]) == 10
    cards = r1.catalog()
    parent_path = ROOT / next(row["source_path"] for row in manifest["decks"] if row["deck_key"] == "splinter")
    parent = r1.validate_deck(parent_path, cards)
    candidate = r1.validate_deck(CANDIDATE, cards)
    assert sum(candidate["cards"].values()) == 60
    assert r1.diff(parent["cards"], candidate["cards"]) == {
        "Splinter, Hamato Yoshi": {"parent": 4, "candidate": 3},
        "Stomped by the Foot": {"parent": 3, "candidate": 4},
    }
    schedule = r1.schedule()
    assert len(schedule) == 4500 and r5.digest(schedule) == SCHEDULE_SHA
    selected = [row for row in schedule if "splinter" in row["pair"]]
    assert len(selected) == 900
    for offset in range(0, 900, 100):
        cell = selected[offset : offset + 100]
        assert Counter(row["orientation"] for row in cell) == {"canonical": 50, "reversed": 50}
        assert sum(
            row["decks"][0] == "splinter" for row in cell
        ) == 50
    return selected, deck_paths(), manifest


def run_rows(rows: list[dict], paths: dict[str, str], workers: int, offset: int) -> list[dict]:
    with ProcessPoolExecutor(max_workers=workers, initializer=r1._init_worker, initargs=(r1.catalog(),)) as pool:
        results = list(pool.map(r1._run_one, [(offset + i + 1, paths, row) for i, row in enumerate(rows)], chunksize=1))
    assert all(result.get("runtime_error") is None for result in results), "runtime failure"
    return results


def summarize(games: list[dict]) -> dict:
    opponents = [next(deck for deck in game["seats"] if deck != "splinter") for game in games]
    by_opponent = {}
    for opponent in sorted(set(opponents)):
        own = [game for game, opp in zip(games, opponents) if opp == opponent]
        wins = sum(game["winner"] == "splinter" for game in own)
        draws = sum(game["draw"] for game in own)
        starts = [game for game in own if game["first_player"] == "splinter"]
        by_opponent[opponent] = {
            "games": len(own), "wins": wins, "draws": draws,
            "win_rate": round((wins + draws / 2) / len(own), 6),
            "first_player_games": len(starts),
            "first_player_wins": sum(game["winner"] == "splinter" for game in starts),
            "mean_turn": round(statistics.mean(game["turn"] for game in own), 4),
            "median_turn": statistics.median(game["turn"] for game in own),
        }
    all_wins = sum(game["winner"] == "splinter" for game in games)
    return {
        "games": len(games), "wins": all_wins,
        "draws": sum(game["draw"] for game in games),
        "win_rate": round((all_wins + sum(game["draw"] for game in games) / 2) / len(games), 6),
        "mean_turn": round(statistics.mean(game["turn"] for game in games), 4),
        "median_turn": statistics.median(game["turn"] for game in games),
        "by_opponent": by_opponent,
        "first_player": {
            "games": sum(game["first_player"] == "splinter" for game in games),
            "wins": sum(game["first_player"] == "splinter" and game["winner"] == "splinter" for game in games),
        },
        "casts": sum(sum(game.get("casts", {}).values()) for game in games),
        "interaction_casts": sum(game.get("interaction_casts", {}).get("splinter", 0) for game in games),
        "activation_events": sum(len(game.get("activation_events", [])) for game in games),
        "aura_events": sum(len(game.get("aura_events", [])) for game in games),
        "etb_life_gain_events": sum(len(game.get("etb_life_gain_events", [])) for game in games),
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    selected, paths, manifest = preflight()
    if OUTPUT.exists():
        raise RuntimeError(f"refusing to overwrite {OUTPUT}")
    games: list[dict] = []
    replays: dict[str, str] = {}
    for offset in range(0, len(selected), 100):
        rows = selected[offset : offset + 100]
        cell = run_rows(rows, paths, args.workers, offset)
        games.extend(cell)
        key = "|".join(rows[0]["pair"])
        replay = run_rows(rows, paths, args.workers, 1000 + offset)
        assert digest(replay) == digest(cell)
        replays[key] = digest(replay)
        print(json.dumps({"cell": key, "games": len(games)}), flush=True)
    evidence = {
        "schema": "obl-round9a-isolated-v1", "status": "COMPLETE", "experiment_id": EXPERIMENT_ID,
        "control_id": CONTROL_ID, "semantic_runtime_sha256": RUNTIME,
        "schedule_sha256": SCHEDULE_SHA, "selected_schedule_sha256": digest(selected),
        "baseline_manifest_sha256": sha(OBL / "baselines/OBL_BASELINE_005_MANIFEST.json"),
        "candidate_path": CANDIDATE.relative_to(ROOT).as_posix(), "candidate_sha256": sha(CANDIDATE),
        "candidate_diff": {"Splinter, Hamato Yoshi": {"parent": 4, "candidate": 3}, "Stomped by the Foot": {"parent": 3, "candidate": 4}},
        "required_games": 900, "games": games, "replays": replays, "summary": summarize(games),
        "combined_validation_run": False, "promotion_authorized": False,
        "prior_control_artifact_sha256": "55a1f0074e5c61548744ed78421ade014ea04627ac01a6f772dfce5daad19c09",
    }
    expected = {"schema": evidence["schema"], "experiment_id": EXPERIMENT_ID, "semantic_runtime_sha256": RUNTIME, "schedule_sha256": SCHEDULE_SHA}
    write_validated_artifact(OUTPUT, evidence, expected_manifest=expected)
    s = evidence["summary"]
    lines = [
        "# Round 9-A — Splinter isolated balance probe", "",
        f"Candidate `{EXPERIMENT_ID}`: −1 Splinter, Hamato Yoshi / +1 Stomped by the Foot.",
        f"Control: `{CONTROL_ID}`. Runtime: `{RUNTIME}`.", "",
        f"**900/900 games completed; zero runtime errors; nine full-cell replays matched.**", "",
        f"Splinter: **{s['wins']}/{s['games']} ({s['win_rate']:.2%})**, mean ending turn {s['mean_turn']}, median {s['median_turn']}.", "",
        "| Opponent | Wins | Games | Splinter WR | Mean turn |", "| --- | ---: | ---: | ---: | ---: |",
    ]
    for opp, row in s["by_opponent"].items():
        lines.append(f"| {opp} | {row['wins']} | {row['games']} | {row['win_rate']:.2%} | {row['mean_turn']:.2f} |")
    lines += ["", "Mechanic counts are execution telemetry, not causal evidence. This isolated result does not promote a baseline or authorize combined validation."]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "artifact": str(OUTPUT), "report": str(REPORT), "games": 900, "candidate_sha256": sha(CANDIDATE)}))


if __name__ == "__main__":
    main()
