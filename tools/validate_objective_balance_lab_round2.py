"""Integrity and deterministic replay checks for OBL Round 2 evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round2 as r2  # noqa: E402


def main() -> None:
    evidence = json.loads((ROOT / "docs/objective-balance-lab/ROUND_2_EVIDENCE.json").read_text(encoding="utf-8"))
    round1 = json.loads((ROOT / "docs/objective-balance-lab/ROUND_1_EVIDENCE.json").read_text(encoding="utf-8"))
    cards = r1.catalog()
    assert evidence["main"] == "63b303b8853d7919a2f683eb8b215e20374e5606"
    assert evidence["schedule_sha256"]
    assert evidence["candidate_schedule_games"] == dict.fromkeys(r1.DECKS, 900)
    assert len(round1["baseline_results"]) == 4500
    assert sum(len(games) for games in round1["candidate_results"].values()) == 9000
    assert evidence["counts"] == {
        "baseline_games_reused": 4500,
        "candidate_games": 18000,
        "total_experimental_games": 18000,
        "runtime_errors": 0,
    }
    expected_schedule = r1.schedule()
    assert evidence["candidate_results"].keys() == set(r1.DECKS)
    for deck in r1.DECKS:
        expected = r2.candidate_schedule(deck)
        for label in ("A", "B"):
            games = evidence["candidate_results"][deck][label]
            assert len(games) == 900
            assert not any(game.get("runtime_error") for game in games)
            assert all(game.get("runtime_fingerprint") for game in games)
            assert [game["schedule"] for game in games] == expected
            manifest = evidence["manifests"][deck]["candidates"][label]
            assert sum(manifest["cards"].values()) == 60
            assert len(manifest["diff"]) <= 4
            assert sum(abs(change["candidate"] - change["parent"]) for change in manifest["diff"].values()) <= 8
            r1.validate_deck(ROOT / manifest["path"], cards)
    assert evidence["candidate_results"]["leonardo"]["A"][0]["schedule"] in expected_schedule

    # Re-run one sealed game per candidate to verify the stored fingerprints and orientation.
    r1._init_worker(cards)
    replayed = 0
    for deck in r1.DECKS:
        for label in ("A", "B"):
            item = evidence["candidate_results"][deck][label][0]["schedule"]
            paths = dict(r1.PARENT)
            paths[deck] = r2.CANDIDATES[deck][label]
            replay = r1._run_one((0, paths, item))
            assert replay["runtime_error"] is None
            assert replay["runtime_fingerprint"] == evidence["candidate_results"][deck][label][0]["runtime_fingerprint"]
            replayed += 1

    roles = json.loads((ROOT / "docs/objective-balance-lab/CARD_ROLE_EVIDENCE.json").read_text(encoding="utf-8"))
    assert roles["records"]
    assert all(record["semantic_support"] for record in roles["records"])
    print(json.dumps({"candidate_slices": 20, "candidate_games": 18000, "replayed_fingerprints": replayed, "runtime_errors": 0}))


if __name__ == "__main__":
    main()
