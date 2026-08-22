from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

from tmnt_design_studio.card_interpreter07 import TokenCreationProgram, TokenDefinition
from tmnt_design_studio.engine07 import CardFact, Game
from tmnt_design_studio.stage002 import (
    PAIRINGS,
    DeckSpec,
    GameSpec,
    _add_created_token_presence,
    _checked_action,
    _finish_presence,
    _token_definition_identity,
    build_deck_manifest,
    build_stage_manifest,
    canonical_json,
    execute_stage,
    load_catalog,
    plan,
    reconcile_snapshot,
    run_game,
    stable_digest,
    stage_games,
)

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Plains", "", 0, "Basic Land — Plains", oracle_id="stage002-land")


def _token_game() -> Game:
    return Game(([LAND] * 60, [LAND] * 60), seed=83)


def _created_token_presence(definition: TokenDefinition) -> tuple[Game, list[dict[str, object]]]:
    current = _token_game()
    current.create_tokens(
        0,
        TokenCreationProgram(definition, 1),
        source_card="Stage 002 fixture",
        oracle_fragment="Create a fixture token.",
    )
    presence: list[dict[str, object]] = []
    _add_created_token_presence(current, presence, current.events)
    return current, presence


def _snapshot(*, context: bool = False, witness: bool = False) -> dict[str, object]:
    occurrence = {
        "occurrence_id": "semantic-1",
        "semantic_key": "known-key",
        "object_id": "object-1",
        "limitations": ["unsupported"],
    }
    return {
        "winner": "a",
        "turn": 3,
        "rng": {"state_digest": "rng"},
        "events": [],
        "activated_abilities": [],
        "food_activations": [],
        "sneak": [],
        "hand_bottom_draw": [],
        "discard_draw": [],
        "lifelink": [],
        "combat_damage": {"evidence": []},
        "stage002_presence": [
            {
                "initial_object_id": "object-1",
                "object_ids": ["object-1"],
                "owner": 0,
                "card": "Fixture",
                "semantic_key": "known-key",
                "oracle_fragment": "Fixture text",
                "zone_history": [{"zone": "library", "object_id": "object-1"}],
            }
        ],
        "conformance": {
            "semantic_occurrences": [occurrence],
            "opportunity_witnesses": (
                [
                    {
                        "witness_id": "witness-1",
                        "occurrence_id": "semantic-1",
                        "semantic_key": "known-key",
                        "cause_kind": "authoritative_context",
                        "cause_id": "context-1",
                    }
                ]
                if witness
                else []
            ),
            "opportunity_contexts": ([{"context_id": "context-1"}] if context else []),
            "executed_references": [],
            "stop_records": [],
        },
    }


def _manifest() -> dict[str, object]:
    return {
        "manifest_digest": "manifest",
        "decks": [
            {
                "cards": [
                    {
                        "fragments": [
                            {
                                "semantic_key": "known-key",
                                "oracle_fragment": "Fixture text",
                                "limitations": ["unsupported"],
                            }
                        ]
                    }
                ]
            }
        ],
    }


def _add_valid_execution(snapshot: dict[str, object], *, source_id: str = "object-1") -> None:
    snapshot["activated_abilities"] = [
        {
            "stack_object_id": "stack-1",
            "source_id": source_id,
            "oracle_fragment": "Fixture text",
            "resolved": True,
        }
    ]
    snapshot["conformance"]["executed_references"] = [
        {
            "semantic_key": "known-key",
            "oracle_fragment": "Fixture text",
            "evidence_kind": "activated_ability",
            "evidence_id": "stack-1",
            "source_id": source_id,
        }
    ]


def test_frozen_matrix_is_16_distinct_games_and_32_executions():
    games = stage_games()
    assert len(PAIRINGS) == 4
    assert len(games) == 16
    assert len({game.game_id for game in games}) == 16
    assert {(game.orientation, game.seed) for game in games} >= {
        ("canonical", 7201),
        ("reversed", 7201),
    }


def test_stage_manifest_freezes_all_eight_decks_and_is_deterministic():
    deck_paths = {ROOT / seat.relative_path for game in stage_games() for seat in game.seats}
    before = {path: path.read_bytes() for path in deck_paths}
    first = build_stage_manifest(ROOT)
    second = build_stage_manifest(ROOT)
    assert {path: path.read_bytes() for path in deck_paths} == before
    assert first == second
    assert first["distinct_game_count"] == 16
    assert first["execution_count_with_duplicates"] == 32
    assert len(first["decks"]) == 8
    assert all(deck["slot_count"] == 60 for deck in first["decks"])
    assert all(deck["represented_families"] for deck in first["decks"])
    assert all(deck["unsupported_families"] for deck in first["decks"])
    assert all(deck["acceptance_001_novelty"]["count"] > 0 for deck in first["decks"])
    assert first["manifest_digest"] == second["manifest_digest"]
    assert all(
        fragment["semantic_coverage"]["fully_supported"] == (not fragment["limitations"])
        for deck in first["decks"]
        for card in deck["cards"]
        for fragment in card["fragments"]
    )


def test_plan_never_executes_a_game():
    result = plan(ROOT)
    assert result["authorized"] is False
    assert result["manifest"]["distinct_game_count"] == 16


def test_manifest_maps_every_unsupported_fragment_to_producer_or_unobservable():
    manifest = build_stage_manifest(ROOT)
    unsupported = [
        fragment
        for deck in manifest["decks"]
        for card in deck["cards"]
        for fragment in card["fragments"]
        if fragment["limitations"]
    ]
    assert unsupported
    assert all(
        fragment["observability"]["status"] in {"bounded_producer", "opportunity_not_observable"}
        for fragment in unsupported
    )


def test_unwitnessed_text_stays_present_unreached():
    report = reconcile_snapshot(stage_games()[0], _snapshot(), _manifest())
    assert report["occurrences"][0]["classification"] == "present_unreached"
    assert report["presence"][0]["classification"] == "present_unreached"
    assert report["stop_records"] == []


def test_valid_context_promotes_only_its_witnessed_occurrence():
    report = reconcile_snapshot(
        stage_games()[0], _snapshot(context=True, witness=True), _manifest()
    )
    assert report["occurrences"][0]["classification"] == "reached_unsupported"
    assert report["stop_records"] == []


def test_orphan_authoritative_context_is_an_unclassified_reach_stop():
    report = reconcile_snapshot(stage_games()[0], _snapshot(context=True), _manifest())
    assert report["stop_records"] == [{"kind": "unclassified_reach", "detail": ["context-1"]}]


def test_unknown_runtime_semantic_is_a_silent_approximation_stop():
    snapshot = _snapshot()
    snapshot["conformance"]["semantic_occurrences"][0]["semantic_key"] = "unknown"
    report = reconcile_snapshot(stage_games()[0], snapshot, _manifest())
    assert report["stop_records"] == [{"kind": "silent_approximation", "detail": ["unknown"]}]


def test_missing_runtime_presence_is_a_silent_approximation_stop():
    snapshot = _snapshot()
    del snapshot["stage002_presence"]
    report = reconcile_snapshot(stage_games()[0], snapshot, _manifest())
    assert report["stop_records"] == [
        {"kind": "silent_approximation", "detail": ["presence_evidence_missing"]}
    ]


def test_genuine_transaction_authenticates_executed_class():
    snapshot = _snapshot()
    _add_valid_execution(snapshot)
    report = reconcile_snapshot(stage_games()[0], snapshot, _manifest())
    assert report["occurrences"][0]["classification"] == "executed"
    assert report["stop_records"] == []


@pytest.mark.parametrize(
    ("field", "value"),
    (("evidence_id", "fabricated"), ("evidence_kind", "wrong-kind")),
)
def test_fabricated_execution_identity_fails_closed_without_promotion(field, value):
    snapshot = _snapshot()
    _add_valid_execution(snapshot)
    snapshot["conformance"]["executed_references"][0][field] = value
    report = reconcile_snapshot(stage_games()[0], snapshot, _manifest())
    assert report["occurrences"][0]["classification"] == "present_unreached"
    assert report["authenticated_executed_references"] == []
    assert report["stop_records"][0]["kind"] == "silent_approximation"


def test_semantic_key_and_source_lineage_without_transaction_are_insufficient():
    snapshot = _snapshot()
    _add_valid_execution(snapshot)
    snapshot["activated_abilities"] = []
    report = reconcile_snapshot(stage_games()[0], snapshot, _manifest())
    assert report["occurrences"][0]["classification"] == "present_unreached"
    assert report["stop_records"][0]["kind"] == "silent_approximation"


def test_real_transaction_cannot_be_borrowed_by_another_source():
    snapshot = _snapshot()
    snapshot["stage002_presence"].append(
        {
            **snapshot["stage002_presence"][0],
            "initial_object_id": "object-2",
            "object_ids": ["object-2"],
        }
    )
    _add_valid_execution(snapshot, source_id="object-1")
    snapshot["conformance"]["executed_references"][0]["source_id"] = "object-2"
    report = reconcile_snapshot(stage_games()[0], snapshot, _manifest())
    assert report["occurrences"][0]["classification"] == "present_unreached"
    assert report["stop_records"][0]["kind"] == "silent_approximation"


def test_report_serialization_and_digest_are_deterministic():
    first = reconcile_snapshot(stage_games()[0], _snapshot(), _manifest())
    second = reconcile_snapshot(stage_games()[0], copy.deepcopy(_snapshot()), _manifest())
    assert canonical_json(first) == canonical_json(second)
    assert first["report_digest"] == stable_digest(
        {key: value for key, value in first.items() if key != "report_digest"}
    )


def test_execute_stage_runs_each_distinct_game_exactly_twice(monkeypatch):
    calls = []
    snapshot = _snapshot()
    monkeypatch.setattr(
        "tmnt_design_studio.stage002.build_stage_manifest", lambda _root: _manifest()
    )

    def runner(_root, spec, _pilot):
        calls.append(spec.game_id)
        return copy.deepcopy(snapshot)

    games = stage_games()[:2]
    result = execute_stage(ROOT, runner=runner, games=games)
    assert calls == [games[0].game_id, games[0].game_id, games[1].game_id, games[1].game_id]
    assert result["aggregate"]["distinct_game_count"] == 2
    assert result["aggregate"]["execution_count"] == 4


def test_execute_stage_fails_on_duplicate_mismatch(monkeypatch):
    monkeypatch.setattr(
        "tmnt_design_studio.stage002.build_stage_manifest", lambda _root: _manifest()
    )
    count = 0

    def runner(_root, _spec, _pilot):
        nonlocal count
        count += 1
        snapshot = _snapshot()
        snapshot["turn"] = count
        return snapshot

    with pytest.raises(RuntimeError, match="nondeterministic duplicate"):
        execute_stage(ROOT, runner=runner, games=stage_games()[:1])


def test_execute_stage_fails_on_invariant_or_conformance_stop(monkeypatch):
    monkeypatch.setattr(
        "tmnt_design_studio.stage002.build_stage_manifest", lambda _root: _manifest()
    )
    invariant = _snapshot()
    invariant["events"] = [{"event": "invariant_violation"}]
    with pytest.raises(RuntimeError, match="invariant violation"):
        execute_stage(ROOT, runner=lambda *_args: copy.deepcopy(invariant), games=stage_games()[:1])
    stopped = _snapshot(context=True)
    with pytest.raises(RuntimeError, match="unclassified_reach"):
        execute_stage(ROOT, runner=lambda *_args: copy.deepcopy(stopped), games=stage_games()[:1])


class _MutationProbe:
    def __init__(self):
        self.state = "before"
        self.stops = []

    def authoritative_state_fingerprint(self):
        return self.state

    def record_conformance_stop(self, kind, before, detail):
        self.stops.append((kind, before, self.state, detail))


def test_rejected_action_mutation_is_detected_and_recorded():
    game = _MutationProbe()

    def reject_after_mutation():
        game.state = "after"
        return False

    with pytest.raises(RuntimeError, match="illegal mutation"):
        _checked_action(game, reject_after_mutation, "probe")
    assert game.stops == [("illegal_mutation", "before", "after", "probe")]


def test_rejected_action_without_mutation_is_not_a_false_stop():
    game = _MutationProbe()
    assert _checked_action(game, lambda: False, "probe") is False
    assert game.stops == []


def test_stage_games_reference_only_frozen_design_paths():
    assert {seat.relative_path for game in stage_games() for seat in game.seats} == {
        "decks/donatello/PROTOTYPE_0.2.txt",
        "decks/krang/PROTOTYPE_0.2.txt",
        "decks/michelangelo/PROTOTYPE_0.1.txt",
        "decks/bebop_rocksteady/PROTOTYPE_0.1.txt",
        "decks/splinter/PROTOTYPE_0.1.txt",
        "decks/shredder/PROTOTYPE_0.1.txt",
        "decks/april_oneil/PROTOTYPE_0.1.txt",
        "decks/casey_jones/PROTOTYPE_0.1.txt",
    }


def test_zone_history_follows_new_object_identity_deterministically():
    initial = [
        {
            "initial_object_id": "object-1",
            "object_ids": ["object-1"],
            "owner": 0,
            "semantic_key": "known-key",
            "zone_history": [{"zone": "hand", "object_id": "object-1"}],
        }
    ]
    events = [
        {
            "event": "zone_changed",
            "turn": 1,
            "phase": "precombat_main",
            "step": "precombat_main",
            "source_object_id": "object-1",
            "destination_object_id": "object-2",
            "destination_zone": "stack",
        },
        {
            "event": "zone_changed",
            "turn": 1,
            "phase": "precombat_main",
            "step": "precombat_main",
            "source_object_id": "object-2",
            "destination_object_id": "object-3",
            "destination_zone": "graveyard",
        },
    ]
    result = _finish_presence(initial, events)
    assert result[0]["object_ids"] == ["object-1", "object-2", "object-3"]
    assert [item["zone"] for item in result[0]["zone_history"]] == [
        "hand",
        "stack",
        "graveyard",
    ]


def test_created_token_presence_uses_authoritative_runtime_namespace():
    definition = TokenDefinition(
        "Provision",
        "Artifact — Food",
        oracle_text="{2}, {T}, Sacrifice this artifact: You gain 3 life.",
    )
    current, presence = _created_token_presence(definition)
    token = next(obj for obj in current._objects.values() if getattr(obj, "is_token", False))
    event = next(item for item in current.events if item["event"] == "tokens_created")

    assert len(presence) == 1
    record = presence[0]
    assert record["initial_object_id"] == token.object_id
    assert record["owner"] == token.owner
    assert record["creation_event_id"] == event["event_id"]
    assert record["token_definition_identity"] == _token_definition_identity(definition)
    assert record["oracle_fragment"] == definition.oracle_text
    assert str(record["semantic_key"]).startswith("runtime-token:")
    assert "oracle" not in record["token_definition_identity"]


def test_created_token_presence_is_deterministic_and_definition_distinct():
    first = TokenDefinition(
        "Drone",
        "Artifact Creature — Robot",
        power=1,
        toughness=1,
        oracle_text="Vigilance",
        keywords=("Vigilance",),
    )
    distinguishable = TokenDefinition(
        "Drone",
        "Artifact Creature — Robot",
        power=1,
        toughness=1,
        oracle_text="Vigilance",
        keywords=("Vigilance", "Trample"),
    )

    _game_a, presence_a = _created_token_presence(first)
    _game_b, presence_b = _created_token_presence(first)
    _game_c, presence_c = _created_token_presence(distinguishable)

    assert canonical_json(presence_a) == canonical_json(presence_b)
    assert presence_a[0]["semantic_key"] != presence_c[0]["semantic_key"]
    assert presence_a[0]["token_definition_identity"] != presence_c[0]["token_definition_identity"]


def test_created_token_presence_preserves_zone_lineage_after_token_ceases():
    definition = TokenDefinition(
        "Drone",
        "Artifact Creature — Robot",
        power=1,
        toughness=1,
        oracle_text="Vigilance",
        keywords=("Vigilance",),
    )
    current = _token_game()
    token = current.create_tokens(
        0,
        TokenCreationProgram(definition, 1),
        source_card="Stage 002 fixture",
        oracle_fragment="Create a fixture token.",
    )[0]
    graveyard_object = current.put_into_graveyard(token)
    current.check_state_based_actions()
    presence: list[dict[str, object]] = []

    _add_created_token_presence(current, presence, current.events)
    finished = _finish_presence(presence, current.events)

    assert finished[0]["object_ids"] == [token.object_id, graveyard_object.object_id]
    assert [item["zone"] for item in finished[0]["zone_history"]] == [
        "battlefield",
        "graveyard",
    ]
    assert any(item["event"] == "token_ceased" for item in current.events)


def test_runtime_token_namespace_reconciles_without_frozen_oracle_identity():
    definition = TokenDefinition(
        "Provision",
        "Artifact — Food",
        oracle_text="{2}, {T}, Sacrifice this artifact: You gain 3 life.",
    )
    current, presence = _created_token_presence(definition)
    snapshot = _snapshot()
    snapshot["events"] = current.snapshot()["events"]
    snapshot["stage002_presence"] = presence
    snapshot["conformance"] = {
        "semantic_occurrences": [],
        "opportunity_witnesses": [],
        "opportunity_contexts": [],
        "executed_references": [],
        "stop_records": [],
    }

    report = reconcile_snapshot(stage_games()[0], snapshot, {"decks": []})

    assert report["stop_records"] == []
    assert report["presence"][0]["classification"] == "present_unreached"


def test_parameterized_runner_preserves_acceptance_001_gameplay():
    script_path = ROOT / "scripts" / "run_acceptance_match_001.py"
    module_spec = importlib.util.spec_from_file_location("acceptance_match_001", script_path)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)

    spec = GameSpec(
        "acceptance-001-regression",
        "acceptance-001",
        7001,
        "canonical",
        (
            DeckSpec("leonardo-p0.1", "decks/leonardo/PROTOTYPE_0.1.txt"),
            DeckSpec("raphael-p0.1", "decks/raphael/PROTOTYPE_0.1.txt"),
        ),
    )
    generic = run_game(ROOT, spec)
    presence = generic.pop("stage002_presence")
    assert presence
    assert generic == module.run(ROOT, 7001)
    generic["stage002_presence"] = presence
    catalog = load_catalog(ROOT)
    manifest = {"decks": [build_deck_manifest(ROOT, seat, catalog) for seat in spec.seats]}
    report = reconcile_snapshot(spec, generic, manifest)
    assert report["stop_records"] == []
    assert (
        report["authenticated_executed_references"] == generic["conformance"]["executed_references"]
    )
