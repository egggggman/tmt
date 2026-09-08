import copy
import json
from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, RulesEventKind, TriggerEffect
from tmnt_design_studio.food_search07 import FoodSearchOption

LAND = CardFact("Plains", "", 0, "Basic Land")
FOOD = CardFact("Test Food Card", "{1}", 1, "Artifact \u2014 Food")
FRAGMENT = CardInterpreter.ETB_FOOD_SEARCH_FRAGMENT
COURIER = CardFact("Courier of Comestibles", "{2}{G}", 3, "Creature", FRAGMENT, 3, 2)


def setup(chooser=None, foods=2, owner=0):
    g = Game(([LAND] * 30, [LAND] * 30), seed=28, food_search_chooser=chooser)
    g.begin_turn()
    for _ in range(foods):
        obj = g._create_card_object(FOOD, owner, "library")
        g.players[owner].library.append(obj)
    source = g.create_permanent(COURIER, owner)
    g._process_creature_entered_triggers(source)
    return g, source, g.stack[-1]


def resolve(g):
    while g.priority_state is not None:
        if g.priority_state.resolution_pending:
            g.process_priority_resolution()
        else:
            g.execute_priority_action(g.legal_priority_actions(g.priority_state.player_index)[0])


def evidence(g):
    return next(e for e in g.events if e["event"] == "etb_food_search_committed")


def test_exact_grammar_and_no_name_dispatch():
    i = CardInterpreter()
    assert i.etb_food_search_semantic_coverage(COURIER, FRAGMENT).fully_supported
    assert i.etb_food_search_semantic_coverage(replace(COURIER, name="Renamed"), FRAGMENT)
    assert (
        i.etb_food_search_semantic_coverage(replace(COURIER, type_line="Artifact"), FRAGMENT)
        is None
    )


@pytest.mark.parametrize(
    "fragment",
    [
        FRAGMENT.replace("Food card", "artifact card"),
        FRAGMENT.replace("enters", "attacks"),
        FRAGMENT.replace("you may", "you must"),
        FRAGMENT.replace("then shuffle", "then draw a card"),
        FRAGMENT + " Draw a card.",
        FRAGMENT.split(" (It's")[0],
    ],
)
def test_neighbors_fail_closed(fragment):
    assert CardInterpreter().etb_food_search_semantic_coverage(COURIER, fragment) is None


def test_once_and_no_early_mutation():
    g, source, ability = setup()
    before = tuple(g.players[0].library), tuple(g.players[0].hand), tuple(g.players[0].battlefield)
    g._enqueue_trigger(ability.event, source, FRAGMENT, TriggerEffect.ETB_FOOD_SEARCH)
    g._put_pending_triggers_on_stack()
    assert g.stack == [ability]
    with pytest.raises(ValueError, match="before all players pass"):
        g.resolve_top_of_stack()
    assert before == (
        tuple(g.players[0].library),
        tuple(g.players[0].hand),
        tuple(g.players[0].battlefield),
    )
    resolve(g)
    after = g.snapshot()
    with pytest.raises(ValueError):
        g._resolve_etb_food_search(ability)
    assert after == g.snapshot()


@pytest.mark.parametrize("owner", [0, 1])
def test_success_identity_reveal_shuffle_no_token(owner):
    observed = []

    def choose(view, options):
        observed.append((view, options))
        assert len(view.cards) == 2
        assert len({o.card_id for o in options if o.card_id}) == 2
        return options[1]

    g, source, ability = setup(choose, owner=owner)
    original = tuple(g.players[owner].library)
    resolve(g)
    e = evidence(g)
    assert e["selected_library_id"] == original[-1].object_id
    assert e["hand_id"] != e["selected_library_id"]
    assert g.players[owner].hand[-1].card is FOOD
    assert not e["token_ids"]
    assert g.players[owner].hand[-1].owner == owner
    assert len(g.players[owner].library) == len(original) - 1
    assert len(observed) == 1
    Game.validate_food_search_snapshot_evidence(json.loads(json.dumps(g.snapshot())))


@pytest.mark.parametrize("search,foods", [(False, 2), (False, 0), (True, 0), (True, 2)])
def test_decline_or_no_result_creates_one_food(search, foods):
    g, _source, _ability = setup(lambda _v, _o: FoodSearchOption(search), foods)
    before_hand = tuple(g.players[0].hand)
    resolve(g)
    e = evidence(g)
    assert e["hand_id"] is None and len(e["token_ids"]) == 1
    token = g._objects[e["token_ids"][0]]
    assert token.card is CardInterpreter.PREDEFINED_TOKENS["food"] and token.is_token
    assert tuple(g.players[0].hand) == before_hand
    assert bool([e for e in g.events if e["event"] == "food_search_shuffled"]) == search
    Game.validate_food_search_snapshot_evidence(json.loads(json.dumps(g.snapshot())))


@pytest.mark.parametrize(
    "kind", ["fabricated", "stale", "relinked", "card", "zones", "registry", "movement", "rng"]
)
def test_chooser_tampering_fails_closed(kind):
    def choose(_view, options):
        obj = g.players[0].library[-1]
        if kind == "fabricated":
            return FoodSearchOption(True, "fake")
        if kind == "stale":
            return FoodSearchOption(True, stale_id)
        if kind == "relinked":
            g._objects[obj.object_id] = copy.copy(obj)
        if kind == "card":
            obj.card = replace(obj.card)
        if kind == "zones":
            g.players[0].library.pop()
        if kind == "registry":
            g._objects["fake"] = copy.copy(obj)
        if kind == "movement":
            g.move_object(obj, "hand", reason="invalid")
        if kind == "rng":
            g.rng.shuffled([1, 2, 3], domain="invalid")
        return options[0]

    g, _source, _ability = setup(choose)
    stale = g.players[0].library[-1]
    stale_id = stale.object_id
    g.move_object(stale, "graveyard", reason="test_stale")
    before = tuple(g.players[0].library), tuple(g.players[0].hand), tuple(g.players[0].graveyard)
    with pytest.raises(ValueError, match="Food search"):
        resolve(g)
    assert before == (
        tuple(g.players[0].library),
        tuple(g.players[0].hand),
        tuple(g.players[0].graveyard),
    )
    assert all(g.is_authoritative(obj, "library") for obj in g.players[0].library)
    assert not any(e["event"] == "etb_food_search_committed" for e in g.events)


@pytest.mark.parametrize("kind", ["source", "event", "controller", "stack", "fragment"])
def test_provenance_tampering(kind):
    g, source, ability = setup()
    before = tuple(g.players[0].library), tuple(g.players[0].hand)
    if kind == "source":
        g._objects[source.object_id] = copy.copy(source)
    if kind == "event":
        ability.event = replace(ability.event, subject_ids=("fake",))
    if kind == "controller":
        ability.controller = 1
    if kind == "stack":
        clone = copy.copy(ability)
        g.stack[-1] = clone
        g._objects[ability.object_id] = clone
    if kind == "fragment":
        ability.oracle_fragment += " Draw a card."
    with pytest.raises(ValueError):
        resolve(g)
    assert before == (tuple(g.players[0].library), tuple(g.players[0].hand))


def test_source_departure_and_wrong_event():
    g, source, _ability = setup()
    event = g._new_rules_event(RulesEventKind.ATTACKERS_DECLARED, 0, (source.object_id,))
    with pytest.raises(ValueError, match="entry provenance"):
        g._enqueue_trigger(event, source, FRAGMENT, TriggerEffect.ETB_FOOD_SEARCH)
    g.put_into_graveyard(source)
    resolve(g)
    assert evidence(g)["hand_id"]
    Game.validate_food_search_snapshot_evidence(g.snapshot())


def test_deterministic_shuffle():
    runs = []
    for _ in range(2):
        g, _, _ = setup()
        resolve(g)
        runs.append(json.dumps(g.snapshot(), sort_keys=True))
    assert runs[0] == runs[1]


@pytest.mark.parametrize(
    "field,value",
    [
        ("hand_id", "fake"),
        ("selected_library_id", "fake"),
        ("token_ids", ["fake"]),
        ("controller", 1),
        ("search", False),
        ("start_event_cursor", 0),
        ("post_library_ids", []),
    ],
)
def test_evidence_tampering(field, value):
    g, _, _ = setup()
    resolve(g)
    snapshot = json.loads(json.dumps(g.snapshot()))
    next(e for e in snapshot["events"] if e["event"] == "etb_food_search_committed")[field] = value
    with pytest.raises(ValueError, match="reconstruct"):
        Game.validate_food_search_snapshot_evidence(snapshot)


@pytest.mark.parametrize("kind", ["library_reassigned", "hand_reassigned", "register"])
def test_chooser_cannot_replace_zones_or_register(kind):
    def choose(_view, options):
        if kind == "library_reassigned":
            g.players[0].library = []
        elif kind == "hand_reassigned":
            g.players[1].hand = []
        else:
            g.create_permanent(FOOD, 0)
        return options[0]

    g, _, _ = setup(choose)
    before = tuple(g.players[0].library), tuple(g.players[1].hand), set(g._objects)
    with pytest.raises(ValueError, match="Food search"):
        resolve(g)
    assert before == (tuple(g.players[0].library), tuple(g.players[1].hand), set(g._objects))


def test_food_means_subtype_and_excludes_tokens():
    g, _, _ = setup(foods=0)
    for card, token in [
        (replace(FOOD, type_line="Artifact"), False),
        (replace(FOOD, type_line="Artifact \u2014 Foodstuff"), False),
        (FOOD, True),
    ]:
        obj = g._create_card_object(card, 0, "library")
        obj.is_token = token
        assert not g._is_food_card(obj)


@pytest.mark.parametrize("branch", ["success", "decline", "no_result"])
def test_evidence_survives_later_zone_changes(branch):
    chooser = (
        None if branch == "success" else lambda _v, _o: FoodSearchOption(branch == "no_result")
    )
    g, _, _ = setup(chooser)
    resolve(g)
    e = evidence(g)
    obj = g._objects[e["hand_id"] or e["token_ids"][0]]
    if obj.zone == "hand":
        g.move_object(obj, "graveyard", reason="later_discard")
    else:
        g.put_into_graveyard(obj)
        g.check_state_based_actions()
    Game.validate_food_search_snapshot_evidence(json.loads(json.dumps(g.snapshot())))


@pytest.mark.parametrize(
    "kind",
    [
        "shuffle",
        "reveal",
        "candidate",
        "both_branches",
        "missing_entry",
        "missing_history",
        "rng_record",
        "reordered",
    ],
)
def test_independent_reconstruction_rejects_corruption(kind):
    g, _, _ = setup()
    resolve(g)
    snapshot = json.loads(json.dumps(g.snapshot()))
    if kind == "missing_entry":
        snapshot["rules_event_evidence"] = []
    elif kind == "missing_history":
        snapshot["food_search_evidence"] = []
    elif kind == "rng_record":
        snapshot["rng"]["records"][-1]["state_after"] = "fake"
    else:
        steps = snapshot["food_search_evidence"][0]["events"]
        if kind == "shuffle":
            next(e for e in steps if e["event"] == "food_search_shuffled")["permutation"] = []
        elif kind == "reveal":
            next(e for e in steps if e["event"] == "food_card_revealed")["library_object_id"] = (
                "fake"
            )
        elif kind == "candidate":
            steps[0]["candidates"] = []
        elif kind == "both_branches":
            steps[-1]["token_ids"] = ["fake"]
        elif kind == "reordered":
            steps[1], steps[2] = steps[2], steps[1]
        # Corrupt both copies: reconstruction must independently reject the claim.
        start = snapshot["food_search_evidence"][0]["start_event_cursor"]
        snapshot["events"][start : start + len(steps)] = copy.deepcopy(steps)
    with pytest.raises(ValueError, match="reconstruct"):
        Game.validate_food_search_snapshot_evidence(snapshot)


def test_live_evidence_tampering_fails_closed():
    g, _, _ = setup()
    resolve(g)
    evidence(g)["hand_id"] = "fake"
    with pytest.raises(ValueError, match="original transaction"):
        g.snapshot()


def test_missing_transaction_ledger_fails_closed():
    g, _, _ = setup()
    resolve(g)
    snapshot = json.loads(json.dumps(g.snapshot()))
    del snapshot["food_search_evidence"]
    with pytest.raises(ValueError, match="reconstruct"):
        Game.validate_food_search_snapshot_evidence(snapshot)
