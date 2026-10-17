"""Variable-cost spells and complete X-dependent entry token triggers."""

import copy

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import ActionKind, ActionOption, CardFact, Game, StackObject

LAND = CardFact("Forest", "", 0, "Basic Land — Forest")
PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
OOZE = CardFact(
    "Renamed Ooze",
    "{X}{G}{G}",
    2,
    "Creature — Ooze Mutant",
    "When this creature enters, create X Mutagen tokens. (They're artifacts with "
    '"{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. '
    'Activate only as a sorcery.")',
    power=4,
    toughness=4,
)


def setup(lands=5):
    game = Game(([LAND] * 60, [LAND] * 60), seed=771)
    game.begin_turn()
    for _ in range(lands):
        game.create_permanent(LAND, 0)
    card = game._create_card_object(OOZE, 0, "hand")
    game.players[0].hand.append(card)
    return game, card


def drain(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            options = game.legal_priority_actions(game.priority_state.player_index)
            game.execute_priority_action(
                next(o for o in options if o.kind is ActionKind.PASS_PRIORITY)
            )


@pytest.mark.parametrize("x_value", [0, 1, 3])
def test_announced_x_payment_entry_trigger_and_replay(x_value):
    game, card = setup()
    expected = [o for o in game.legal_main_actions(0) if o.object_id == card.object_id]
    assert {o.x_value for o in expected} == {0, 1, 2, 3}
    before = copy.deepcopy(game)
    option = next(o for o in expected if o.x_value == x_value)
    game.execute_main_action(option)
    drain(game)
    tokens = [p for p in game.players[0].battlefield if p.is_token]
    assert len(tokens) == x_value
    assert all(t.card is CardInterpreter.PREDEFINED_TOKENS["mutagen"] for t in tokens)
    assert any(
        e["event"] == "variable_x_entry_resolved" and e["x_value"] == x_value for e in game.events
    )
    assert sum(e["event"] == "tokens_created" for e in game.events) == (x_value > 0)
    assert (
        next(e for e in game.events if e["event"] == "cost_paid" and e["card"] == OOZE.name)[
            "x_value"
        ]
        == x_value
    )
    before.execute_main_action(
        next(
            o
            for o in before.legal_main_actions(0)
            if o.object_id == card.object_id and o.x_value == x_value
        )
    )
    drain(before)
    assert before.events == game.events
    game.check_invariants()


def test_insufficient_mana_and_invalid_announcements_are_transactional():
    game, card = setup(lands=2)
    assert {o.x_value for o in game.legal_main_actions(0) if o.object_id == card.object_id} == {0}
    before = (tuple(p.tapped for p in game.players[0].battlefield), len(game.stack))
    for chosen in (None, -1, 1, True):
        assert game.announce_spell(0, card, x_value=chosen) is None
        assert (tuple(p.tapped for p in game.players[0].battlefield), len(game.stack)) == before
    assert game.payment_plan(0, card, x_value=0) is not None


def test_colored_payment_and_legal_choice_revalidation():
    game, card = setup(0)
    for _ in range(6):
        game.create_permanent(PLAINS, 0)
    assert not [o for o in game.legal_main_actions(0) if o.object_id == card.object_id]
    assert game.announce_spell(0, card, x_value=0) is None
    game.create_permanent(LAND, 0)
    game.create_permanent(LAND, 0)
    options = [o for o in game.legal_main_actions(0) if o.object_id == card.object_id]
    assert set(o.x_value for o in options) == set(range(7))
    forged = ActionOption(ActionKind.CAST, 0, object_id=card.object_id, choice_ids=("7",))
    with pytest.raises(ValueError, match="not currently legal"):
        game.execute_main_action(forged)
    before = tuple(p.tapped for p in game.players[0].battlefield)
    plan = game.payment_plan(0, card, x_value=6)
    assert plan is not None
    game.players[0].battlefield[-1].tapped = True
    with pytest.raises(ValueError, match="no longer legal"):
        game._commit_announcement_payment(
            card, plan, cast_kind=game.interpreter.cast_program(card.card).kind, target_id=None
        )
    assert tuple(p.tapped for p in game.players[0].battlefield) == before[:-1] + (True,)


def test_countered_spell_never_creates_tokens():
    game, card = setup()
    spell = game.announce_spell(0, card, x_value=3)
    assert isinstance(spell, StackObject) and spell.x_value == 3
    game.move_object(spell, "graveyard", reason="countered")
    assert not any(e["event"] == "variable_x_entry_resolved" for e in game.events)
    assert not any(p.is_token for p in game.players[0].battlefield)
    game.check_invariants()


def test_entry_trigger_independent_of_source_departure():
    game, card = setup()
    assert game.cast(0, card, x_value=2)
    entered = next(p for p in game.players[0].battlefield if p.card == OOZE)
    game.move_object(entered, "graveyard", reason="response_removed")
    drain(game)
    assert len([p for p in game.players[0].battlefield if p.is_token]) == 2
    game.check_invariants()


def test_put_onto_battlefield_without_cast_uses_zero_x():
    game, card = setup(0)
    entered = game.move_object(card, "battlefield", controller=0, reason="put_onto_battlefield")
    assert entered.x_value == 0
    game._process_creature_entered_triggers(entered)
    drain(game)
    assert not [p for p in game.players[0].battlefield if p.is_token]
    assert any(e["event"] == "variable_x_entry_resolved" and e["x_value"] == 0 for e in game.events)
    game.check_invariants()


def test_incomplete_variable_clause_stays_unsupported():
    broken = CardFact(
        "Ooze Variant",
        "{X}{G}{G}",
        2,
        "Creature — Ooze",
        "When this creature enters, create X Mutagen tokens.",
    )
    fragment = broken.oracle_text
    coverage = CardInterpreter().token_semantic_coverage(broken, fragment)
    assert coverage is not None and not coverage.fully_supported
    assert CardInterpreter().x_entry_token_program(broken, fragment) is None
