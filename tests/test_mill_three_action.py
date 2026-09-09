import copy
import json
from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TriggerEffect

LAND = CardFact("Plains", "", 0, "Basic Land")
FRAGMENT = CardInterpreter.MILL_THREE_FRAGMENT
SIBLING = (
    "When this creature dies, you may exile it. When you do, put target creature card "
    "from your graveyard on top of your library."
)
SOURCE = CardFact("Paramecia Coloniex", "{1}{B}", 2, "Creature", FRAGMENT, 2, 2)


def setup(size=5, owner=0):
    game = Game(([LAND] * 30, [LAND] * 30), seed=31)
    game.begin_turn()
    for obj in tuple(game.players[owner].library):
        game.move_object(obj, "graveyard", reason="test_setup")
    for _ in range(size):
        game.players[owner].library.append(game._create_card_object(LAND, owner, "library"))
    source = game.create_permanent(SOURCE, owner)
    game._process_creature_entered_triggers(source)
    return game, source, game.stack[-1]


def resolve(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def validate(game):
    snapshot = game.snapshot()
    Game.validate_mill_three_snapshot_evidence(snapshot)
    Game.validate_mill_three_snapshot_evidence(json.loads(json.dumps(snapshot)))
    return snapshot


@pytest.mark.parametrize("size", range(7))
@pytest.mark.parametrize("owner", [0, 1])
def test_bounded_transaction(size, owner):
    game, source, ability = setup(size, owner)
    player = game.players[owner]
    library, yard, hand = tuple(player.library), tuple(player.graveyard), tuple(player.hand)
    rng, records = game.rng.export_state(), tuple(game.rng.records)
    before = len(game.events)
    with pytest.raises(ValueError):
        game.resolve_top_of_stack()
    assert tuple(player.library) == library and tuple(player.graveyard) == yard
    assert not any(e["event"].startswith("mill_three_") for e in game.events)
    resolve(game)
    n = min(3, size)
    assert all(a is b for a, b in zip(player.library, library[: size - n], strict=True))
    assert all(a is b for a, b in zip(player.graveyard[: len(yard)], yard, strict=True))
    moved = player.graveyard[len(yard) :]
    originals = tuple(reversed(library[-n:])) if n else ()
    assert len(moved) == n
    for old, new in zip(originals, moved, strict=True):
        assert old is not new and old.object_id != new.object_id
        assert old.zone == "former" and new.card is old.card and new.owner == owner
    changes = [e for e in game.events[before:] if e["event"] == "zone_changed"]
    assert [e["source_object_id"] for e in changes] == [o.object_id for o in originals]
    assert tuple(player.hand) == hand and not player.failed_draw_pending
    assert game.rng.export_state() == rng and tuple(game.rng.records) == records
    assert not any(e["event"] in ("draw_failed", "card_drawn") for e in game.events[before:])
    validate(game)
    with pytest.raises(ValueError):
        game._resolve_mill_three(ability)


@pytest.mark.parametrize(
    "fragment",
    [
        FRAGMENT.replace("three", "four"),
        FRAGMENT.replace("enters", "dies"),
        FRAGMENT.split(" (")[0],
        FRAGMENT + " Draw a card.",
    ],
)
def test_near_neighbors(fragment):
    assert CardInterpreter().mill_three_semantic_coverage(SOURCE, fragment) is None


def test_renaming_and_sibling_boundary():
    interpreter = CardInterpreter()
    assert interpreter.mill_three_semantic_coverage(replace(SOURCE, name="Renamed"), FRAGMENT)
    assert (
        interpreter.mill_three_semantic_coverage(replace(SOURCE, type_line="Artifact"), FRAGMENT)
        is None
    )
    assert interpreter.mill_three_semantic_coverage(SOURCE, SIBLING) is None
    assert any(
        f == SIBLING
        for f, _ in interpreter.unsupported_fragments(
            replace(SOURCE, oracle_text=FRAGMENT + "\n" + SIBLING)
        )
    )


def test_resolution_time_library_and_later_movement():
    game, _, _ = setup()
    old = game.players[0].library[-1]
    game.move_object(old, "hand", reason="before_mill")
    current = tuple(game.players[0].library)
    resolve(game)
    commit = next(e for e in game.events if e["event"] == "mill_three_committed")
    assert commit["post_library_ids"] == [o.object_id for o in current[:-3]]
    game.move_object(game.players[0].graveyard[-1], "hand", reason="after_mill")
    validate(game)


@pytest.mark.parametrize(
    "kind",
    [
        "source",
        "card",
        "event",
        "controller",
        "fragment",
        "stack",
        "library",
        "library_card",
        "graveyard",
        "allocation",
        "registry",
        "duplicate",
    ],
)
def test_preflight_tampering_has_no_partial_mill(kind):
    game, source, ability = setup()
    if kind == "source":
        game._objects[source.object_id] = copy.copy(source)
    elif kind == "card":
        source.card = replace(SOURCE)
    elif kind == "event":
        ability.event = replace(ability.event, subject_ids=("fake",))
    elif kind == "controller":
        ability.controller = 1
    elif kind == "fragment":
        ability.oracle_fragment = "fake"
    elif kind == "stack":
        game.stack[-1] = copy.copy(ability)
    elif kind == "library":
        game._objects[game.players[0].library[-2].object_id] = copy.copy(
            game.players[0].library[-2]
        )
    elif kind == "library_card":
        game.players[0].library[-2].card = replace(LAND)
    elif kind == "graveyard":
        game.players[0].graveyard[-1].owner = 1
    elif kind == "allocation":
        game._next_object_number = 1
    elif kind == "registry":
        game._objects = dict(game._objects)
    elif kind == "duplicate":
        game.players[0].library.append(game.players[0].library[-1])
    before = tuple(game.players[0].library), tuple(game.players[0].graveyard)
    with pytest.raises(ValueError):
        resolve(game)
    assert before == (tuple(game.players[0].library), tuple(game.players[0].graveyard))
    assert not any(e["event"] == "mill_three_committed" for e in game.events)


def test_departure_control_change_reentry_and_duplicate():
    game, source, ability = setup(6)
    game._enqueue_trigger(ability.event, source, FRAGMENT, TriggerEffect.ETB_MILL_THREE)
    game._put_pending_triggers_on_stack()
    assert game.stack == [ability]
    game.change_controller(source, 1)
    departed = game.move_object(source, "graveyard", reason="departure")
    other = tuple(game.players[1].library)
    resolve(game)
    assert tuple(game.players[1].library) == other
    returned = game.move_object(departed, "battlefield", reason="reentry")
    game._process_creature_entered_triggers(returned)
    resolve(game)
    assert len(game.mill_three_snapshot_evidence()["transactions"]) == 2
    validate(game)


@pytest.mark.parametrize(
    "field",
    [
        "post_library_ids",
        "post_graveyard_ids",
        "new_graveyard_ids",
        "hand_ids",
        "rng_state",
        "failed_draw_pending",
    ],
)
def test_serialized_coordinated_corruption(field):
    game, _, _ = setup()
    resolve(game)
    snapshot = json.loads(json.dumps(game.snapshot()))
    commit = next(e for e in snapshot["events"] if e["event"] == "mill_three_committed")
    commit[field] = "fake"
    snapshot["mill_three_evidence"]["transactions"][0]["events"] = snapshot["events"][
        commit["start_event_cursor"] : snapshot["events"].index(commit) + 1
    ]
    with pytest.raises(ValueError, match="reconstruct"):
        Game.validate_mill_three_snapshot_evidence(snapshot)


def test_local_rollback_on_second_move_failure(monkeypatch):
    game, _, _ = setup()
    library, yard = tuple(game.players[0].library), tuple(game.players[0].graveyard)
    number, registry = game._next_object_number, dict(game._objects)
    move = game.move_object
    calls = []

    def fail_second(obj, *args, **kwargs):
        calls.append(obj)
        if len(calls) == 2:
            raise ValueError("injected movement failure")
        return move(obj, *args, **kwargs)

    monkeypatch.setattr(game, "move_object", fail_second)
    with pytest.raises(ValueError, match="injected"):
        resolve(game)
    assert tuple(game.players[0].library) == library and tuple(game.players[0].graveyard) == yard
    assert all(o.zone == "library" for o in library)
    assert game._next_object_number == number and game._objects == registry
    assert not any(e["event"].startswith("mill_three_") for e in game.events)


@pytest.mark.parametrize("owner", [0, 1])
def test_preexisting_failed_draw_is_preserved(owner):
    game, _, _ = setup(0, owner)
    game.players[owner].failed_draw_pending = True
    start = len(game.events)
    resolve(game)
    # Normal post-resolution SBAs consume the preexisting failure, not the mill.
    assert game.players[owner].lost is True
    assert not any(e["event"] in ("card_drawn", "draw_failed") for e in game.events[start:])
    commit = next(e for e in game.events if e["event"] == "mill_three_committed")
    assert commit["failed_draw_pending"][owner] is True
    validate(game)


def test_terminal_pending_does_not_receive_execution_credit():
    game, _, _ = setup()
    game.winner = 1
    snapshot = validate(game)
    assert not any(
        e["oracle_fragment"] == FRAGMENT for e in snapshot["conformance"]["executed_references"]
    )
    assert not snapshot["mill_three_evidence"]["transactions"]


@pytest.mark.parametrize(
    "kind",
    [
        "movement_order",
        "movement_card",
        "movement_owner",
        "movement_id",
        "missing_ledger",
        "borrowed_priority",
        "pre_library",
        "live_ledger",
    ],
)
def test_deep_evidence_tampering(kind):
    game, _, _ = setup()
    resolve(game)
    if kind == "live_ledger":
        next(e for e in game.events if e["event"] == "mill_three_committed")[
            "post_library_ids"
        ] = []
        with pytest.raises(ValueError):
            game.snapshot()
        return
    snapshot = json.loads(json.dumps(game.snapshot()))
    events = snapshot["events"]
    commit = next(e for e in events if e["event"] == "mill_three_committed")
    start = commit["start_event_cursor"]
    if kind == "movement_order":
        events[start + 1], events[start + 2] = events[start + 2], events[start + 1]
    elif kind == "movement_card":
        events[start + 1]["card"] = "Forged"
    elif kind == "movement_owner":
        events[start + 1]["owner"] = "Forged"
    elif kind == "movement_id":
        events[start + 1]["destination_object_id"] = events[start + 2]["destination_object_id"]
    elif kind == "missing_ledger":
        snapshot["mill_three_evidence"]["transactions"] = []
    elif kind == "borrowed_priority":
        next(e for e in events if e["event"] == "stack_resolution_permitted")["priority_epoch"] = -1
    elif kind == "pre_library":
        events[start]["pre_library_ids"].reverse()
    if kind != "missing_ledger":
        snapshot["mill_three_evidence"]["transactions"][0]["events"] = events[
            start : events.index(commit) + 1
        ]
    with pytest.raises(ValueError, match="reconstruct"):
        Game.validate_mill_three_snapshot_evidence(snapshot)


@pytest.mark.parametrize("kind", ["former", "fabricated", "token", "graveyard_card", "source_id"])
def test_invalid_identity_fails_before_any_move(kind):
    game, _, ability = setup()
    if kind == "former":
        game.players[0].library[-2].zone = "former"
    elif kind == "fabricated":
        game.players[0].library[-2].object_id = "object-999999"
    elif kind == "token":
        game.players[0].library[-2].is_token = True
    elif kind == "graveyard_card":
        game.players[0].graveyard[-1].card = replace(LAND)
    else:
        ability.source_id = "fake"
    start = len(game.events)
    with pytest.raises(ValueError):
        resolve(game)
    assert not any(
        e["event"] in ("zone_changed", "mill_three_started") for e in game.events[start:]
    )


@pytest.mark.parametrize("zone", ["library", "graveyard"])
@pytest.mark.parametrize("container", [list, tuple])
def test_relinked_zone_containers_fail_before_movement(zone, container):
    game, _, _ = setup()
    setattr(game.players[0], zone, container(getattr(game.players[0], zone)))
    start = len(game.events)
    with pytest.raises(ValueError, match="container"):
        resolve(game)
    assert not any(e["event"] == "zone_changed" for e in game.events[start:])


def test_graveyard_reconstruction_accounts_for_prior_token_cessation():
    game, _, _ = setup()
    text = "Create a Food token."
    program = game.interpreter.token_creation_program(text)
    token = game.create_tokens(0, program, source_card="Fixture", oracle_fragment=text)[0]
    vanished = game.move_object(token, "graveyard", reason="fixture_token_departure")
    game.check_state_based_actions()
    assert vanished.zone == "former"
    resolve(game)
    snapshot = validate(game)
    corrupt = json.loads(json.dumps(snapshot))
    next(e for e in corrupt["events"] if e["event"] == "token_ceased")["object_id"] = "fake"
    with pytest.raises(ValueError, match="reconstruct"):
        Game.validate_mill_three_snapshot_evidence(corrupt)
