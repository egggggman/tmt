"""Run OBL Round 2 candidates against the frozen Round 1 baseline schedule."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402

R1_EVIDENCE = ROOT / "docs/objective-balance-lab/ROUND_1_EVIDENCE.json"
R2_DIR = ROOT / "docs/objective-balance-lab/candidates"
CANDIDATES = {
    deck: {
        "A": f"docs/objective-balance-lab/candidates/{deck.upper()}_OBL_R2_A.txt",
        "B": f"docs/objective-balance-lab/candidates/{deck.upper()}_OBL_R2_B.txt",
    }
    for deck in r1.DECKS
}


def candidate_schedule(deck: str) -> list[dict[str, object]]:
    return [item for item in r1.schedule() if deck in item["pair"]]


def matchup_rates(games: list[dict[str, object]], deck: str) -> dict[str, float]:
    result = {}
    for opponent in r1.DECKS:
        if opponent == deck:
            continue
        subset = [
            game for game in games if deck in game["seats"] and opponent in game["seats"]
        ]
        wins = sum(game["winner"] == deck for game in subset)
        draws = sum(game["draw"] for game in subset)
        result[opponent] = round((wins + draws / 2) / len(subset), 6) if subset else None
    return result


def balance_error(rates: dict[str, float]) -> float:
    return round(sum(abs(value - 0.5) for value in rates.values()) / len(rates), 6)


def own_summary(games: list[dict[str, object]], deck: str) -> dict[str, object]:
    return r1.aggregate(games, (deck,))[deck]


def summary(games: list[dict[str, object]], deck: str) -> dict[str, object]:
    rates = matchup_rates(games, deck)
    own = own_summary(games, deck)
    return {
        **own,
        "matchup_win_rates": rates,
        "mean_matchup_balance_error": balance_error(rates),
        "runtime_errors": sum(bool(game.get("runtime_error")) for game in games),
    }


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_round1() -> dict[str, object]:
    return json.loads(R1_EVIDENCE.read_text(encoding="utf-8"))


def validate_schedule(evidence: dict[str, object]) -> None:
    expected = r1.schedule()
    actual = evidence.get("schedule")
    if actual != expected:
        raise SystemExit("Round 1 schedule differs from the frozen schedule")
    if len(evidence.get("baseline_results", [])) != 4500:
        raise SystemExit("Round 1 baseline evidence is not exactly 4,500 games")
    if sum(len(value) for value in evidence.get("candidate_results", {}).values()) != 9000:
        raise SystemExit("Round 1 candidate evidence is not exactly 9,000 games")
    if any(game.get("runtime_error") for game in evidence["baseline_results"]):
        raise SystemExit("Round 1 baseline contains runtime errors")
    if any(
        game.get("runtime_error")
        for games in evidence["candidate_results"].values()
        for game in games
    ):
        raise SystemExit("Round 1 candidate evidence contains runtime errors")


def validate_candidates(cards: dict[str, dict[str, object]]) -> dict[str, object]:
    manifests = {}
    for deck in r1.DECKS:
        parent = r1.validate_deck(ROOT / r1.PARENT[deck], cards)
        variants = {}
        for label, relative in CANDIDATES[deck].items():
            path = ROOT / relative
            manifest = r1.validate_deck(path, cards)
            manifest["diff"] = r1.diff(parent["cards"], manifest["cards"])
            if sum(abs(row["candidate"] - row["parent"]) for row in manifest["diff"].values()) > 8:
                raise SystemExit(f"{path}: more than four changed card slots")
            variants[label] = manifest
        manifests[deck] = {"parent": parent, "candidates": variants}
    return manifests


def run_variant(deck: str, label: str, cards: dict[str, dict[str, object]], workers: int):
    paths = dict(r1.PARENT)
    paths[deck] = CANDIDATES[deck][label]
    return deck, label, r1.run_set(paths, candidate_schedule(deck), cards, max(1, workers))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--workers", type=int, default=20)
    args = parser.parse_args()

    cards = r1.catalog()
    round1 = load_round1()
    validate_schedule(round1)
    manifests = validate_candidates(cards)
    payload = {
        "schema": "objective-balance-lab-round-2-v1",
        "main": "63b303b8853d7919a2f683eb8b215e20374e5606",
        "round1_evidence_sha256": sha(R1_EVIDENCE),
        "snapshot": {"path": r1.SNAPSHOT.relative_to(ROOT).as_posix(), "sha256": sha(r1.SNAPSHOT)},
        "schedule_sha256": hashlib.sha256(
            json.dumps(round1["schedule"], sort_keys=True).encode()
        ).hexdigest(),
        "manifests": manifests,
        "candidate_schedule_games": {deck: len(candidate_schedule(deck)) for deck in r1.DECKS},
    }
    if args.validate_only:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 0
    if args.output is None:
        raise SystemExit("--output is required for simulation")

    checkpoint = args.output.with_name(args.output.stem + ".checkpoint.json")
    results: dict[str, dict[str, list[dict[str, object]]]] = {}
    tasks = [(deck, label) for deck in r1.DECKS for label in ("A", "B")]
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = [executor.submit(run_variant, deck, label, cards, max(1, args.workers // 20)) for deck, label in tasks]
        for future in futures:
            deck, label, games = future.result()
            results.setdefault(deck, {})[label] = games
            checkpoint_payload = {**payload, "candidate_results": results}
            checkpoint.write_text(json.dumps(checkpoint_payload, indent=2) + "\n", encoding="utf-8")

    payload["candidate_results"] = results
    payload["baseline_summary"] = round1["baseline_summary"]
    payload["round1_candidate_summary"] = round1["candidate_summary"]
    payload["candidate_summary"] = {
        deck: {label: summary(games, deck) for label, games in variants.items()}
        for deck, variants in results.items()
    }
    payload["counts"] = {
        "baseline_games_reused": len(round1["baseline_results"]),
        "candidate_games": sum(len(games) for variants in results.values() for games in variants.values()),
        "total_experimental_games": sum(len(games) for variants in results.values() for games in variants.values()),
        "runtime_errors": sum(
            bool(game.get("runtime_error"))
            for variants in results.values()
            for games in variants.values()
            for game in games
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
