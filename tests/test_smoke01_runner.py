from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tmnt_design_studio.smoke01 import (
    _mechanical_label,
    build_smoke_manifest,
    execute_smoke,
    plan,
    smoke_games,
    validate_smoke_result,
)
from tmnt_design_studio.stage002 import stable_digest

ROOT = Path(__file__).resolve().parents[1]


def _snapshot(*, winner: int | None = 0, reached: bool = False) -> dict[str, object]:
    semantic_key = "oracle:0:0:fragment"
    occurrence = {
        "occurrence_id": "occurrence-1",
        "semantic_key": semantic_key,
        "object_id": "object-1",
        "limitations": ["unsupported"],
    }
    witness = {
        "witness_id": "witness-1",
        "occurrence_id": "occurrence-1",
        "cause_kind": "typed_event",
    }
    return {
        "winner": winner,
        "turn": 4,
        "phase": "combat",
        "step": "end_of_combat",
        "authoritative_state_fingerprint": "a" * 64,
        "rng": {"state_digest": "b" * 64},
        "stack": [],
        "priority": None,
        "pending_triggers": [],
        "players": [{"name": "a"}, {"name": "b"}],
        "events": [],
        "scry": [],
        "combat_damage": {"evidence": []},
        "lifelink": [],
        "hand_bottom_draw": [],
        "discard_draw": [],
        "activated_abilities": [],
        "food_activations": [],
        "sneak": [],
        "stage002_presence": [
            {
                "initial_object_id": "object-1",
                "object_ids": ["object-1"],
                "owner": 0,
                "card": "fixture",
                "is_token": False,
                "semantic_key": semantic_key,
                "oracle_fragment": "fragment",
                "zone_history": [],
            }
        ],
        "conformance": {
            "semantic_occurrences": [occurrence] if reached else [],
            "opportunity_witnesses": [witness] if reached else [],
            "opportunity_contexts": [],
            "executed_references": [],
            "stop_records": [],
        },
    }


def _manifest_for(snapshot: dict[str, object]) -> dict[str, object]:
    presence = snapshot["stage002_presence"][0]
    body = {
        "stage": "coverage-aware-engine-smoke-0.1",
        "decks": [
            {
                "cards": [
                    {
                        "fragments": [
                            {
                                "semantic_key": presence["semantic_key"],
                                "oracle_fragment": presence["oracle_fragment"],
                            }
                        ]
                    }
                ]
            }
        ],
        "distinct_game_count": 1,
        "execution_count": 2,
    }
    return {**body, "manifest_digest": stable_digest(body)}


def _resign_outer_digests(result: dict[str, object]) -> None:
    aggregate = result["aggregate"]
    aggregate["aggregate_digest"] = stable_digest(
        {key: value for key, value in aggregate.items() if key != "aggregate_digest"}
    )
    result["raw_artifact_body_digest"] = stable_digest(
        {key: value for key, value in result.items() if key != "raw_artifact_body_digest"}
    )


def _use_one_game(monkeypatch) -> None:
    one_game = smoke_games()[:1]
    monkeypatch.setattr("tmnt_design_studio.smoke01.smoke_games", lambda: one_game)
    monkeypatch.setattr("tmnt_design_studio.smoke01.REQUIRED_GAME_COUNT", 1)


def test_matrix_is_exact_and_collision_free():
    games = smoke_games()
    assert len(games) == 180
    assert len({game.game_id for game in games}) == 180
    assert len({game.pairing_id for game in games}) == 45
    assert {game.seed for game in games} == set(range(8001, 8091))
    assert games[0].game_id == "april_oneil--bebop_rocksteady:canonical:8001"
    assert games[-1].game_id == "shredder--splinter:reversed:8090"


def test_plan_reconstructs_frozen_inputs_without_creating_game(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("plan instantiated Game")

    monkeypatch.setattr("tmnt_design_studio.engine07.Game.__init__", forbidden)
    result = plan(ROOT)
    manifest = result["manifest"]
    assert result["authorized"] is False
    assert manifest["pairing_count"] == 45
    assert manifest["distinct_game_count"] == 180
    assert manifest["execution_count"] == 360
    assert manifest["manifest_digest"] == stable_digest(
        {key: value for key, value in manifest.items() if key != "manifest_digest"}
    )


def test_frozen_input_tampering_fails_manifest(monkeypatch):
    monkeypatch.setitem(
        __import__("tmnt_design_studio.smoke01", fromlist=["FROZEN_HASHES"]).FROZEN_HASHES,
        "cardcade/roster-0.2.json",
        "0" * 64,
    )
    with pytest.raises(ValueError, match="input mismatch"):
        build_smoke_manifest(ROOT)


@pytest.mark.parametrize(
    ("reached", "expected"),
    [
        (False, "mechanically_clean_coverage_complete"),
        (True, "mechanically_clean_coverage_limited"),
    ],
)
def test_mechanical_label_is_computed(reached, expected):
    snapshot = _snapshot(reached=reached)
    from tmnt_design_studio.stage002 import reconcile_snapshot

    report = reconcile_snapshot(smoke_games()[0], snapshot, _manifest_for(snapshot))
    assert _mechanical_label(report, snapshot) == expected


def test_incomplete_game_is_mechanically_invalid():
    snapshot = _snapshot(winner=None)
    from tmnt_design_studio.stage002 import reconcile_snapshot

    report = reconcile_snapshot(smoke_games()[0], snapshot, _manifest_for(snapshot))
    with pytest.raises(RuntimeError, match="invalid or incomplete"):
        _mechanical_label(report, snapshot)


def test_execute_serializes_both_duplicates_and_balance_boundary(monkeypatch, tmp_path):
    snapshot = _snapshot(reached=True)
    manifest = _manifest_for(snapshot)
    monkeypatch.setattr("tmnt_design_studio.smoke01.build_smoke_manifest", lambda _root: manifest)
    _use_one_game(monkeypatch)
    output = tmp_path / "result.json"
    failure = tmp_path / "failure.json"
    result = execute_smoke(
        ROOT,
        output=output,
        failure_output=failure,
        runner=lambda *_args: copy.deepcopy(snapshot),
    )
    report = result["aggregate"]["games"][0]
    assert report["duplicate_snapshots"]["first"] == report["duplicate_snapshots"]["second"]
    assert report["mechanical_label"] == "mechanically_clean_coverage_limited"
    assert result["aggregate"]["future_balance_candidate_games"] == []
    assert not failure.exists()
    assert output.exists() and output.with_suffix(".json.sha256").exists()
    validate_smoke_result(result)


def test_duplicate_tampering_fails_independent_validation(monkeypatch, tmp_path):
    snapshot = _snapshot()
    monkeypatch.setattr(
        "tmnt_design_studio.smoke01.build_smoke_manifest", lambda _root: _manifest_for(snapshot)
    )
    _use_one_game(monkeypatch)
    result = execute_smoke(
        ROOT,
        output=tmp_path / "result.json",
        failure_output=tmp_path / "failure.json",
        runner=lambda *_args: copy.deepcopy(snapshot),
    )
    result["aggregate"]["games"][0]["duplicate_snapshots"]["second"]["turn"] = 99
    _resign_outer_digests(result)
    with pytest.raises(ValueError, match="duplicate evidence"):
        validate_smoke_result(result)


def test_failure_is_atomic_and_preserves_active_execution(monkeypatch, tmp_path):
    snapshot = _snapshot()
    monkeypatch.setattr(
        "tmnt_design_studio.smoke01.build_smoke_manifest", lambda _root: _manifest_for(snapshot)
    )
    _use_one_game(monkeypatch)
    output = tmp_path / "result.json"
    failure = tmp_path / "failure.json"

    def fail(*_args):
        raise RuntimeError("probe stop")

    with pytest.raises(RuntimeError, match="probe stop"):
        execute_smoke(
            ROOT,
            output=output,
            failure_output=failure,
            runner=fail,
        )
    artifact = json.loads(failure.read_text(encoding="utf-8"))
    assert artifact["accepted_aggregate"] is False
    assert artifact["active_execution"]["game_id"] == smoke_games()[0].game_id
    assert artifact["active_execution"]["duplicate_member"] == "first"
    assert artifact["active_execution"]["completed_distinct_game_count"] == 0
    assert not output.exists()


def test_balance_projection_tampering_fails_validation(monkeypatch, tmp_path):
    snapshot = _snapshot(reached=True)
    monkeypatch.setattr(
        "tmnt_design_studio.smoke01.build_smoke_manifest", lambda _root: _manifest_for(snapshot)
    )
    _use_one_game(monkeypatch)
    result = execute_smoke(
        ROOT,
        output=tmp_path / "result.json",
        failure_output=tmp_path / "failure.json",
        runner=lambda *_args: copy.deepcopy(snapshot),
    )
    result["aggregate"]["future_balance_candidate_games"] = [
        {"game_id": smoke_games()[0].game_id, "balance_valid": True}
    ]
    _resign_outer_digests(result)
    with pytest.raises(ValueError, match="leaked"):
        validate_smoke_result(result)


def test_reconciled_classification_tampering_fails_even_with_resigned_outer_digests(
    monkeypatch, tmp_path
):
    snapshot = _snapshot(reached=True)
    monkeypatch.setattr(
        "tmnt_design_studio.smoke01.build_smoke_manifest", lambda _root: _manifest_for(snapshot)
    )
    _use_one_game(monkeypatch)
    result = execute_smoke(
        ROOT,
        output=tmp_path / "result.json",
        failure_output=tmp_path / "failure.json",
        runner=lambda *_args: copy.deepcopy(snapshot),
    )
    result["aggregate"]["games"][0]["occurrences"][0]["classification"] = "executed"
    _resign_outer_digests(result)
    with pytest.raises(ValueError, match="not reconstructive"):
        validate_smoke_result(result)
