"""Read-only, independent authentication of the R7-A combined matrix."""

# Long, explicit cross-artifact assertions are intentional.
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
CONTROL = OBL / "BASELINE_003_R7A_SEMANTIC_CONTROL.json.gz"
CANDIDATE = OBL / "ROUND_7_A_EVIDENCE.json.gz"
MANIFEST = OBL / "combined/OBL_COMBINED_006_MANIFEST.json"
EVIDENCE = OBL / "COMBINED_006_R7A_EVIDENCE.json.gz"
RUNTIME = "f40c4888ef9128d03819fc1be86dde1316b2115fd0d4fb365cd03b288453afa1"
CANDIDATE_SHA = "2d598af2d05212ffb0f19fe5f315b7bf8f85501975155f394448b0a48fa81ab1"


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
    cells = defaultdict(list)
    for game in games:
        cells[tuple(sorted(game["schedule"]["pair"]))].append(game)
    return dict(cells)


def win_rate(games: list[dict], deck: str) -> float:
    return round(
        (sum(g["winner"] == deck for g in games) + sum(g["draw"] for g in games) / 2) / len(games),
        6,
    )


def validate() -> dict:
    control, candidate, manifest, evidence = (
        load(path) for path in (CONTROL, CANDIDATE, MANIFEST, EVIDENCE)
    )
    readiness = load(OBL / "ROUND_7_A_SEMANTIC_READINESS.json")
    base_manifest = load(OBL / "baselines/OBL_BASELINE_003_MANIFEST.json")
    assert manifest["environment_id"] == evidence["environment_id"] == "OBL-COMBINED-006"
    assert manifest["parent_environment"] == evidence["parent_environment"] == "OBL-BASELINE-003"
    assert manifest["state"] == evidence["state"] == "EXPERIMENTAL_COMBINED_ENVIRONMENT"
    assert manifest["selected_experiments"] == ["OBL-R7-KRANG-A"]
    assert evidence["candidate_experiment"] == "OBL-R7-KRANG-A"
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
    assert manifest["baseline_manifest_sha256"] == sha(
        (OBL / "baselines/OBL_BASELINE_003_MANIFEST.json").read_bytes()
    )
    assert (
        control["baseline_manifest_sha256"]
        == candidate["baseline_manifest_sha256"]
        == manifest["baseline_manifest_sha256"]
    )
    assert (
        manifest["candidate_sha256"]
        == candidate["candidate_sha256"]
        == readiness["candidate_sha256"]
        == CANDIDATE_SHA
    )
    assert sha((ROOT / candidate["candidate_path"]).read_bytes()) == CANDIDATE_SHA
    assert sha(CONTROL.read_bytes()) == candidate["control_sha256"]
    assert evidence["manifest_sha256"] == sha(MANIFEST.read_bytes())
    assert evidence["manifest_path"] == MANIFEST.relative_to(ROOT).as_posix()
    assert (
        sha((OBL / "ROUND_7_A_SEMANTIC_READINESS.json").read_bytes())
        == control["readiness_sha256"]
        == candidate["readiness_sha256"]
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
            "BASELINE_003_REUSED": sha(CONTROL.read_bytes()),
            "ROUND_7_A_REUSED": sha(CANDIDATE.read_bytes()),
        }
    )
    base_decks = {row["deck_key"]: row for row in base_manifest["decks"]}
    selected = {row["deck_key"]: row for row in manifest["decks"]}
    assert set(base_decks) == set(selected) and len(selected) == 10
    for deck, row in selected.items():
        assert row["parent_baseline_sha256"] == base_decks[deck]["sha256"]
        if deck == "krang":
            assert row["source_path"] == candidate["candidate_path"]
            assert row["sha256"] == CANDIDATE_SHA
            assert row["selection"] == "OBL-R7-KRANG-A"
            assert row["exact_diff"] == {
                "removals": {"Does Machines": 1, "Negate": 1},
                "additions": {"Ray Fillet, Man Ray": 1, "Stockman, Mad Fly-entist": 1},
            }
        else:
            assert row["selection"] == "OBL-BASELINE-003"
            assert row["source_path"] == base_decks[deck]["source_path"]
            assert row["sha256"] == base_decks[deck]["sha256"]
            assert row["exact_diff"] == {"removals": {}, "additions": {}}

    old = by_cell(control["games"])
    new = by_cell(candidate["games"])
    combined = by_cell(evidence["combined_games"])
    assert len(old) == len(combined) == 45 and len(new) == 9
    assert set(new) == {pair for pair in old if "krang" in pair}
    assert len(evidence["provenance"]) == 45
    provenance = {tuple(sorted(row["decks"])): row for row in evidence["provenance"]}
    assert set(provenance) == set(old)
    assert evidence["provenance_counts"] == {"BASELINE_003_REUSED": 36, "ROUND_7_A_REUSED": 9}
    for pair, old_games in old.items():
        source_name = "ROUND_7_A_REUSED" if "krang" in pair else "BASELINE_003_REUSED"
        source = new.get(pair, old_games)
        payload = candidate if pair in new else control
        row = provenance[pair]
        assert combined[pair] == source
        assert len(source) == 100
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
    assert [g["schedule"] for g in evidence["combined_games"]] == [
        g["schedule"] for g in control["games"]
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
                assert row["win_rates"][deck] == win_rate(cells[pair], deck)
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
            assert deck_summary[deck]["win_rate"] == win_rate(involved, deck)
        rates = [deck_summary[deck]["win_rate"] for deck in selected]
        assert global_metrics["aggregate_win_rate_spread"] == round(max(rates) - min(rates), 6)
        assert global_metrics["aggregate_win_rate_stddev"] == round(statistics.pstdev(rates), 6)
    for key, delta in evidence["global_delta"].items():
        assert delta == round(
            evidence["combined_global_metrics"][key] - evidence["baseline_global_metrics"][key], 6
        )
    assert evidence["baseline_deck_summary"]["krang"]["win_rate"] == 0.345556
    assert evidence["combined_deck_summary"]["krang"]["win_rate"] == 0.387778
    return {
        "acceptance": "PASS_COMBINED_INDEPENDENT_READ_ONLY",
        "environment_id": evidence["environment_id"],
        "cells": len(combined),
        "games": len(evidence["combined_games"]),
        "runtime_errors": evidence["runtime_errors"],
        "global_delta": evidence["global_delta"],
    }


if __name__ == "__main__":
    print(json.dumps(validate()))
