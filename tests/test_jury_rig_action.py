import json
from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game
from tmnt_design_studio.jury_rig07 import JuryRigOption

LAND = CardFact("Plains", "", 0, "Basic Land")
ARTIFACT = CardFact("Tool", "{1}", 1, "Artifact")
FRAGMENT = CardInterpreter.JURY_RIG_FRAGMENT
SOURCE = CardFact("Casey Jones", "{2}", 2, "Creature", FRAGMENT, 2, 2)


def setup(cards, chooser=None, owner=0):
    game = Game(([LAND] * 30, [LAND] * 30), seed=30, jury_rig_chooser=chooser)
    game.begin_turn()
    for obj in tuple(game.players[owner].library):
        game.move_object(obj, "graveyard", reason="test_setup")
    for card in cards:
        game.players[owner].library.append(game._create_card_object(card, owner, "library"))
    source = game.create_permanent(SOURCE, owner)
    game._process_creature_entered_triggers(source)
    return game


def resolve(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


@pytest.mark.parametrize("size", range(7))
@pytest.mark.parametrize("owner", [0, 1])
@pytest.mark.parametrize("select", [False, True])
def test_bounded_transaction(size, owner, select):
    game = setup([ARTIFACT] * size, None if select else lambda v, o: JuryRigOption(None), owner)
    original = tuple(game.players[owner].library)
    rng_count = len(game.rng.records)
    with pytest.raises(ValueError):
        game.resolve_top_of_stack()
    assert tuple(game.players[owner].library) == original
    resolve(game)
    snapshot = json.loads(json.dumps(game.snapshot()))
    Game.validate_jury_rig_snapshot_evidence(snapshot)
    commit = next(e for e in game.events if e["event"] == "jury_rig_committed")
    n = min(4, size)
    assert commit["untouched_ids"] == [o.object_id for o in original[: size - n]]
    assert len(game.rng.records) == rng_count + 1
    assert len(game.players[owner].library) == size - bool(size and select)
    for obj in game.players[owner].library:
        assert any(obj is old for old in original)
    if size and select:
        assert commit["selected_id"] == original[-1].object_id
        assert commit["hand_id"] != commit["selected_id"]


@pytest.mark.parametrize("fragment", [FRAGMENT.replace("four", "five"), FRAGMENT + " Draw a card."])
def test_exact_fragment_only(fragment):
    assert CardInterpreter().jury_rig_semantic_coverage(SOURCE, fragment) is None


def test_fifth_card_is_private_and_ineligible():
    observed = []

    def choose(view, options):
        observed.append(view)
        assert len(view.cards) == 4
        assert options == (JuryRigOption(None),)
        return options[0]

    game = setup([ARTIFACT] + [LAND] * 4, choose)
    original = game.players[0].library[0]
    resolve(game)
    assert game.players[0].library[-1] is original
    assert len(observed) == 1
    Game.validate_jury_rig_snapshot_evidence(json.loads(json.dumps(game.snapshot())))


@pytest.mark.parametrize("mutation", ["zone", "registry", "card", "rng", "invalid"])
def test_chooser_mutation_rolls_back(mutation):
    def choose(view, options):
        if mutation == "zone":
            game.players[0].library.pop()
        elif mutation == "registry":
            game._objects = dict(game._objects)
        elif mutation == "card":
            game.players[0].library[-1].card = replace(ARTIFACT)
        elif mutation == "rng":
            game.rng.shuffled([1, 2, 3], domain="tamper")
        else:
            return JuryRigOption("fabricated")
        return options[0]

    game = setup([ARTIFACT] * 5, choose)
    original = tuple(game.players[0].library)
    registry = game._objects
    state = game.rng.export_state()
    with pytest.raises(ValueError):
        resolve(game)
    assert game._objects is registry
    assert all(a is b for a, b in zip(original, game.players[0].library, strict=True))
    assert game.players[0].library[-1].card is ARTIFACT
    assert game.rng.export_state() == state
    assert not any(e["event"] == "jury_rig_committed" for e in game.events)


@pytest.mark.parametrize(
    "field,value", [("source_id", "fake"), ("controller", 1), ("oracle_fragment", "fake")]
)
def test_trigger_provenance(field, value):
    game = setup([ARTIFACT] * 5)
    setattr(game.stack[-1], field, value)
    before = tuple(game.players[0].library)
    with pytest.raises(ValueError):
        resolve(game)
    assert tuple(game.players[0].library) == before


@pytest.mark.parametrize(
    "kind", ["inspection", "eligible", "prefix", "order", "reveal", "rng", "hand", "ledger"]
)
def test_reconstruction_rejects_coordinated_corruption(kind):
    game = setup([ARTIFACT] * 6)
    resolve(game)
    snapshot = json.loads(json.dumps(game.snapshot()))
    events = snapshot["events"]
    decision = next(e for e in events if e["event"] == "jury_rig_decided")
    commit = next(e for e in events if e["event"] == "jury_rig_committed")
    if kind == "inspection":
        decision["inspected_ids"][0] = decision["library"][0]["object_id"]
    elif kind == "eligible":
        decision["eligible_ids"] = []
    elif kind == "prefix":
        commit["untouched_ids"].reverse()
    elif kind == "order":
        commit["post_library_ids"].reverse()
    elif kind == "reveal":
        next(e for e in events if e["event"] == "jury_rig_revealed")["card"] = "Forged"
    elif kind == "rng":
        next(e for e in events if e["event"] == "jury_rig_bottom_ordered")["permutation"] = []
    elif kind == "hand":
        decision["pre_hand_ids"] = ["invented"]
        commit["post_hand_ids"] = ["invented", commit["hand_id"]]
    else:
        snapshot["jury_rig_evidence"] = []
    if kind != "ledger":
        snapshot["jury_rig_evidence"][0]["events"] = events[
            commit["start_event_cursor"] : events.index(commit) + 1
        ]
    with pytest.raises(ValueError, match="reconstruct"):
        Game.validate_jury_rig_snapshot_evidence(snapshot)


def test_source_departure_and_determinism():
    runs = []
    for _ in range(2):
        game = setup([LAND, ARTIFACT, LAND, ARTIFACT, LAND])
        source = game._objects[game.stack[-1].source_id]
        game.put_into_graveyard(source)
        resolve(game)
        snapshot = json.loads(json.dumps(game.snapshot()))
        Game.validate_jury_rig_snapshot_evidence(snapshot)
        runs.append(snapshot)
    assert runs[0] == runs[1]


def test_resolution_time_inspection_and_artifact_creature():
    game = setup([ARTIFACT] * 5)
    game.move_object(game.players[0].library[-1], "graveyard", reason="before_resolution")
    card = replace(ARTIFACT, type_line="Artifact Creature")
    obj = game._create_card_object(card, 0, "library")
    game.players[0].library.append(obj)
    resolve(game)
    assert game.players[0].hand[-1].card is card
    Game.validate_jury_rig_snapshot_evidence(json.loads(json.dumps(game.snapshot())))


@pytest.mark.parametrize("size,select", [(0, False), (1, False), (1, True), (2, True)])
def test_trivial_remainder_records_shuffle_without_advancing_rng(size, select):
    game = setup([ARTIFACT] * size, None if select else lambda v, o: JuryRigOption(None))
    before = game.rng.export_state()
    resolve(game)
    assert game.rng.export_state() == before
    record = game.rng.records[-1]
    assert record.state_before == record.state_after
    assert len(record.result) <= 1


def test_private_view_does_not_change_public_game_view():
    from dataclasses import FrozenInstanceError

    observed = []

    def choose(view, options):
        public = game.public_view()
        assert not hasattr(public, "libraries")
        assert "Secret Tool" not in repr(public)
        assert "Lower Secret" not in repr(view)
        with pytest.raises(FrozenInstanceError):
            view.controller = 1
        observed.append(view)
        return options[0]

    game = setup(
        [replace(LAND, name="Lower Secret")] + [replace(ARTIFACT, name="Secret Tool")] * 4, choose
    )
    assert not observed
    assert not any(e["event"].startswith("jury_rig_") for e in game.events)
    resolve(game)
    assert len(observed) == 1


def test_duplicate_entry_replay_and_source_reentry():
    from tmnt_design_studio.engine07 import TriggerEffect

    game = setup([ARTIFACT] * 6)
    ability = game.stack[-1]
    source = game._objects[ability.source_id]
    game._enqueue_trigger(ability.event, source, FRAGMENT, TriggerEffect.ETB_JURY_RIG)
    game._put_pending_triggers_on_stack()
    assert game.stack == [ability]
    departed = game.move_object(source, "graveyard", reason="test_departure")
    resolve(game)
    with pytest.raises(ValueError):
        game._resolve_jury_rig(ability)
    returned = game.move_object(departed, "battlefield", reason="test_reentry")
    game._process_creature_entered_triggers(returned)
    resolve(game)
    assert len(game.jury_rig_snapshot_evidence()) == 2
    Game.validate_jury_rig_snapshot_evidence(json.loads(json.dumps(game.snapshot())))


@pytest.mark.parametrize("kind", ["stale", "relinked", "token", "provenance"])
def test_selection_and_provenance_identity_guards(kind):
    def choose(view, options):
        if kind == "stale":
            return JuryRigOption(game.players[0].graveyard[0].object_id)
        if kind == "relinked":
            from copy import copy

            obj = game.players[0].library[-1]
            game._objects[obj.object_id] = copy(obj)
        if kind == "provenance":
            ability.controller = 1
        return options[0]

    game = setup([ARTIFACT] * 5, choose)
    ability = game.stack[-1]
    if kind == "token":
        game.players[0].library[-1].is_token = True
    before = tuple(game.players[0].library)
    with pytest.raises(ValueError):
        resolve(game)
    assert all(a is b for a, b in zip(before, game.players[0].library, strict=True))
    assert ability.controller == 0


def test_recognition_does_not_dispatch_by_card_name():
    assert CardInterpreter().jury_rig_semantic_coverage(replace(SOURCE, name="Renamed"), FRAGMENT)
