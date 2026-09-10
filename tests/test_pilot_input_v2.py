"""Interface validation only: no fitness scoring or calibration."""

import copy
import json
import pickle
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass

import pytest

from tmnt_design_studio.card_interpreter07 import (
    CastKind,
    DiscardDrawProgram,
    HandBottomDrawProgram,
    ScryProgram,
)
from tmnt_design_studio.engine07 import (
    ActivatedAbilityObject,
    CardFact,
    Game,
    PriorityState,
    RulesEvent,
    RulesEventKind,
    StackObject,
    TemporaryKeyword,
    TemporaryKeywordEffect,
    TriggeredAbilityObject,
    TriggerEffect,
)
from tmnt_design_studio.pilot_input_v2 import decision_context

LAND = CardFact("Island", "", 0, "Basic Land — Island")
BODY = CardFact("Public body", "{1}", 1, "Creature", "", 2, 3)


def make_game():
    game = Game(([LAND] * 20, [LAND] * 20), seed=401)
    game.begin_turn()
    for seat in (0, 1):
        game.create_permanent(LAND, seat)
        game.create_permanent(BODY, seat, summoning_sick=False)
    return game


def immutable(value):
    if is_dataclass(value):
        assert value.__dataclass_params__.frozen
        assert not hasattr(value, "__dict__")
        for f in fields(value):
            with pytest.raises((FrozenInstanceError, AttributeError)):
                setattr(value, f.name, getattr(value, f.name))
            immutable(getattr(value, f.name))
    elif isinstance(value, tuple):
        for item in value:
            immutable(item)
    else:
        assert type(value) in (str, int, bool, type(None))


def serialized(value):
    return json.dumps(asdict(value), sort_keys=True)


def graph_state(game):
    # Includes every state/evidence field, registry, counters, interpreter and
    # private anchors, beyond the public snapshot. Callbacks are unchanged.
    clone = copy.deepcopy(vars(game))
    for name in tuple(clone):
        if callable(clone[name]):
            clone[name] = id(vars(game)[name])
    return pickle.dumps(clone)


@pytest.mark.parametrize("seat", [0, 1])
def test_recipient_privacy_purity_and_deep_immutability(seat):
    game = make_game()
    before = graph_state(game)
    view = game.pilot_view(seat)
    context = decision_context(game, seat)
    immutable(view)
    immutable(context)
    assert graph_state(game) == before
    assert view.observer_index == context.observer_index == seat
    assert view.hands[1 - seat] == ()
    assert view.hand_sizes == tuple(len(p.hand) for p in game.players)
    assert len(view.hands[seat]) == view.hand_sizes[seat]
    assert context.library_sizes == tuple(len(p.library) for p in game.players)
    hidden = [*game.players[1 - seat].hand]
    hidden += [c for p in game.players for c in p.library]
    for card in hidden:
        assert card.object_id not in serialized(context)
        assert card.object_id not in serialized(view)
    old = serialized(context)
    game.players[seat].hand[0].card = BODY
    game.players[0].battlefield[1].counters["+1/+1"] = 5
    assert serialized(context) == old


@pytest.mark.parametrize("seat", [0, 1])
def test_hidden_identity_and_future_order_noninterference_in_views_and_options(seat):
    game = make_game()
    game._active_player = seat
    before_view = game.pilot_view(seat)
    before_context = decision_context(game, seat)
    options = game.legal_main_actions(seat)
    for index, card in enumerate(game.players[1 - seat].hand):
        del game._objects[card.object_id]
        card.object_id = f"opponent-secret-{index}"
        card.card = CardFact(f"Secret {index}", "{9}", 9, "Creature", "secret", 9, 9)
        game._objects[card.object_id] = card
    for player in game.players:
        player.library.reverse()
    assert game.pilot_view(seat) == before_view
    assert decision_context(game, seat) == before_context
    assert game.legal_main_actions(seat) == options
    assert "opponent-secret" not in repr(options)


@pytest.mark.parametrize("seat", [0, 1])
@pytest.mark.parametrize("hook", ["scry", "bottom", "discard", "mandatory"])
@pytest.mark.parametrize("empty", [False, True])
def test_private_dispatch_binding_inspection_and_empty_counts(seat, hook, empty):
    game = make_game()
    if empty:
        for card in tuple(game.players[seat].hand):
            game.move_object(card, "graveyard")
        for card in tuple(game.players[seat].library):
            game.move_object(card, "graveyard")
    own_hand = tuple((c.object_id, c.name) for c in game.players[seat].hand)
    inspected = tuple(reversed(game.players[seat].library[-2:]))
    observations = []

    def choose(view, options):
        immutable(view)
        assert view.schema_version == view.context.schema_version == 2
        assert view.player_index == view.context.observer_index == seat
        assert tuple((c.object_id, c.name) for c in view.context.own_hand) == own_hand
        assert view.context.library_sizes[seat] == len(game.players[seat].library)
        allowed = {c.object_id for c in view.context.own_hand}
        if hook == "scry":
            assert view.cards == tuple((c.object_id, c.name) for c in inspected)
            assert tuple(c.object_id for c in view.inspected_cards) == tuple(
                c.object_id for c in inspected
            )
            allowed.update(c.object_id for c in inspected)
        else:
            assert view.cards == own_hand
        for p in game.players:
            for card in (*p.hand, *p.library):
                if card.object_id not in allowed:
                    assert card.object_id not in serialized(view)
        observations.append(view)
        return options[0]

    if hook == "scry":
        game.scry_chooser = choose
        game.scry(seat, ScryProgram(2), source_card="Public", oracle_fragment="Scry 2.")
    elif hook == "bottom":
        game.hand_bottom_draw_chooser = choose
        game.choose_hand_bottom_draw(seat, HandBottomDrawProgram(1, 1, True, True))
    else:
        game.discard_draw_chooser = choose
        game.draw_discard_chooser = choose
        mandatory = hook == "mandatory"
        game.choose_discard_draw(
            seat, DiscardDrawProgram(1, 1, not mandatory, not mandatory, mandatory)
        )
    assert len(observations) == 1


@pytest.mark.parametrize("seat", [0, 1])
def test_scry_future_library_changes_preserve_inspected_projection_and_options(seat):
    game = make_game()
    observed = []
    game.scry_chooser = lambda view, options: (
        observed.append((view, options))
        or next(
            o for o in options if o.top_ids == tuple(c[0] for c in view.cards) and not o.bottom_ids
        )
    )
    game.scry(seat, ScryProgram(2), source_card="Public", oracle_fragment="Scry 2.")
    library = game.players[seat].library
    library[:-2] = reversed(library[:-2])
    for c in library[:-2]:
        c.card = CardFact("Uninspected secret", "", 0, "Land")
    game.scry(seat, ScryProgram(2), source_card="Public", oracle_fragment="Scry 2.")
    assert observed[0] == observed[1]


@pytest.mark.parametrize("seat", [0, 1])
def test_stack_allowlist_order_targets_source_departure_and_nonactive_priority(seat):
    game = make_game()
    source = game.players[seat].battlefield[1]
    victim = game.players[1 - seat].battlefield[1]
    spell = StackObject("stack-z", BODY, seat, seat, CastKind.CREATURE, victim.object_id)
    event = RulesEvent("private-event", RulesEventKind.CREATURE_ENTERED, seat, ("secret-id",))
    trigger = TriggeredAbilityObject(
        "stack-a",
        1 - seat,
        source.object_id,
        BODY,
        "Scry 2.",
        TriggerEffect.SCRY,
        event,
        target_id=victim.object_id,
    )
    # Program and paid-cost payloads are deliberately opaque; the projection
    # must not inspect/serialize them to describe an announced ability.
    ability = ActivatedAbilityObject(
        "stack-m",
        seat,
        source.object_id,
        BODY,
        "Public ability",
        object(),
        ("private-paid-id",),
        False,
        target_ids=(spell.object_id, victim.object_id),
        choice_ids=("future-choice-secret",),
    )
    game.stack[:] = [spell, trigger, ability]
    game.priority_state = PriorityState(73, seat, (1 - seat,))
    game._active_player = 1 - seat
    before = graph_state(game)
    options = game.legal_priority_actions(seat)
    view = game.priority_view(seat)
    assert graph_state(game) == before
    immutable(view)
    assert game.legal_priority_actions(seat) == options
    assert view.context.observer_index == view.priority_player == seat
    assert view.context.active_player == 1 - seat
    assert view.priority_epoch == 73 and view.consecutive_passes == (1 - seat,)
    rows = view.stack_bottom_to_top
    assert [r.object_id for r in rows] == ["stack-z", "stack-a", "stack-m"]
    assert [r.kind for r in rows] == ["spell", "triggered", "activated"]
    assert [r.controller for r in rows] == [seat, 1 - seat, seat]
    assert rows[0].spell_card.object_id == spell.object_id and rows[0].source_card is None
    assert rows[1].source_id == source.object_id and rows[1].spell_card is None
    assert [t.object_id for t in rows[2].targets] == [spell.object_id, victim.object_id]
    assert [t.current_public_zone for t in rows[2].targets] == ["stack", "battlefield"]
    assert all(t.announcement_zone is None for row in rows for t in row.targets)
    assert "secret" not in serialized(view) and "private-paid-id" not in serialized(view)
    game.move_object(source, "hand")
    departed = game.move_object(victim, "hand")
    replacement = game.move_object(departed, "battlefield")
    updated = game.priority_view(seat).stack_bottom_to_top
    assert updated[1].source_card == rows[1].source_card
    target = updated[2].targets[1]
    assert target.object_id == victim.object_id != replacement.object_id
    assert target.status == "unresolved" and target.description is None
    assert target.current_public_zone is None
    with pytest.raises(ValueError, match="decision owner"):
        game.priority_view(1 - seat)
    game.stack.append(object())
    with pytest.raises(ValueError, match="Stack kind"):
        game.priority_view(seat)


def test_battlefield_copied_characteristics_and_payment_observations():
    game = make_game()
    land, body = game.players[0].battlefield
    body.counters.update({"stun": 2, "+1/+1": 1})
    body.temporary_keyword_effects.append(
        TemporaryKeywordEffect(
            TemporaryKeyword.HASTE, "until_end_of_turn", "public-source", "public text"
        )
    )
    rows = decision_context(game, 0).battlefields[0]
    assert rows[0].represented_land_payment_color == "U"
    assert rows[0].land_payment_untapped is True
    assert rows[1].land_payment_untapped is None
    assert rows[1].power == 3 and rows[1].toughness == 4
    assert rows[1].counters == (("+1/+1", 1), ("stun", 2))
    assert dict(rows[1].represented_keyword_status)["temporary_haste"] is True
    land.tapped = True
    assert decision_context(game, 0).battlefields[0][0].land_payment_untapped is False


@pytest.mark.parametrize("seat", [-1, 2, None, True])
def test_invalid_recipients_fail_closed(seat):
    with pytest.raises(ValueError, match="explicit seat"):
        make_game().pilot_view(seat)
