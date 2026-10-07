"""Read-only independent authentication of the frozen R8-A combined matrix."""

# Long cross-artifact assertions are intentional.
# ruff: noqa: E501

from __future__ import annotations

import gzip
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
CONTROL = OBL / "BASELINE_004_R8A_ETB_RUNTIME_CONTROL.json.gz"
CANDIDATE = OBL / "ROUND_8_A_EVIDENCE.json.gz"
MANIFEST = OBL / "combined/OBL_COMBINED_007_MANIFEST.json"
EVIDENCE = OBL / "COMBINED_007_R8A_EVIDENCE.json.gz"
READINESS = OBL / "ROUND_8_A_SEMANTIC_READINESS.json"
BASE_MANIFEST = OBL / "baselines/OBL_BASELINE_004_MANIFEST.json"
RUNTIME = "d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924"
CANDIDATE_SHA = "aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed"
DECK = "bebop_rocksteady"


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(value: object) -> str:
    return sha(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    )


def load(path: Path) -> dict:
    return (
        json.loads(gzip.decompress(path.read_bytes()))
        if path.suffix == ".gz"
        else json.loads(path.read_text())
    )


def by_cell(games: list[dict]) -> dict[tuple[str, str], list[dict]]:
    result = defaultdict(list)
    for game in games:
        result[tuple(sorted(game["schedule"]["pair"]))].append(game)
    return dict(result)


def rate(games: list[dict], deck: str) -> float:
    return round(
        (sum(g["winner"] == deck for g in games) + sum(g["draw"] for g in games) / 2) / len(games),
        6,
    )


def validate() -> dict:
    control, candidate, manifest, evidence = (
        load(path) for path in (CONTROL, CANDIDATE, MANIFEST, EVIDENCE)
    )
    readiness, baseline_manifest = load(READINESS), load(BASE_MANIFEST)
    assert manifest["environment_id"] == evidence["environment_id"] == "OBL-COMBINED-007"
    assert manifest["parent_environment"] == evidence["parent_environment"] == "OBL-BASELINE-004"
    assert manifest["state"] == evidence["state"] == "EXPERIMENTAL_COMBINED_ENVIRONMENT"
    assert manifest["selected_experiments"] == ["OBL-R8-BEBOP-A"]
    assert evidence["candidate_experiment"] == "OBL-R8-BEBOP-A"
    assert (
        manifest["accepted_isolated_record"]
        == evidence["accepted_isolated_record"]
        == {
            "pull_request": "https://github.com/egggggman/tmt/pull/275",
            "merge_commit": "75133aecde12f0dc979424e324debc465021c788",
        }
    )
    assert (
        manifest["semantic_runtime_sha256"]
        == evidence["semantic_runtime_sha256"]
        == control["semantic_runtime_sha256"]
        == candidate["semantic_runtime_sha256"]
        == readiness["semantic_runtime_sha256"]
        == RUNTIME
    )
    assert (
        manifest["schedule_sha256"]
        == evidence["schedule_sha256"]
        == control["schedule_sha256"]
        == candidate["schedule_sha256"]
    )
    assert (
        manifest["baseline_manifest_sha256"]
        == control["baseline_manifest_sha256"]
        == candidate["baseline_manifest_sha256"]
        == sha(BASE_MANIFEST.read_bytes())
    )
    assert (
        manifest["candidate_sha256"]
        == candidate["candidate_deck_sha256"]
        == readiness["candidate_sha256"]
        == CANDIDATE_SHA
    )
    assert sha((ROOT / readiness["candidate_path"]).read_bytes()) == CANDIDATE_SHA
    assert sha(CONTROL.read_bytes()) == candidate["runtime_control_sha256"]
    assert evidence["manifest_sha256"] == sha(MANIFEST.read_bytes())
    assert evidence["manifest_path"] == MANIFEST.relative_to(ROOT).as_posix()
    assert (
        sha(READINESS.read_bytes()) == control["readiness_sha256"] == candidate["readiness_sha256"]
    )
    assert control["status"] == candidate["status"] == "COMPLETE"
    assert (
        control["runtime_errors"] == candidate["runtime_errors"] == evidence["runtime_errors"] == 0
    )
    assert len(control["games"]) == 4500 and len(candidate["games"]) == 900
    assert (
        len(evidence["combined_games"])
        == evidence["logical_games"]
        == manifest["logical_games"]
        == 4500
    )
    assert evidence["logical_matchups"] == manifest["logical_matchups"] == 45
    assert manifest["reused_games"] == evidence["reused_games"] == 4500
    assert manifest["newly_executed_games"] == evidence["newly_executed_games"] == 0
    assert manifest["promotion_authorized"] is evidence["promotion_authorized"] is False
    assert evidence["handoff"] == "RETURN_TO_DESIGN_STUDIO_HQ_FOR_PROMOTION_DECISION"
    assert (
        manifest["source_artifact_sha256"]
        == evidence["source_artifact_sha256"]
        == {
            "BASELINE_004_REUSED": sha(CONTROL.read_bytes()),
            "ROUND_8_A_REUSED": sha(CANDIDATE.read_bytes()),
        }
    )
    original = {row["deck_key"]: row for row in baseline_manifest["decks"]}
    selected = {row["deck_key"]: row for row in manifest["decks"]}
    assert set(original) == set(selected) and len(selected) == 10
    for deck, row in selected.items():
        assert row["parent_baseline_sha256"] == original[deck]["sha256"]
        if deck == DECK:
            assert row["source_path"] == readiness["candidate_path"]
            assert row["sha256"] == CANDIDATE_SHA
            assert row["selection"] == "OBL-R8-BEBOP-A"
            assert (
                row["exact_diff"]
                == readiness["exact_diff"]
                == {
                    "removals": {"Illegitimate Business": 2},
                    "additions": {"Primordial Pachyderm": 2},
                }
            )
        else:
            assert row["selection"] == "OBL-BASELINE-004"
            assert row["source_path"] == original[deck]["source_path"]
            assert row["sha256"] == original[deck]["sha256"]
            assert row["exact_diff"] == {"removals": {}, "additions": {}}
    old, new, combined = (
        by_cell(games)
        for games in (control["games"], candidate["games"], evidence["combined_games"])
    )
    assert len(old) == len(combined) == 45 and len(new) == 9
    assert set(new) == {pair for pair in old if DECK in pair}
    assert len(evidence["provenance"]) == 45
    provenance = {tuple(sorted(row["decks"])): row for row in evidence["provenance"]}
    assert set(provenance) == set(old)
    assert evidence["provenance_counts"] == {"BASELINE_004_REUSED": 36, "ROUND_8_A_REUSED": 9}
    for pair, old_games in old.items():
        source_name = "ROUND_8_A_REUSED" if pair in new else "BASELINE_004_REUSED"
        source = new.get(pair, old_games)
        payload = candidate if pair in new else control
        row = provenance[pair]
        assert combined[pair] == source and len(source) == 100
        assert Counter(game["first_player"] for game in source) == {pair[0]: 50, pair[1]: 50}
        assert all(game["runtime_error"] is None and game["runtime_fingerprint"] for game in source)
        assert row["source"] == source_name
        assert row["source_artifact"] == manifest["source_artifacts"][source_name]
        assert row["source_artifact_sha256"] == manifest["source_artifact_sha256"][source_name]
        assert row["semantic_runtime_sha256"] == RUNTIME
        assert row["schedule_sha256"] == manifest["schedule_sha256"]
        assert row["deck_sha256"] == {deck: selected[deck]["sha256"] for deck in pair}
        assert row["orientation_counts"] == {"canonical": 50, "reversed": 50}
        assert row["game_count"] == 100
        cell_key = "|".join(source[0]["schedule"]["pair"])
        assert row["cell_sha256"] == payload["cell_hashes"][cell_key] == digest(source)
        if pair in new:
            assert candidate["replays"][cell_key] == digest(source)
    assert [game["schedule"] for game in evidence["combined_games"]] == [
        game["schedule"] for game in control["games"]
    ]
    assert len(candidate["replays"]) == 9 and len(control["replays"]) == 6
    for games, rows, deck_summary, global_metrics in (
        (
            control["games"],
            evidence["baseline_matchups"],
            evidence["baseline_deck_summary"],
            evidence["baseline_global_metrics"],
        ),
        (
            evidence["combined_games"],
            evidence["combined_matchups"],
            evidence["combined_deck_summary"],
            evidence["combined_global_metrics"],
        ),
    ):
        cells = by_cell(games)
        assert len(rows) == 45
        deviations = []
        for row in rows:
            pair = tuple(row["decks"])
            assert row["games"] == 100
            for deck in pair:
                assert row["win_rates"][deck] == rate(cells[pair], deck)
            assert row["deviation"] == round(abs(row["win_rates"][pair[0]] - 0.5), 6)
            deviations.append(row["deviation"])
        assert global_metrics["mean_matchup_balance_error"] == round(statistics.mean(deviations), 6)
        assert global_metrics["median_matchup_deviation"] == round(statistics.median(deviations), 6)
        assert global_metrics["over_60_40"] == sum(value > 0.1 for value in deviations)
        assert global_metrics["over_70_30"] == sum(value > 0.2 for value in deviations)
        assert global_metrics["mean_ending_turn"] == round(
            statistics.mean(game["turn"] for game in games), 4
        )
        assert global_metrics["median_ending_turn"] == statistics.median(
            game["turn"] for game in games
        )
        for deck in selected:
            involved = [game for game in games if deck in game["seats"]]
            assert len(involved) == 900
            assert deck_summary[deck]["win_rate"] == rate(involved, deck)
        rates = [deck_summary[deck]["win_rate"] for deck in selected]
        assert global_metrics["aggregate_win_rate_spread"] == round(max(rates) - min(rates), 6)
        assert global_metrics["aggregate_win_rate_stddev"] == round(statistics.pstdev(rates), 6)
    for key, delta in evidence["global_delta"].items():
        assert delta == round(
            evidence["combined_global_metrics"][key] - evidence["baseline_global_metrics"][key], 6
        )
    for opponent, expected in {
        "raphael": (11, 23),
        "shredder": (13, 19),
        "splinter": (12, 29),
        "casey_jones": (16, 26),
        "donatello": (39, 54),
        "leonardo": (31, 35),
        "krang": (27, 54),
        "april_oneil": (36, 55),
    }.items():
        pair = tuple(sorted((DECK, opponent)))
        assert (
            round(rate(old[pair], DECK) * 100),
            round(rate(combined[pair], DECK) * 100),
        ) == expected
    return {
        "acceptance": "PASS_COMBINED_INDEPENDENT_READ_ONLY",
        "environment_id": evidence["environment_id"],
        "cells": len(combined),
        "games": len(evidence["combined_games"]),
        "global_delta": evidence["global_delta"],
    }


if __name__ == "__main__":
    print(json.dumps(validate()))
