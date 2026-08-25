from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from tmnt_design_studio.engine07 import CardFact, Game, TurnStep, phase_for_step
from tmnt_design_studio.smoke01 import SmokeGameFailure
from tmnt_design_studio.stage002 import canonical_json, stable_digest
from tmnt_design_studio.stage02 import (
    _aggregate,
    _fingerprint_from_preimage,
    _game_spec_from_report,
    _original_event_evidence_stops,
    _report_for,
    build_stage02_manifest,
    commitment_directory_for,
    execute_stage02,
    load_and_validate_result,
    load_execution_commitments,
    plan,
    stage02_games,
    validate_failure_artifact,
    validate_stage02_result,
)

ROOT = Path(__file__).resolve().parents[1]


def _refresh_authority(snapshot: dict[str, object], winner_index: int | None) -> None:
    players = snapshot["players"]
    preimage = {
        "scheme": "engine07-authoritative-state-fingerprint-preimage-v1",
        "turn": snapshot["turn"],
        "active_player_index": 0,
        "step": snapshot["step"],
        "stack_object_ids": [item["object_id"] for item in snapshot["stack"]],
        "combat_attacker_ids": [],
        "combat_blocks": [],
        "players": [
            {
                "library_object_ids": [
                    f"p{index}-library-{item}" for item in range(player["library"])
                ],
                "hand_object_ids": [f"p{index}-hand-{item}" for item in range(len(player["hand"]))],
                "battlefield_object_ids": [item["object_id"] for item in player["battlefield"]],
                "graveyard_object_ids": [
                    f"p{index}-graveyard-{item}" for item in range(len(player["graveyard"]))
                ],
                "life": player["life"],
                "lost": player["lost"],
                "failed_draw_pending": player["failed_draw_pending"],
            }
            for index, player in enumerate(players)
        ],
        "rng_state_digest": snapshot["rng"]["state_digest"],
        "winner_index": winner_index,
    }
    snapshot["authoritative_state_fingerprint_preimage"] = preimage
    snapshot["authoritative_state_fingerprint"] = _fingerprint_from_preimage(preimage)
    for index, player in enumerate(snapshot["players"]):
        authority = preimage["players"][index]
        player["library_object_ids"] = list(authority["library_object_ids"])
        player["hand_object_ids"] = list(authority["hand_object_ids"])
        player["graveyard_object_ids"] = list(authority["graveyard_object_ids"])


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
    players = [
        {
            "name": "a",
            "life": 20,
            "library": 40,
            "library_object_ids": [f"p0-library-{item}" for item in range(40)],
            "lost": False,
            "loss_reason": None,
            "failed_draw_pending": False,
            "hand": [],
            "hand_object_ids": [],
            "battlefield": [],
            "graveyard": [],
            "graveyard_object_ids": [],
        },
        {
            "name": "b",
            "life": 20,
            "library": 40,
            "library_object_ids": [f"p1-library-{item}" for item in range(40)],
            "lost": False,
            "loss_reason": None,
            "failed_draw_pending": False,
            "hand": [],
            "hand_object_ids": [],
            "battlefield": [],
            "graveyard": [],
            "graveyard_object_ids": [],
        },
    ]
    events = []
    serialized_winner = None
    if winner is not None:
        loser = 1 - winner
        players[loser]["life"] = 0
        players[loser]["lost"] = True
        players[loser]["loss_reason"] = "life_zero_or_less"
        serialized_winner = players[winner]["name"]
        events.append(
            {
                "event": "player_lost",
                "player": players[loser]["name"],
                "reason": "life_zero_or_less",
            }
        )
    snapshot = {
        "winner": serialized_winner,
        "turn": 4 if winner is not None else 120,
        "phase": "combat",
        "step": "end_of_combat",
        "active_player": "a",
        "rng": {"state_digest": "b" * 64},
        "stack": [],
        "priority": None,
        "pending_triggers": [],
        "rules_event_evidence": [],
        "players": players,
        "events": events,
        "scry": [],
        "etb_drain_gain_scry": [],
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
    _refresh_authority(snapshot, winner)
    return snapshot


def _add_original_event(snapshot: dict[str, object]) -> None:
    record = {
        "event_id": "event-000001",
        "event_cursor": 1,
        "kind": "creature_entered",
        "player_index": 0,
        "subject_ids": ["object-1"],
        "source_id": "object-1",
        "target_player": None,
        "amount": None,
        "turn": 4,
        "step": "precombat_main",
        "active_player": 0,
        "battlefield_authority": [{"object_id": "object-1", "controller": 0}],
        "battlefield_characteristics": [
            {"object_id": "object-1", "controller": 0, "type_line": "Artifact Creature"}
        ],
        "last_known_battlefield": [],
    }
    ledger = {
        "event": "rules_event",
        "event_id": "event-000001",
        "rules_event": "creature_entered",
        "player": "a",
        "subject_ids": ["object-1"],
        "source_id": "object-1",
        "target_player": None,
        "amount": None,
        "event_turn": 4,
        "event_step": "precombat_main",
        "event_active_player": 0,
        "battlefield_authority": [{"object_id": "object-1", "controller": 0}],
        "battlefield_characteristics": [
            {"object_id": "object-1", "controller": 0, "type_line": "Artifact Creature"}
        ],
        "last_known_battlefield": [],
    }
    snapshot["rules_event_evidence"] = [record]
    snapshot["events"].append(ledger)


def _one_game_manifest(snapshot: dict[str, object]) -> dict[str, object]:
    game = stage02_games()[0]
    presence = snapshot["stage002_presence"][0]
    body = {
        "stage": "coverage-aware-engine-validation-0.2",
        "schema_version": "coverage-aware-engine-validation-0.2-evidence-v1",
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
        "games": [
            {
                "game_id": game.game_id,
                "pairing_id": game.pairing_id,
                "seed": game.seed,
                "orientation": game.orientation,
                "seats": [seat.display_id for seat in game.seats],
            }
        ],
        "pairing_count": 1,
        "seed_assignment_count": 1,
        "distinct_game_count": 1,
        "execution_count": 2,
    }
    return {**body, "manifest_digest": stable_digest(body)}


def _one_game(monkeypatch, snapshot: dict[str, object]) -> dict[str, object]:
    game = stage02_games()[0]
    manifest = _one_game_manifest(snapshot)
    monkeypatch.setattr("tmnt_design_studio.stage02.stage02_games", lambda: (game,))
    monkeypatch.setattr("tmnt_design_studio.stage02.REQUIRED_PAIRING_COUNT", 1)
    monkeypatch.setattr("tmnt_design_studio.stage02.REQUIRED_SEED_ASSIGNMENT_COUNT", 1)
    monkeypatch.setattr("tmnt_design_studio.stage02.REQUIRED_GAME_COUNT", 1)
    monkeypatch.setattr("tmnt_design_studio.stage02.REQUIRED_EXECUTION_COUNT", 2)
    monkeypatch.setattr("tmnt_design_studio.stage02.build_stage02_manifest", lambda _root: manifest)
    return manifest


def _resign(result: dict[str, object]) -> None:
    aggregate = result["aggregate"]
    aggregate["aggregate_digest"] = stable_digest(
        {key: value for key, value in aggregate.items() if key != "aggregate_digest"}
    )
    result["raw_artifact_body_digest"] = stable_digest(
        {key: value for key, value in result.items() if key != "raw_artifact_body_digest"}
    )


def _execute_one(monkeypatch, tmp_path, snapshot=None):
    snapshot = _snapshot(reached=True) if snapshot is None else snapshot
    _one_game(monkeypatch, snapshot)
    return execute_stage02(
        ROOT,
        output=tmp_path / "result.json",
        failure_output=tmp_path / "failure.json",
        runner=lambda *_args: copy.deepcopy(snapshot),
    )


def _commitments(tmp_path):
    directory = commitment_directory_for(tmp_path / "result.json")
    records = load_execution_commitments(directory) if directory.exists() else []
    return records, directory


def _validate_result(result, tmp_path):
    commitments, directory = _commitments(tmp_path)
    validate_stage02_result(result, ROOT, commitments=commitments, commitment_directory=directory)


def _validate_failure(artifact, tmp_path):
    commitments, directory = _commitments(tmp_path)
    validate_failure_artifact(artifact, commitments=commitments, commitment_directory=directory)


def test_matrix_is_exact_collision_free_and_uses_five_seed_allocations():
    games = stage02_games()
    assert len(games) == 450
    assert len({game.game_id for game in games}) == 450
    assert len({game.pairing_id for game in games}) == 45
    assert {game.seed for game in games} == set(range(9001, 9226))
    assert games[0].game_id == "april_oneil--bebop_rocksteady:canonical:9001"
    assert games[-1].game_id == "shredder--splinter:reversed:9225"
    assignments = {(game.pairing_id, game.seed) for game in games}
    assert len(assignments) == 225
    assert all(
        len({seed for pairing_id, seed in assignments if pairing_id == pairing}) == 5
        for pairing in {game.pairing_id for game in games}
    )


def test_plan_reconstructs_45_225_450_900_without_game_or_rng(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("plan instantiated Game or gameplay RNG")

    monkeypatch.setattr("tmnt_design_studio.engine07.Game.__init__", forbidden)
    monkeypatch.setattr("random.Random.__init__", forbidden)
    result = plan(ROOT)
    manifest = result["manifest"]
    assert result["authorized"] is False
    assert manifest["pairing_count"] == 45
    assert manifest["seed_assignment_count"] == 225
    assert manifest["distinct_game_count"] == 450
    assert manifest["execution_count"] == 900
    assert manifest["balance_policy"]["balance_valid"] is False


def test_plan_manifest_is_deterministic_and_frozen_inputs_reconstruct():
    first = build_stage02_manifest(ROOT)
    second = build_stage02_manifest(ROOT)
    assert first == second
    assert first["manifest_digest"] == stable_digest(
        {key: value for key, value in first.items() if key != "manifest_digest"}
    )
    assert first["hashing_contract"]["version"] == "smoke-frozen-input-hashing-v2"


def test_engine_snapshot_exposes_exact_existing_authoritative_fingerprint_preimage():
    land = CardFact("Audit Land", "", 0, "Basic Land — Plains")
    current = Game(([land] * 60, [land] * 60), seed=77)
    snapshot = current.snapshot()
    preimage = snapshot["authoritative_state_fingerprint_preimage"]
    assert preimage == current.authoritative_state_fingerprint_evidence()
    assert _fingerprint_from_preimage(preimage) == current.authoritative_state_fingerprint()
    assert snapshot["authoritative_state_fingerprint"] == current.authoritative_state_fingerprint()


@pytest.mark.parametrize("step", list(TurnStep))
def test_authenticated_step_requires_the_engine_canonical_phase(step):
    snapshot = _snapshot()
    snapshot["step"] = step.value
    snapshot["phase"] = phase_for_step(step)
    _refresh_authority(snapshot, 0)
    from tmnt_design_studio.stage02 import _authoritative_state_stops

    assert not _authoritative_state_stops(snapshot)
    snapshot["phase"] = next(
        value
        for value in {phase_for_step(item) for item in TurnStep}
        if value != phase_for_step(step)
    )
    assert "authoritative-state phase does not derive from authenticated step" in (
        _authoritative_state_stops(snapshot)
    )


def test_original_event_evidence_reconstructs_and_rejects_tampering():
    snapshot = _snapshot()
    _add_original_event(snapshot)
    assert not _original_event_evidence_stops(snapshot)
    snapshot["rules_event_evidence"][0]["battlefield_characteristics"][0]["type_line"] = "Creature"
    assert _original_event_evidence_stops(snapshot)


def test_execute_preserves_duplicates_classification_aggregates_and_balance(monkeypatch, tmp_path):
    result = _execute_one(monkeypatch, tmp_path)
    report = result["aggregate"]["games"][0]
    assert report["duplicate_snapshots"]["first"] == report["duplicate_snapshots"]["second"]
    assert report["distinct_game_weight"] == 1
    assert report["duplicate_execution_count"] == 2
    assert report["mechanical_label"] == "mechanically_clean_coverage_limited"
    assert report["balance"]["balance_valid"] is False
    assert result["aggregate"]["balance_valid"] is False
    assert result["aggregate"]["distinct_game_count"] == 1
    assert result["aggregate"]["execution_count"] == 2
    _validate_result(result, tmp_path)


def test_terminal_outcome_is_reconstructed_and_resigned_false_winner_fails(monkeypatch, tmp_path):
    result = _execute_one(monkeypatch, tmp_path, _snapshot(winner=0))
    report = result["aggregate"]["games"][0]
    for snapshot in report["duplicate_snapshots"].values():
        snapshot["winner"] = "b"
    spec = _game_spec_from_report(report)
    with pytest.raises(RuntimeError, match="authoritative state evidence failure"):
        _report_for(spec, report["duplicate_snapshots"], result["manifest"])
    _resign(result)
    with pytest.raises(ValueError):
        _validate_result(result, tmp_path)


@pytest.mark.parametrize(
    ("zone", "mutation"),
    [
        ("library_object_ids", lambda values: ["substitute", *values[1:]]),
        ("library_object_ids", lambda values: list(reversed(values))),
        ("hand_object_ids", lambda values: ["substitute", *values[1:]]),
        ("graveyard_object_ids", lambda values: ["substitute", *values[1:]]),
    ],
)
def test_resigned_hidden_zone_substitution_fails_independent_commitment(
    monkeypatch, tmp_path, zone, mutation
):
    snapshot = _snapshot(winner=0)
    snapshot["players"][0]["hand"] = ["fixture"]
    snapshot["players"][0]["hand_object_ids"] = ["p0-hand-0"]
    snapshot["players"][0]["graveyard"] = ["fixture"]
    snapshot["players"][0]["graveyard_object_ids"] = ["p0-graveyard-0"]
    _refresh_authority(snapshot, 0)
    result = _execute_one(monkeypatch, tmp_path, snapshot)
    report = result["aggregate"]["games"][0]
    for member_snapshot in report["duplicate_snapshots"].values():
        values = member_snapshot["authoritative_state_fingerprint_preimage"]["players"][0][zone]
        member_snapshot["authoritative_state_fingerprint_preimage"]["players"][0][zone] = mutation(
            values
        )
        member_snapshot["players"][0][zone] = list(
            member_snapshot["authoritative_state_fingerprint_preimage"]["players"][0][zone]
        )
        member_snapshot["authoritative_state_fingerprint"] = _fingerprint_from_preimage(
            member_snapshot["authoritative_state_fingerprint_preimage"]
        )
    report["duplicate_execution_digests"] = {
        member: hashlib.sha256(canonical_json(value).encode()).hexdigest()
        for member, value in report["duplicate_snapshots"].items()
    }
    spec = _game_spec_from_report(report)
    reconstructed = _report_for(spec, report["duplicate_snapshots"], result["manifest"])
    result["aggregate"] = _aggregate([reconstructed], result["manifest"])
    _resign(result)
    with pytest.raises(ValueError, match="independent commitments"):
        _validate_result(result, tmp_path)


def test_coordinated_terminal_projection_substitution_fails_authority_join(monkeypatch, tmp_path):
    result = _execute_one(monkeypatch, tmp_path, _snapshot(winner=0))
    report = result["aggregate"]["games"][0]
    for snapshot in report["duplicate_snapshots"].values():
        snapshot["winner"] = "b"
        snapshot["players"][0].update({"life": 0, "lost": True, "loss_reason": "life_zero_or_less"})
        snapshot["players"][1].update({"life": 20, "lost": False, "loss_reason": None})
        loss = next(event for event in snapshot["events"] if event["event"] == "player_lost")
        loss.update({"player": "a", "reason": "life_zero_or_less"})
    spec = _game_spec_from_report(report)
    with pytest.raises(RuntimeError, match="authoritative state evidence failure"):
        _report_for(spec, report["duplicate_snapshots"], result["manifest"])


def test_preimage_and_fingerprint_tampering_remains_joined_to_snapshot(monkeypatch, tmp_path):
    result = _execute_one(monkeypatch, tmp_path, _snapshot(winner=0))
    report = result["aggregate"]["games"][0]
    for snapshot in report["duplicate_snapshots"].values():
        snapshot["authoritative_state_fingerprint_preimage"]["winner_index"] = 1
    spec = _game_spec_from_report(report)
    with pytest.raises(RuntimeError, match="fingerprint does not reconstruct"):
        _report_for(spec, report["duplicate_snapshots"], result["manifest"])
    for snapshot in report["duplicate_snapshots"].values():
        snapshot["authoritative_state_fingerprint"] = _fingerprint_from_preimage(
            snapshot["authoritative_state_fingerprint_preimage"]
        )
    with pytest.raises(RuntimeError, match="winner projection disagrees"):
        _report_for(spec, report["duplicate_snapshots"], result["manifest"])


@pytest.mark.parametrize("winner", [0, 1])
def test_legitimate_terminal_outcomes_authenticate(monkeypatch, tmp_path, winner):
    result = _execute_one(monkeypatch, tmp_path, _snapshot(winner=winner))
    _validate_result(result, tmp_path)
    assert result["aggregate"]["games"][0]["winner"] == ("a" if winner == 0 else "b")


def test_legitimate_failed_draw_terminal_outcome_authenticates(monkeypatch, tmp_path):
    snapshot = _snapshot(winner=0)
    loser = snapshot["players"][1]
    loser["life"] = 20
    loser["library"] = 0
    loser["loss_reason"] = "draw_from_empty_library"
    snapshot["events"][0]["reason"] = "draw_from_empty_library"
    _refresh_authority(snapshot, 0)
    result = _execute_one(monkeypatch, tmp_path, snapshot)
    _validate_result(result, tmp_path)
    assert result["aggregate"]["games"][0]["winner"] == "a"


@pytest.mark.parametrize(
    "attack",
    [
        "matrix_seed",
        "duplicate_identity",
        "mechanical_classification",
        "aggregate_membership",
        "semantic_classification",
        "original_event_evidence",
        "balance_valid",
        "frozen_input",
    ],
)
def test_resigned_adversarial_tampering_fails(monkeypatch, tmp_path, attack):
    snapshot = _snapshot(reached=True)
    if attack == "original_event_evidence":
        _add_original_event(snapshot)
    manifest = _one_game(monkeypatch, snapshot)
    result = execute_stage02(
        ROOT,
        output=tmp_path / "result.json",
        failure_output=tmp_path / "failure.json",
        runner=lambda *_args: copy.deepcopy(snapshot),
    )
    report = result["aggregate"]["games"][0]
    if attack == "matrix_seed":
        result["manifest"]["games"][0]["seed"] += 1
        result["manifest"]["manifest_digest"] = stable_digest(
            {key: value for key, value in result["manifest"].items() if key != "manifest_digest"}
        )
    elif attack == "duplicate_identity":
        report["duplicate_snapshots"]["second"]["turn"] += 1
        report["duplicate_execution_digests"]["second"] = hashlib.sha256(
            json.dumps(
                report["duplicate_snapshots"]["second"],
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
    elif attack == "mechanical_classification":
        report["mechanical_label"] = "mechanically_clean_coverage_complete"
    elif attack == "aggregate_membership":
        labels = result["aggregate"]["mechanical_labels"]
        labels["mechanically_clean_coverage_complete"] = [report["game_id"]]
        labels["mechanically_clean_coverage_limited"] = []
    elif attack == "semantic_classification":
        report["occurrences"][0]["classification"] = "executed"
    elif attack == "original_event_evidence":
        for member in ("first", "second"):
            member_snapshot = report["duplicate_snapshots"][member]
            member_snapshot["rules_event_evidence"][0]["battlefield_authority"] = []
        report["duplicate_execution_digests"] = {
            member: hashlib.sha256(
                json.dumps(snapshot_value, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            for member, snapshot_value in report["duplicate_snapshots"].items()
        }
    elif attack == "balance_valid":
        report["balance"]["balance_valid"] = True
        result["aggregate"]["balance_valid"] = True
        result["aggregate"]["balance_records"][0]["balance_valid"] = True
    elif attack == "frozen_input":
        result["manifest"]["decks"] = []
        result["manifest"]["manifest_digest"] = stable_digest(
            {key: value for key, value in result["manifest"].items() if key != "manifest_digest"}
        )
    _resign(result)
    with pytest.raises(ValueError):
        _validate_result(result, tmp_path)
    assert manifest["distinct_game_count"] == 1


def test_turn_cap_without_winner_fails_closed_without_draw_or_success(monkeypatch, tmp_path):
    snapshot = _snapshot(winner=None)
    _one_game(monkeypatch, snapshot)
    output = tmp_path / "result.json"
    failure = tmp_path / "failure.json"
    with pytest.raises(RuntimeError, match="invalid or incomplete"):
        execute_stage02(
            ROOT,
            output=output,
            failure_output=failure,
            runner=lambda *_args: copy.deepcopy(snapshot),
        )
    assert not output.exists()
    artifact = json.loads(failure.read_text(encoding="utf-8"))
    _validate_failure(artifact, tmp_path)
    assert artifact["last_authoritative_state"]["turn"] == 120
    assert artifact["last_authoritative_state"]["winner"] is None
    assert artifact["status"] == "failed"


def test_preflight_failure_is_atomic_and_has_sidecar(monkeypatch, tmp_path):
    def fail(_root):
        raise ValueError("frozen input drift")

    monkeypatch.setattr("tmnt_design_studio.stage02.build_stage02_manifest", fail)
    failure = tmp_path / "failure.json"
    with pytest.raises(ValueError, match="frozen input drift"):
        execute_stage02(
            ROOT,
            output=tmp_path / "result.json",
            failure_output=failure,
        )
    artifact = json.loads(failure.read_text(encoding="utf-8"))
    _validate_failure(artifact, tmp_path)
    assert failure.with_suffix(".json.sha256").exists()
    assert artifact["active_execution"]["stage"] == "manifest_preflight"


def test_inherited_smoke_failure_preserves_authoritative_snapshot(monkeypatch, tmp_path):
    snapshot = _snapshot(winner=None)
    _one_game(monkeypatch, snapshot)
    failure = tmp_path / "failure.json"

    def fail(*_args):
        raise SmokeGameFailure("bounded game failure", copy.deepcopy(snapshot))

    with pytest.raises(SmokeGameFailure):
        execute_stage02(
            ROOT,
            output=tmp_path / "result.json",
            failure_output=failure,
            runner=fail,
        )
    artifact = json.loads(failure.read_text(encoding="utf-8"))
    _validate_failure(artifact, tmp_path)
    assert artifact["available_duplicate_snapshots"] == {"first": snapshot}
    assert artifact["last_authoritative_snapshot"] == snapshot
    assert artifact["last_authoritative_state"]["turn"] == 120


def test_second_commitment_write_failure_keeps_first_and_removes_partial_current(
    monkeypatch, tmp_path
):
    snapshot = _snapshot()
    _one_game(monkeypatch, snapshot)
    output = tmp_path / "result.json"
    failure = tmp_path / "failure.json"
    from tmnt_design_studio.smoke01 import _atomic_write as accepted_atomic_write

    def fail_second_commitment(path, payload):
        if path.name == "execution-0002.json":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("partial", encoding="utf-8")
            raise PermissionError("commitment denied")
        return accepted_atomic_write(path, payload)

    monkeypatch.setattr("tmnt_design_studio.stage02._atomic_write", fail_second_commitment)
    with pytest.raises(PermissionError, match="commitment denied"):
        execute_stage02(
            ROOT,
            output=output,
            failure_output=failure,
            runner=lambda *_args: copy.deepcopy(snapshot),
        )
    directory = commitment_directory_for(output)
    records = load_execution_commitments(directory)
    assert [record["execution_ordinal"] for record in records] == [1]
    assert not (directory / "execution-0002.json").exists()
    artifact = json.loads(failure.read_text(encoding="utf-8"))
    validate_failure_artifact(artifact, commitments=records, commitment_directory=directory)
    assert artifact["active_execution"]["stage"] == "execution_commitment_persistence"


@pytest.mark.parametrize(
    "attack",
    [
        "audit4_orphan_sidecar",
        "orphan_json",
        "missing_json",
        "missing_sidecar",
        "unexpected_file",
        "temporary_residue",
        "extra_ordinal_pair",
        "alternate_ordinal_encoding",
        "alternate_filename",
        "unexpected_directory",
    ],
)
def test_commitment_directory_requires_exact_inventory(monkeypatch, tmp_path, attack):
    _execute_one(monkeypatch, tmp_path, _snapshot(winner=0))
    directory = commitment_directory_for(tmp_path / "result.json")
    assert len(load_execution_commitments(directory)) == 2

    if attack == "audit4_orphan_sidecar":
        (directory / "execution-0003.json.sha256").write_text(
            "partial sidecar without JSON\n", encoding="ascii"
        )
    elif attack == "orphan_json":
        (directory / "execution-0003.json").write_text("{}\n", encoding="utf-8")
    elif attack == "missing_json":
        (directory / "execution-0002.json").unlink()
    elif attack == "missing_sidecar":
        (directory / "execution-0002.json.sha256").unlink()
    elif attack == "unexpected_file":
        (directory / "README.txt").write_text("unexpected\n", encoding="utf-8")
    elif attack == "temporary_residue":
        (directory / ".execution-0003.json.tmp").write_text("partial", encoding="utf-8")
    elif attack == "extra_ordinal_pair":
        (directory / "execution-0003.json").write_text("{}\n", encoding="utf-8")
        (directory / "execution-0003.json.sha256").write_text("invalid\n", encoding="ascii")
    elif attack == "alternate_ordinal_encoding":
        (directory / "execution-003.json").write_text("{}\n", encoding="utf-8")
        (directory / "execution-003.json.sha256").write_text("invalid\n", encoding="ascii")
    elif attack == "alternate_filename":
        (directory / "commitment-0003.json").write_text("{}\n", encoding="utf-8")
    elif attack == "unexpected_directory":
        (directory / "execution-0003.json").mkdir()

    with pytest.raises(ValueError, match="inventory|authenticate|ordering"):
        load_execution_commitments(directory)
    with pytest.raises(ValueError):
        load_and_validate_result(tmp_path / "result.json", ROOT)


def test_fully_authenticated_extra_commitment_is_not_in_the_execution_sequence(
    monkeypatch, tmp_path
):
    _execute_one(monkeypatch, tmp_path, _snapshot(winner=0))
    directory = commitment_directory_for(tmp_path / "result.json")
    records = load_execution_commitments(directory)
    extra = copy.deepcopy(records[-1])
    extra["execution_ordinal"] = 3
    extra["commitment_digest"] = stable_digest(
        {key: value for key, value in extra.items() if key != "commitment_digest"}
    )
    from tmnt_design_studio.smoke01 import _atomic_write as accepted_atomic_write

    accepted_atomic_write(directory / "execution-0003.json", extra)
    assert len(load_execution_commitments(directory)) == 3
    with pytest.raises(ValueError, match="commitment references"):
        load_and_validate_result(tmp_path / "result.json", ROOT)


def test_resigned_inherited_snapshot_substitution_fails_authority_reconstruction(
    monkeypatch, tmp_path
):
    snapshot = _snapshot(winner=None)
    _one_game(monkeypatch, snapshot)
    failure = tmp_path / "failure.json"

    def fail(*_args):
        raise SmokeGameFailure("bounded game failure", copy.deepcopy(snapshot))

    with pytest.raises(SmokeGameFailure):
        execute_stage02(
            ROOT,
            output=tmp_path / "result.json",
            failure_output=failure,
            runner=fail,
        )
    artifact = json.loads(failure.read_text(encoding="utf-8"))
    substitute = copy.deepcopy(snapshot)
    substitute["turn"] = 119
    artifact["available_duplicate_snapshots"] = {"first": substitute}
    artifact["available_duplicate_digests"] = {
        "first": hashlib.sha256(
            json.dumps(substitute, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    }
    artifact["last_authoritative_snapshot"] = substitute
    artifact["last_authoritative_state"]["turn"] = 119
    artifact["failure_body_digest"] = stable_digest(
        {key: value for key, value in artifact.items() if key != "failure_body_digest"}
    )
    with pytest.raises(ValueError, match="authoritative state does not reconstruct"):
        _validate_failure(artifact, tmp_path)


def test_late_aggregate_failure_preserves_completed_duplicate_evidence(monkeypatch, tmp_path):
    snapshot = _snapshot()
    _one_game(monkeypatch, snapshot)
    failure = tmp_path / "failure.json"

    def fail_aggregate(*_args):
        raise ValueError("forced aggregate failure")

    monkeypatch.setattr("tmnt_design_studio.stage02._aggregate", fail_aggregate)
    with pytest.raises(ValueError, match="forced aggregate failure"):
        execute_stage02(
            ROOT,
            output=tmp_path / "result.json",
            failure_output=failure,
            runner=lambda *_args: copy.deepcopy(snapshot),
        )
    artifact = json.loads(failure.read_text(encoding="utf-8"))
    _validate_failure(artifact, tmp_path)
    assert len(artifact["completed_game_evidence"]) == 1
    assert set(artifact["completed_game_evidence"][0]["duplicate_snapshots"]) == {
        "first",
        "second",
    }
    assert artifact["last_authoritative_snapshot"] == snapshot


def test_resigned_late_failure_report_stripping_fails_reconstruction(monkeypatch, tmp_path):
    snapshot = _snapshot(reached=True)
    _one_game(monkeypatch, snapshot)
    failure = tmp_path / "failure.json"

    def fail_aggregate(*_args):
        raise ValueError("forced aggregate failure")

    monkeypatch.setattr("tmnt_design_studio.stage02._aggregate", fail_aggregate)
    with pytest.raises(ValueError, match="forced aggregate failure"):
        execute_stage02(
            ROOT,
            output=tmp_path / "result.json",
            failure_output=failure,
            runner=lambda *_args: copy.deepcopy(snapshot),
        )
    artifact = json.loads(failure.read_text(encoding="utf-8"))
    report = artifact["completed_game_evidence"][0]
    for field in (
        "occurrences",
        "classification_sets",
        "opportunity_contexts",
        "opportunity_witnesses",
    ):
        report.pop(field)
    report["report_digest"] = stable_digest(report)
    artifact["completed_game_digests"][0]["report_digest"] = report["report_digest"]
    artifact["failure_body_digest"] = stable_digest(
        {key: value for key, value in artifact.items() if key != "failure_body_digest"}
    )
    with pytest.raises(ValueError, match="not authentic"):
        _validate_failure(artifact, tmp_path)


def test_final_success_serialization_failure_removes_success_and_preserves_failure(
    monkeypatch, tmp_path
):
    snapshot = _snapshot()
    _one_game(monkeypatch, snapshot)
    output = tmp_path / "result.json"
    failure = tmp_path / "failure.json"
    from tmnt_design_studio.smoke01 import _atomic_write as accepted_atomic_write

    def fail_success(path, payload):
        if path == output:
            path.write_text("partial success", encoding="utf-8")
            raise PermissionError("sidecar denied")
        return accepted_atomic_write(path, payload)

    monkeypatch.setattr("tmnt_design_studio.stage02._atomic_write", fail_success)
    with pytest.raises(PermissionError, match="sidecar denied"):
        execute_stage02(
            ROOT,
            output=output,
            failure_output=failure,
            runner=lambda *_args: copy.deepcopy(snapshot),
        )
    assert not output.exists()
    assert not output.with_suffix(".json.sha256").exists()
    artifact = json.loads(failure.read_text(encoding="utf-8"))
    _validate_failure(artifact, tmp_path)
    assert artifact["active_execution"]["stage"] == "final_success_serialization"
    assert artifact["accepted_aggregate"] is False
    assert len(artifact["completed_game_evidence"]) == 1
    assert artifact["last_authoritative_snapshot"] == snapshot


def test_failure_artifact_cannot_be_resigned_as_success():
    snapshot = _snapshot(winner=None)
    artifact = {
        "stage": "coverage-aware-engine-validation-0.2",
        "schema_version": "coverage-aware-engine-validation-0.2-evidence-v1",
        "status": "failed",
        "accepted_aggregate": False,
        "success_artifact_valid": False,
        "balance_valid": False,
        "manifest_digest": None,
        "manifest": None,
        "active_execution": {
            "stage": "game_execution",
            "game_id": "game",
            "pairing_id": "pairing",
            "seed": 9001,
            "orientation": "canonical",
            "duplicate_member": "first",
            "execution_ordinal": 1,
            "completed_distinct_game_count": 0,
        },
        "failure": {"kind": "SmokeGameFailure", "message": "stop", "traceback": "trace"},
        "completed_game_digests": [],
        "completed_game_evidence": [],
        "available_duplicate_digests": {
            "first": hashlib.sha256(
                json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
        },
        "available_duplicate_snapshots": {"first": snapshot},
        "last_authoritative_snapshot": snapshot,
        "last_authoritative_state": {
            "turn": snapshot["turn"],
            "phase": snapshot["phase"],
            "step": snapshot["step"],
            "winner": snapshot["winner"],
            "state_fingerprint": snapshot["authoritative_state_fingerprint"],
            "stack": snapshot["stack"],
            "priority": snapshot["priority"],
            "pending_triggers": snapshot["pending_triggers"],
            "invariant_violations": [],
        },
    }
    artifact["failure_body_digest"] = stable_digest(artifact)
    with pytest.raises(ValueError, match="commitment"):
        validate_failure_artifact(artifact)
    artifact["available_duplicate_snapshots"] = {}
    artifact["available_duplicate_digests"] = {}
    artifact["last_authoritative_snapshot"] = None
    artifact["last_authoritative_state"] = None
    artifact["active_execution"].update(
        {"stage": "manifest_preflight", "game_id": None, "pairing_id": None}
    )
    artifact["failure_body_digest"] = stable_digest(
        {key: value for key, value in artifact.items() if key != "failure_body_digest"}
    )
    validate_failure_artifact(artifact)
    artifact["aggregate"] = {"games": []}
    artifact["accepted_aggregate"] = True
    artifact["failure_body_digest"] = stable_digest(
        {key: value for key, value in artifact.items() if key != "failure_body_digest"}
    )
    with pytest.raises(ValueError, match="masquerade"):
        validate_failure_artifact(artifact)


def test_resigned_stripped_failure_evidence_is_rejected(monkeypatch, tmp_path):
    snapshot = _snapshot(winner=None)
    _one_game(monkeypatch, snapshot)
    failure = tmp_path / "failure.json"

    def fail(*_args):
        raise SmokeGameFailure("bounded game failure", copy.deepcopy(snapshot))

    with pytest.raises(SmokeGameFailure):
        execute_stage02(
            ROOT,
            output=tmp_path / "result.json",
            failure_output=failure,
            runner=fail,
        )
    artifact = json.loads(failure.read_text(encoding="utf-8"))
    artifact["available_duplicate_snapshots"] = {}
    artifact["available_duplicate_digests"] = {}
    artifact["last_authoritative_snapshot"] = None
    artifact["last_authoritative_state"] = None
    artifact["failure_body_digest"] = stable_digest(
        {key: value for key, value in artifact.items() if key != "failure_body_digest"}
    )
    with pytest.raises(ValueError, match="commitment|lost its authoritative snapshot"):
        _validate_failure(artifact, tmp_path)


def test_raw_artifacts_are_rejected_inside_repository(monkeypatch, tmp_path):
    snapshot = _snapshot()
    _one_game(monkeypatch, snapshot)
    with pytest.raises(ValueError, match="outside ordinary repository history"):
        execute_stage02(
            ROOT,
            output=ROOT / "docs" / "cardcade" / "forbidden-result.json",
            failure_output=tmp_path / "failure.json",
            runner=lambda *_args: copy.deepcopy(snapshot),
        )
