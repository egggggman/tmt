"""Run the OBL-COMBINED-001 45-matchup validation matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

# The evidence payload keeps compact aggregation expressions for reproducibility.
# ruff: noqa: E501

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402

OBL = ROOT / "docs/objective-balance-lab"
MANIFEST_PATH = OBL / "combined/OBL_COMBINED_001_MANIFEST.json"
R1_PATH = OBL / "ROUND_1_EVIDENCE.json"
OUTPUT = OBL / "COMBINED_001_EVIDENCE.json"
DECKS = r1.DECKS


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matchup_rates(games: list[dict], deck: str) -> dict[str, float]:
    result = {}
    for opponent in DECKS:
        if opponent == deck:
            continue
        subset = [game for game in games if deck in game["seats"] and opponent in game["seats"]]
        wins = sum(game["winner"] == deck for game in subset)
        draws = sum(game["draw"] for game in subset)
        result[opponent] = round((wins + draws / 2) / len(subset), 6)
    return result


def balance_error(rates: dict[str, float]) -> float:
    return round(sum(abs(rate - 0.5) for rate in rates.values()) / len(rates), 6)


def extremes(rates: dict[str, float]) -> dict[str, object]:
    worst = max(rates, key=lambda key: abs(rates[key] - 0.5))
    strongest = max(rates, key=rates.get)
    weakest = min(rates, key=rates.get)
    return {
        "worst_matchup": worst,
        "worst_matchup_win_rate": rates[worst],
        "strongest_matchup": strongest,
        "strongest_matchup_win_rate": rates[strongest],
        "weakest_matchup": weakest,
        "weakest_matchup_win_rate": rates[weakest],
        "over_60_40": sum(rate > 0.6 or rate < 0.4 for rate in rates.values()),
        "over_70_30": sum(rate > 0.7 or rate < 0.3 for rate in rates.values()),
    }


def signature_average(games: list[dict], deck: str) -> float:
    values = [
        sum(
            value
            for key, value in game.get("signature_casts", {}).items()
            if key.startswith(deck + ":")
        )
        for game in games
    ]
    return round(statistics.mean(values), 4) if values else 0


def summarize(games: list[dict], deck: str) -> dict[str, object]:
    own = [game for game in games if deck in game["seats"]]
    aggregate = r1.aggregate(games, (deck,))[deck]
    rates = matchup_rates(games, deck)
    return {
        **aggregate,
        "matchup_win_rates": rates,
        "mean_matchup_balance_error": balance_error(rates),
        "median_matchup_deviation": statistics.median(abs(rate - 0.5) for rate in rates.values()),
        "extremes": extremes(rates),
        "signature_casts_average": signature_average(own, deck),
        "runtime_errors": sum(bool(game.get("runtime_error")) for game in own),
    }


def run_matrix(
    paths: dict[str, str], schedule: list[dict], cards: dict[str, dict], workers: int
) -> list[dict]:
    r1._init_worker(cards)
    payloads = [(index, paths, item) for index, item in enumerate(schedule, 1)]
    results = []
    with ProcessPoolExecutor(
        max_workers=workers, initializer=r1._init_worker, initargs=(cards,)
    ) as executor:
        for index, result in enumerate(executor.map(r1._run_one, payloads, chunksize=1), 1):
            results.append(result)
            if index % 250 == 0:
                print(f"completed {index}/{len(schedule)}", flush=True)
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    round1 = json.loads(R1_PATH.read_text(encoding="utf-8"))
    cards = r1.catalog()
    schedule = r1.schedule()
    if manifest["environment_id"] != "OBL-COMBINED-001":
        raise SystemExit("unexpected combined environment identity")
    if len(schedule) != 4500 or schedule != round1["schedule"]:
        raise SystemExit("combined schedule is not the frozen 4,500-game schedule")
    paths = {}
    for selected in manifest["selected_decks"]:
        path = ROOT / selected["source_path"]
        if sha(path) != selected["selected_sha256"]:
            raise SystemExit(f"selected file hash mismatch: {path}")
        r1.validate_deck(path, cards)
        paths[selected["deck_key"]] = selected["source_path"]
    if set(paths) != set(DECKS):
        raise SystemExit("combined manifest does not contain exactly ten decks")
    checkpoint = OUTPUT.with_name("COMBINED_001_EVIDENCE.checkpoint.json")
    combined_results = run_matrix(paths, schedule, cards, args.workers)
    payload = {
        "schema": "objective-balance-lab-combined-environment-v1",
        "environment_id": "OBL-COMBINED-001",
        "state": "EXPERIMENTAL_COMBINED_ENVIRONMENT",
        "repository_sha": "0017d9d3b65d57474789ef24471deb615a9b1e54",
        "manifest_path": MANIFEST_PATH.relative_to(ROOT).as_posix(),
        "manifest_sha256": sha(MANIFEST_PATH),
        "parent_environment_id": "OBL-BASELINE-000",
        "baseline_evidence_path": R1_PATH.relative_to(ROOT).as_posix(),
        "baseline_evidence_sha256": sha(R1_PATH),
        "schedule_sha256": hashlib.sha256(
            json.dumps(schedule, sort_keys=True).encode()
        ).hexdigest(),
        "schedule_games": len(schedule),
        "combined_results": combined_results,
        "counts": {
            "baseline_games_reused": len(round1["baseline_results"]),
            "combined_games": len(combined_results),
            "runtime_errors": sum(bool(game.get("runtime_error")) for game in combined_results),
        },
    }
    checkpoint.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    payload["baseline_summary"] = {
        deck: summarize(round1["baseline_results"], deck) for deck in DECKS
    }
    payload["combined_summary"] = {deck: summarize(combined_results, deck) for deck in DECKS}
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
