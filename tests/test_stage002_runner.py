from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

from tmnt_design_studio.card_interpreter07 import (
    CardInterpreter,
    TokenCreationProgram,
    TokenDefinition,
)
from tmnt_design_studio.conformance07 import opportunity_context_key
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
    TurnStep,
)
from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.stage002 import (
    PAIRINGS,
    DeckSpec,
    GameSpec,
    _add_created_token_presence,
    _checked_action,
    _finish_presence,
    _resolve_combat_damage_steps,
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
    validate_stage_result_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Plains", "", 0, "Basic Land — Plains", oracle_id="stage002-land")
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
DIES_DRAW = CardFact(
    "Anonymous dies fixture",
    "{2}",
    2,
    "Artifact Creature — Robot",
    "When this creature dies, draw a card.",
    power=2,
    toughness=2,
)
FIRST_STRIKE = CardFact(
    "First strike fixture",
    "{1}{W}",
    2,
    "Creature — Soldier",
    "First strike",
    power=2,
    toughness=2,
    keywords=("First strike",),
)


def _token_game() -> Game:
    return Game(([LAND] * 60, [LAND] * 60), seed=83)


def _combat_game(attacker_card: CardFact, blocker_card: CardFact) -> Game:
    current = Game(([LAND] * 60, [LAND] * 60), seed=84)
    current.begin_turn()
    attacker = current.create_permanent(attacker_card, 0, summoning_sick=False)
    blocker = current.create_permanent(blocker_card, 1, summoning_sick=False)
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    attack = next(
        option
        for option in current.legal_attack_options(0)
        if option.attacker_ids == (attacker.object_id,)
    )
    current.execute_attack_action(attack)
    current.execute_block_action(
        ActionOption(
            ActionKind.DECLARE_BLOCKERS,
            1,
            blocks=((attacker.object_id, blocker.object_id),),
        )
    )
    return current


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


def _resolved_food_token_snapshot() -> tuple[dict[str, object], dict[str, object]]:
    current = Game(([LAND] * 40, [LAND] * 40), seed=1201)
    current.begin_turn()
    for _ in range(2):
        current.create_permanent(LAND, 0, summoning_sick=False)
    current.create_tokens(
        0,
        TokenCreationProgram(CardInterpreter.PREDEFINED_TOKENS["food"], 1),
        source_card="Anonymous creator",
        oracle_fragment="Create a Food token.",
    )
    option = next(
        item for item in current.legal_main_actions(0) if item.kind is ActionKind.ACTIVATE_ABILITY
    )
    assert current.execute_main_action(option)
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            priority = current.legal_priority_actions(current.priority_state.player_index)[0]
            current.execute_priority_action(priority)
    snapshot = current.snapshot()
    presence: list[dict[str, object]] = []
    _add_created_token_presence(current, presence, snapshot["events"])
    snapshot["stage002_presence"] = _finish_presence(presence, snapshot["events"])
    return snapshot, snapshot["stage002_presence"][0]


def test_runner_combat_without_stack_work_keeps_existing_progression():
    current = _combat_game(BEAR, BEAR)

    _resolve_combat_damage_steps(current, AcceptancePilot())

    assert current.step is TurnStep.END_OF_COMBAT
    assert len(current.combat_damage_evidence) == 1
    assert current.stack == []
    assert current.priority_state is None


def test_runner_drains_damage_created_trigger_without_repeating_damage():
    current = _combat_game(BEAR, DIES_DRAW)
    hand_before = len(current.players[1].hand)

    _resolve_combat_damage_steps(current, AcceptancePilot())

    assert current.step is TurnStep.END_OF_COMBAT
    assert len(current.combat_damage_evidence) == 1
    assert len(current.players[1].hand) == hand_before + 1
    assert current.stack == []
    assert current.priority_state is None
    assert sum(event["event"] == "trigger_resolved" for event in current.events) == 1


def test_runner_completely_drains_simultaneous_damage_created_triggers():
    current = _combat_game(DIES_DRAW, DIES_DRAW)
    hands_before = tuple(len(player.hand) for player in current.players)

    _resolve_combat_damage_steps(current, AcceptancePilot())

    assert current.step is TurnStep.END_OF_COMBAT
    assert len(current.combat_damage_evidence) == 1
    assert tuple(len(player.hand) for player in current.players) == tuple(
        size + 1 for size in hands_before
    )
    assert current.stack == []
    assert current.priority_state is None
    assert sum(event["event"] == "trigger_resolved" for event in current.events) == 2


def test_runner_drains_trigger_before_next_distinct_strike_damage_step():
    current = _combat_game(FIRST_STRIKE, DIES_DRAW)

    _resolve_combat_damage_steps(current, AcceptancePilot())

    assert current.step is TurnStep.END_OF_COMBAT
    assert len(current.combat_damage_evidence) == 2
    names = [event["event"] for event in current.events]
    first_damage = names.index("combat_damage_step_resolved")
    trigger = names.index("trigger_resolved")
    second_damage = names.index("combat_damage_step_resolved", first_damage + 1)
    assert first_damage < trigger < second_damage


def _snapshot(*, context: bool = False, witness: bool = False) -> dict[str, object]:
    context_row = {
        "context_id": "context-1",
        "context_kind": "activation_available",
        "turn": 3,
        "phase": "precombat_main",
        "step": "precombat_main",
        "active_player": 0,
        "controller": 0,
        "source_id": "object-1",
        "subject_ids": ["object-1"],
        "subject_zones": ["battlefield"],
        "facts": {"timing": "precombat_main"},
        "event_id": None,
        "stack_object_id": None,
        "state_fingerprint": "a" * 64,
    }
    context_row["context_key"] = opportunity_context_key(
        context_row["context_id"],
        context_row["context_kind"],
        context_row["turn"],
        context_row["phase"],
        context_row["step"],
        context_row["active_player"],
        context_row["controller"],
        context_row["source_id"],
        tuple(context_row["subject_ids"]),
        tuple(context_row["subject_zones"]),
        tuple(context_row["facts"].items()),
        context_row["event_id"],
        context_row["stack_object_id"],
        context_row["state_fingerprint"],
    )
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
                        "object_id": "object-1",
                        "controller": 0,
                        "source_controller": 0,
                        "turn": 3,
                        "phase": "precombat_main",
                        "step": "precombat_main",
                        "cause_subject_ids": ["object-1"],
                        "cause_subject_zones": ["battlefield"],
                        "cause_event_kind": None,
                    }
                ]
                if witness
                else []
            ),
            "opportunity_contexts": ([context_row] if context else []),
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
    validate_stage_result_evidence(result)
    for report in result["aggregate"]["games"]:
        assert report["duplicate_byte_equivalent"]
        assert (
            report["duplicate_execution_digests"]["first"]
            == report["duplicate_execution_digests"]["second"]
        )


def test_serialized_duplicate_tampering_fails_independent_validation(monkeypatch):
    monkeypatch.setattr(
        "tmnt_design_studio.stage002.build_stage_manifest", lambda _root: _manifest()
    )
    result = execute_stage(
        ROOT, runner=lambda *_args: copy.deepcopy(_snapshot()), games=stage_games()[:1]
    )
    result["aggregate"]["games"][0]["duplicate_execution_digests"]["second"] = "f" * 64

    with pytest.raises(ValueError, match="duplicate evidence"):
        validate_stage_result_evidence(result)


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "mismatch"))
def test_serialized_context_tampering_fails_closed(monkeypatch, mutation):
    monkeypatch.setattr(
        "tmnt_design_studio.stage002.build_stage_manifest", lambda _root: _manifest()
    )
    result = execute_stage(
        ROOT,
        runner=lambda *_args: copy.deepcopy(_snapshot(context=True, witness=True)),
        games=stage_games()[:1],
    )
    report = result["aggregate"]["games"][0]
    if mutation == "missing":
        report["opportunity_contexts"] = []
    elif mutation == "duplicate":
        report["opportunity_contexts"].append(copy.deepcopy(report["opportunity_contexts"][0]))
    else:
        report["opportunity_contexts"][0]["source_id"] = "object-fabricated"

    with pytest.raises(ValueError, match="opportunity-context evidence"):
        validate_stage_result_evidence(result)


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
    assert record["creation_controller"] == token.controller
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


def test_food_token_execution_authenticates_against_exact_runtime_presence():
    snapshot, presence = _resolved_food_token_snapshot()

    report = reconcile_snapshot(stage_games()[0], snapshot, {"decks": []})

    authenticated = report["authenticated_executed_references"]
    assert {item["evidence_kind"] for item in authenticated} == {
        "activated_ability",
        "food_activation",
    }
    assert {item["semantic_key"] for item in authenticated} == {presence["semantic_key"]}
    assert not any(item["kind"] == "silent_approximation" for item in report["stop_records"])


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("owner", 1),
        ("creation_controller", 1),
        ("creation_event_id", "event-fabricated"),
        ("creation_source_id", "object-fabricated"),
        ("oracle_fragment", "{2}, {T}: Draw a card."),
    ],
)
def test_food_token_execution_rejects_mismatched_runtime_provenance(field, replacement):
    snapshot, _presence = _resolved_food_token_snapshot()
    snapshot["stage002_presence"][0][field] = replacement

    report = reconcile_snapshot(stage_games()[0], snapshot, {"decks": []})

    assert report["authenticated_executed_references"] == []
    assert any(item["kind"] == "silent_approximation" for item in report["stop_records"])


def test_food_token_execution_cannot_borrow_another_runtime_token():
    snapshot, presence = _resolved_food_token_snapshot()
    borrowed = copy.deepcopy(presence)
    borrowed["initial_object_id"] = "object-fabricated"
    borrowed["object_ids"] = ["object-fabricated"]
    snapshot["stage002_presence"] = [borrowed]

    report = reconcile_snapshot(stage_games()[0], snapshot, {"decks": []})

    assert report["authenticated_executed_references"] == []
    assert any(item["kind"] == "silent_approximation" for item in report["stop_records"])


def test_ordinary_card_execution_key_is_not_normalized():
    snapshot = _snapshot()
    _add_valid_execution(snapshot)

    report = reconcile_snapshot(stage_games()[0], snapshot, _manifest())

    assert report["authenticated_executed_references"][0]["semantic_key"] == "known-key"


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
