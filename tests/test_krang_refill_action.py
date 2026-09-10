import copy
from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game

LAND = CardFact("Plains", "", 0, "Basic Land")
FRAGMENT = CardInterpreter.KRANG_REFILL_FRAGMENT
SOURCE = CardFact("Krang, Master Mind", "{5}{U}", 6, "Legendary Artifact Creature", FRAGMENT, 1, 4)


def setup(hand=2, library=6, owner=0):
    game = Game(([LAND] * 30, [LAND] * 30), seed=32)
    game.begin_turn()
    player = game.players[owner]
    for obj in tuple(player.hand)[hand:]:
        game.move_object(obj, "graveyard", reason="test_hand")
    while len(player.hand) < hand:
        game.draw(player, 1)
    for obj in tuple(player.library)[:-library] if library else tuple(player.library):
        game.move_object(obj, "graveyard", reason="test_library")
    source = game.create_permanent(SOURCE, owner)
    game._process_creature_entered_triggers(source)
    return game, source


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
    Game.validate_krang_refill_snapshot_evidence(snapshot)
    return snapshot


@pytest.mark.parametrize("hand", range(6))
@pytest.mark.parametrize("owner", [0, 1])
@pytest.mark.parametrize("library", [0, 1, 3, 6])
def test_boundaries(hand, owner, library):
    game, source = setup(hand, library, owner)
    player = game.players[owner]
    oldhand = tuple(player.hand)
    oldlib = tuple(player.library)
    if hand >= 4:
        assert not game.stack
        validate(game)
        return
    ability = game.stack[-1]
    with pytest.raises(ValueError):
        game.resolve_top_of_stack()
    with pytest.raises(ValueError):
        game._resolve_krang_refill(ability)
    assert tuple(player.hand) == oldhand and tuple(player.library) == oldlib
    resolve(game)
    n = 4 - hand
    k = min(n, library)
    c = next(e for e in game.events if e["event"] == "krang_refill_committed")
    assert (c["requested"], c["attempted"], c["successful"], c["failed"]) == (n, n, k, n - k)
    assert len(player.hand) == hand + k
    assert all(a is b for a, b in zip(player.hand[:hand], oldhand, strict=True))
    assert [o.object_id for o in player.library] == [
        o.object_id for o in (oldlib[:-k] if k else oldlib)
    ]
    assert player.lost is (k < n)
    snap = validate(game)
    assert any(
        r["evidence_kind"] == "krang_refill" for r in snap["conformance"]["executed_references"]
    )
    with pytest.raises(ValueError):
        game._resolve_krang_refill(ability)


@pytest.mark.parametrize("resolution_hand", [0, 1, 3, 4, 5])
def test_second_condition_and_fixed_deficit(resolution_hand):
    game, _ = setup()
    p = game.players[0]
    while len(p.hand) > resolution_hand:
        game.move_object(p.hand[-1], "graveyard", reason="response")
    while len(p.hand) < resolution_hand:
        game.draw(p, 1)
    resolve(game)
    commit = next(e for e in game.events if e["event"] == "krang_refill_committed")
    assert commit["requested"] == max(0, 4 - resolution_hand)
    snap = validate(game)
    assert any(
        r["evidence_kind"] == "krang_refill" for r in snap["conformance"]["executed_references"]
    ) is (resolution_hand < 4)


@pytest.mark.parametrize("mode", ["departure", "control", "reentry", "preexisting_failure"])
def test_source_and_failure_continuity(mode):
    game, source = setup()
    if mode == "departure":
        game.move_object(source, "graveyard", reason="response")
    if mode == "control":
        game.players[0].battlefield.remove(source)
        source.controller = 1
        game.players[1].battlefield.append(source)
    if mode == "reentry":
        grave = game.move_object(source, "graveyard", reason="response")
        new = game.move_object(grave, "battlefield", controller=0)
        game._process_creature_entered_triggers(new)
    if mode == "preexisting_failure":
        game.players[0].failed_draw_pending = True
    resolve(game)
    validate(game)
    assert any(e["event"] == "krang_refill_committed" for e in game.events)


@pytest.mark.parametrize(
    "text",
    [
        FRAGMENT.replace("four", "five"),
        FRAGMENT.replace("fewer than", "at most"),
        FRAGMENT.replace("enters", "dies"),
        FRAGMENT + " Draw a card.",
        FRAGMENT.replace("Krang", "Other"),
    ],
)
def test_recognition_rejects_neighbors(text):
    assert CardInterpreter().krang_refill_semantic_coverage(SOURCE, text) is None


def test_renamed_self_and_noncreature():
    card = replace(SOURCE, name="Renamed", oracle_text=FRAGMENT.replace("Krang", "Renamed"))
    assert CardInterpreter().krang_refill_semantic_coverage(card, card.oracle_text)
    assert (
        CardInterpreter().krang_refill_semantic_coverage(
            replace(SOURCE, type_line="Artifact"), FRAGMENT
        )
        is None
    )


@pytest.mark.parametrize(
    "field",
    [
        "source",
        "card",
        "hand",
        "library",
        "controller",
        "event",
        "fragment",
        "stack",
        "allocation",
        "entry",
    ],
)
def test_live_mutation_rejected_before_draw(field):
    game, source = setup()
    ability = game.stack[-1]
    p = game.players[0]
    if field == "source":
        game._objects[source.object_id] = copy.copy(source)
    if field == "card":
        source.card = replace(source.card)
    if field == "hand":
        game._objects[p.hand[0].object_id] = copy.copy(p.hand[0])
    if field == "library":
        p.library = list(p.library)
    if field == "controller":
        ability.controller = 1
    if field == "event":
        ability.event = replace(ability.event, subject_ids=("fake",))
    if field == "fragment":
        ability.oracle_fragment = "fake"
    if field == "stack":
        game.stack[-1] = copy.copy(ability)
    if field == "allocation":
        game._next_object_number += 1
    if field == "entry":
        next(e for e in game.events if e["event"] == "krang_refill_entry")["hand_size"] = 0
    before = (tuple(p.hand), tuple(p.library))
    with pytest.raises(ValueError):
        resolve(game)
    assert before == (tuple(p.hand), tuple(p.library))


@pytest.mark.parametrize(
    "field",
    [
        "requested",
        "hand",
        "library",
        "controller",
        "entry",
        "draw",
        "duplicate",
        "ledger",
        "permission",
        "failed",
    ],
)
def test_serialized_mutation_rejected(field):
    game, _ = setup(library=1)
    resolve(game)
    s = validate(game)
    c = next(e for e in s["events"] if e["event"] == "krang_refill_committed")
    if field == "requested":
        c["requested"] += 1
    if field == "hand":
        c["post_hand_ids"].reverse()
    if field == "library":
        c["post_library_ids"] = ["fake"]
    if field == "controller":
        c["controller"] = 1
    if field == "entry":
        next(e for e in s["events"] if e["event"] == "krang_refill_entry")["hand_size"] = 0
    if field == "draw":
        next(e for e in s["events"] if e["event"] == "krang_refill_attempt")["ordinal"] = 99
    if field == "duplicate":
        s["events"].append(copy.deepcopy(c))
    if field == "ledger":
        s["krang_refill_evidence"]["transactions"] = []
    if field == "permission":
        next(e for e in s["events"] if e["event"] == "stack_resolution_permitted")[
            "priority_epoch"
        ] = -1
    if field == "failed":
        c["failed_draw_pending"] = False
    with pytest.raises(ValueError):
        Game.validate_krang_refill_snapshot_evidence(s)


def test_false_creation_cannot_be_revived_by_discard():
    game, _ = setup(hand=4)
    game.move_object(game.players[0].hand[-1], "graveyard", reason="later_discard")
    resolve(game)
    assert not game.stack
    s = validate(game)
    assert not any(
        r["evidence_kind"] == "krang_refill" for r in s["conformance"]["executed_references"]
    )


def test_legend_departure_preserves_original_trigger():
    game, source = setup()
    game.create_permanent(SOURCE, 0)
    game.check_state_based_actions()
    resolve(game)
    validate(game)
    assert sum(e["event"] == "krang_refill_committed" for e in game.events) == 1


def test_terminal_pending_is_not_executed_and_one_pass_cannot_resolve():
    game, _ = setup()
    s = validate(game)
    assert not any(
        r["evidence_kind"] == "krang_refill" for r in s["conformance"]["executed_references"]
    )
    game.execute_priority_action(game.legal_priority_actions(game.priority_state.player_index)[0])
    with pytest.raises(ValueError):
        game.resolve_top_of_stack()


@pytest.mark.parametrize(
    "field", ["count", "player", "entry", "movement", "failure", "posthand", "passes"]
)
def test_synchronized_transaction_corruption_still_rejected(field):
    game, _ = setup(library=1)
    resolve(game)
    s = validate(game)
    tx = s["krang_refill_evidence"]["transactions"][0]
    c = tx["events"][-1]
    pre = tx["events"][0]
    if field == "count":
        pre["requested"] = c["requested"] = c["attempted"] = 1
    if field == "player":
        pre["controller"] = c["controller"] = 1
    if field == "entry":
        entry = s["krang_refill_evidence"]["entries"][0]
        entry["record"]["hand_ids"] = []
        entry["record"]["hand_size"] = 0
        s["events"][entry["cursor"]] = copy.deepcopy(entry["record"])
    if field == "movement":
        next(e for e in tx["events"] if e["event"] == "zone_changed")["source_object_id"] = pre[
            "pre_hand_ids"
        ][0]
    if field == "failure":
        next(e for e in tx["events"] if e["event"] == "draw_failed")[
            "state_based_action_pending"
        ] = False
    if field == "posthand":
        c["post_hand_ids"].reverse()
    if field == "passes":
        passes = [e for e in s["events"] if e["event"] == "priority_passed"]
        passes[-1]["player_index"] = passes[-2]["player_index"]
    s["krang_refill_evidence"]["pre_states"][c["stack_object_id"]] = copy.deepcopy(pre)
    s["events"][tx["start"] : tx["start"] + len(tx["events"])] = copy.deepcopy(tx["events"])
    with pytest.raises(ValueError):
        Game.validate_krang_refill_snapshot_evidence(s)


def test_historical_completion_survives_later_hand_movement():
    game, _ = setup()
    resolve(game)
    game.move_object(game.players[0].hand[-1], "graveyard", reason="later")
    validate(game)


def test_failed_draw_cannot_claim_credit_without_subsequent_sba():
    game, _ = setup(library=0)
    resolve(game)
    snapshot = validate(game)
    snapshot["events"] = [e for e in snapshot["events"] if e["event"] != "player_lost"]
    snapshot["players"][0]["failed_draw_pending"] = True
    with pytest.raises(ValueError):
        Game.validate_krang_refill_snapshot_evidence(snapshot)
